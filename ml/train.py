"""Train and evaluate the scam classifier. REQ-2, REQ-7.

Model choice: TF-IDF features into logistic regression.

That is deliberate rather than lazy. A linear model over TF-IDF is the one
family where a prediction can be explained exactly -- the contribution of each
word is its feature value times its coefficient, and those add up to the score.
SRS 5.1.2 requires the score to be shown "along with a brief explanation", and
a gradient-boosted or neural model would force us to bolt on an approximate
explainer that can disagree with the model it is explaining. It is also small
enough to train in seconds and to ship as a file, which matters for a project
that has to be demonstrated on a laptop.

Both word and character n-grams are used. Word n-grams catch phrases like
"share your OTP"; character n-grams survive the obfuscation that real scam
messages are full of -- "O.T.P", "0TP", "u p i" -- which word tokenisation
destroys.

Threshold: the decision point is chosen for recall, not accuracy. A missed
scam costs a victim money; a false alarm costs an investigator a few minutes
of reading. The two errors are not equally bad, so the threshold is set to the
lowest value that still keeps precision at or above a floor, rather than the
usual 0.5.
"""
import csv
import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

HERE = Path(__file__).parent
DATA = HERE / "data" / "train.csv"
ARTIFACTS = HERE / "artifacts"

SEED = 20260929
TEST_FRACTION = 0.2
MODEL_VERSION = "tfidf-logreg-v1"

# Precision floor for threshold selection. Below this, investigators start
# ignoring the score, which is worse than a slightly lower recall.
PRECISION_FLOOR = 0.95


def load() -> tuple[list[str], np.ndarray, list[str]]:
    texts, labels, sources = [], [], []
    with DATA.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            texts.append(row["text"])
            labels.append(int(row["label"]))
            sources.append(row["source"])
    return texts, np.array(labels), sources


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("features", FeatureUnion([
            ("word", TfidfVectorizer(
                analyzer="word", ngram_range=(1, 2), min_df=2,
                sublinear_tf=True, lowercase=True, strip_accents="unicode",
            )),
            ("char", TfidfVectorizer(
                analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                sublinear_tf=True, lowercase=True, strip_accents="unicode",
            )),
        ])),
        ("clf", LogisticRegression(
            max_iter=2000,
            C=4.0,
            # The corpus is roughly 1 scam to 4 legitimate. Without this the
            # model can score well by leaning towards "legitimate", which is
            # precisely the error this system cannot afford.
            class_weight="balanced",
            random_state=SEED,
        )),
    ])


def pick_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, str]:
    """Lowest threshold whose precision still clears the floor."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)

    best = None
    for p, r, t in zip(precision[:-1], recall[:-1], thresholds, strict=False):
        if p >= PRECISION_FLOOR:
            if best is None or r > best[1]:
                best = (float(t), float(r), float(p))

    if best is None:
        return 0.5, (
            f"no threshold reached {PRECISION_FLOOR:.0%} precision, so the "
            "conventional 0.5 is used"
        )

    threshold, recall_at, precision_at = best
    return threshold, (
        f"chosen to maximise recall ({recall_at:.1%}) while holding precision "
        f"at or above {PRECISION_FLOOR:.0%} (achieved {precision_at:.1%}), "
        "because a missed scam costs a victim money while a false alarm costs "
        "an investigator a few minutes"
    )


def scores_for(y_true: np.ndarray, predicted: np.ndarray, probs: np.ndarray) -> dict:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, predicted, average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(roc_auc_score(y_true, probs)), 4) if len(set(y_true)) > 1 else None,
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
        "support": {"scam": int(y_true.sum()), "legitimate": int(len(y_true) - y_true.sum())},
    }


def main() -> None:
    texts, labels, sources = load()
    print(f"loaded {len(texts):,} messages "
          f"({int(labels.sum()):,} scam / {len(labels) - int(labels.sum()):,} legitimate)")

    # Stratified so both splits keep the same scam ratio, and the source label
    # is carried along so the two halves can be scored separately afterwards.
    idx = np.arange(len(texts))
    train_idx, test_idx = train_test_split(
        idx, test_size=TEST_FRACTION, random_state=SEED, stratify=labels
    )
    x_train = [texts[i] for i in train_idx]
    x_test = [texts[i] for i in test_idx]
    y_train, y_test = labels[train_idx], labels[test_idx]
    test_sources = [sources[i] for i in test_idx]

    pipeline = build_pipeline()

    started = time.perf_counter()
    pipeline.fit(x_train, y_train)
    train_seconds = time.perf_counter() - started
    print(f"trained in {train_seconds:.1f}s")

    probs = pipeline.predict_proba(x_test)[:, 1]
    threshold, threshold_reason = pick_threshold(y_test, probs)
    predicted = (probs >= threshold).astype(int)

    overall = scores_for(y_test, predicted, probs)
    print(f"threshold {threshold:.3f}")
    print(f"precision {overall['precision']:.3f}  recall {overall['recall']:.3f}  "
          f"f1 {overall['f1']:.3f}  auc {overall['roc_auc']}")

    # Per source, so the harder half cannot hide behind the easier one.
    per_source = {}
    for source in sorted(set(test_sources)):
        mask = np.array([s == source for s in test_sources])
        if mask.sum() == 0:
            continue
        per_source[source] = scores_for(y_test[mask], predicted[mask], probs[mask])
        print(f"  {source:<14} precision {per_source[source]['precision']:.3f}  "
              f"recall {per_source[source]['recall']:.3f}  n={int(mask.sum())}")

    # Cross-validation on the training half only: a single split can flatter a
    # model by luck, and this says whether the result is stable.
    cv = cross_val_score(build_pipeline(), x_train, y_train, cv=5, scoring="f1")
    print(f"5-fold f1 on train: {cv.mean():.3f} +/- {cv.std():.3f}")

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"pipeline": pipeline, "threshold": threshold, "version": MODEL_VERSION},
        ARTIFACTS / "model.joblib",
        compress=3,
    )

    metrics = {
        "model_version": MODEL_VERSION,
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "algorithm": "TF-IDF (word 1-2 grams + character 3-5 grams) -> logistic regression",
        "why_this_model": (
            "A linear model over TF-IDF is the only common family whose "
            "predictions can be explained exactly: each word's contribution is "
            "its feature value times its coefficient, and those contributions "
            "sum to the score. SRS 5.1.2 requires an explanation alongside the "
            "score."
        ),
        "dataset": {
            "total_messages": len(texts),
            "scam": int(labels.sum()),
            "legitimate": int(len(labels) - labels.sum()),
            "sources": {
                "uci_sms": "UCI SMS Spam Collection, 5,574 real English SMS",
                "synthetic_in": "Generated for this project: Indian UPI, KYC, "
                                "loan and investment fraud, plus ordinary Indian messages",
            },
            "test_fraction": TEST_FRACTION,
            "split": "stratified, fixed seed",
        },
        "decision_threshold": round(threshold, 4),
        "threshold_rationale": threshold_reason,
        "overall": overall,
        "per_source": per_source,
        "cross_validation": {
            "folds": 5,
            "metric": "f1",
            "mean": round(float(cv.mean()), 4),
            "std": round(float(cv.std()), 4),
        },
        "train_seconds": round(train_seconds, 2),
        "honest_limitations": [
            "The Indian financial-fraud half of the training data is synthetic, "
            "generated from templates. Real fraud is more varied, so live "
            "accuracy will be lower than the figures above.",
            "The public half is English SMS from the 2000s and contains almost "
            "no UPI or instant-loan fraud.",
            "No Hinglish or regional-language messages are included; the SRS "
            "places multilingual support out of scope for version 1.",
            "The score is advisory. A scam determination requires human review.",
        ],
    }

    (ARTIFACTS / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    print(f"\nwrote {ARTIFACTS / 'model.joblib'}")
    print(f"wrote {ARTIFACTS / 'metrics.json'}")


if __name__ == "__main__":
    main()
