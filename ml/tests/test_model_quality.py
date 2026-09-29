"""A quality gate for the trained model. REQ-2, REQ-7.

This is not the same kind of test as the rest of the project. Application tests
check rules that are either obeyed or broken; these check that a statistical
artefact is still good enough to ship, and they exist so that retraining on new
data cannot quietly make the system worse.

The floors are set below the measured figures with deliberate headroom: a gate
pinned to today's exact numbers would fail on harmless variation and would soon
be ignored, which is worse than no gate.
"""
import csv
import json
from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import train_test_split

ML_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ML_ROOT / "artifacts"
DATA = ML_ROOT / "data" / "train.csv"

# Must match train.py, or the "held-out" rows would include rows the model was
# fitted on and every number here would be inflated.
SEED = 20260929
TEST_FRACTION = 0.2

PRECISION_FLOOR = 0.88
RECALL_FLOOR = 0.90
AUC_FLOOR = 0.97


pytestmark = pytest.mark.skipif(
    not (ARTIFACTS / "model.joblib").exists(),
    reason="no trained model; run python train.py in the ml folder",
)


@pytest.fixture(scope="module")
def bundle():
    return joblib.load(ARTIFACTS / "model.joblib")


@pytest.fixture(scope="module")
def held_out():
    if not DATA.exists():
        pytest.skip("no dataset; run python build_dataset.py")

    texts, labels = [], []
    with DATA.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            texts.append(row["text"])
            labels.append(int(row["label"]))
    labels = np.array(labels)

    idx = np.arange(len(texts))
    _, test_idx = train_test_split(
        idx, test_size=TEST_FRACTION, random_state=SEED, stratify=labels
    )
    return [texts[i] for i in test_idx], labels[test_idx]


def test_model_clears_the_quality_floors(bundle, held_out):
    texts, y_true = held_out
    probs = bundle["pipeline"].predict_proba(texts)[:, 1]
    predicted = (probs >= bundle["threshold"]).astype(int)

    precision, recall, _, _ = precision_recall_fscore_support(
        y_true, predicted, average="binary", zero_division=0
    )

    assert precision >= PRECISION_FLOOR, (
        f"precision {precision:.3f} is below the {PRECISION_FLOOR} floor -- "
        "investigators will start ignoring the score"
    )
    assert recall >= RECALL_FLOOR, (
        f"recall {recall:.3f} is below the {RECALL_FLOOR} floor -- "
        "too many scams are being missed"
    )


def test_recall_is_not_traded_away_for_precision(bundle, held_out):
    """The threshold is chosen for recall on purpose (a missed scam costs a
    victim money; a false alarm costs an investigator minutes). If a retrain
    inverts that balance, the choice has been lost."""
    texts, y_true = held_out
    probs = bundle["pipeline"].predict_proba(texts)[:, 1]
    predicted = (probs >= bundle["threshold"]).astype(int)

    precision, recall, _, _ = precision_recall_fscore_support(
        y_true, predicted, average="binary", zero_division=0
    )
    assert recall >= precision, (
        f"recall {recall:.3f} has fallen below precision {precision:.3f}; the "
        "threshold no longer reflects the documented trade-off"
    )


def test_metrics_file_matches_the_shipped_model(bundle):
    """Stops the dashboard from advertising numbers from an older artefact."""
    metrics = json.loads((ARTIFACTS / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["model_version"] == bundle["version"]
    assert metrics["decision_threshold"] == pytest.approx(bundle["threshold"], abs=1e-4)


def test_metrics_report_each_source_separately(bundle):
    """The synthetic half is templated and therefore easy. Reporting only a
    combined figure would let it flatter the harder real-SMS half."""
    metrics = json.loads((ARTIFACTS / "metrics.json").read_text(encoding="utf-8"))
    assert "uci_sms" in metrics["per_source"]
    assert "synthetic_in" in metrics["per_source"]


def test_metrics_state_their_limitations(bundle):
    """SRS 2.6 requires the synthetic data and the advisory nature to be
    declared. If this list is ever emptied, the claim stops being honest."""
    metrics = json.loads((ARTIFACTS / "metrics.json").read_text(encoding="utf-8"))
    limitations = " ".join(metrics["honest_limitations"]).lower()
    assert "synthetic" in limitations
    assert "advisory" in limitations


def test_auc_is_high(bundle, held_out):
    from sklearn.metrics import roc_auc_score

    texts, y_true = held_out
    probs = bundle["pipeline"].predict_proba(texts)[:, 1]
    assert roc_auc_score(y_true, probs) >= AUC_FLOOR


# --- behaviour on messages a person would judge the same way ----------------

CLEAR_SCAMS = [
    "URGENT: your SBI account will be blocked in 2 hours. Complete KYC at http://bit.ly/kyc-verify",
    "Congratulations! You won Rs 50,000. Share your UPI PIN to claim the prize.",
    "Pre-approved instant loan, no documents. Pay Rs 499 processing fee to instantloan@upi",
    "Guaranteed returns of 30% per month. Double your money risk-free, join today.",
    "This is HDFC security team. Share the OTP sent to your phone to stop the fraud.",
]

CLEAR_LEGITIMATE = [
    "Rs 2,340 debited from your HDFC account ending 4821 on 12 March. Not you? Call the number on your card.",
    "Your Amazon order has been shipped and arrives on 14 April.",
    "Hey, are we still meeting at 6:30 pm tomorrow? Let me know if the time changed.",
    "Your OTP is 448192. Do not share it with anyone, including bank staff.",
    "The assignment deadline moved to 20 October. Submit on the college portal.",
]


@pytest.mark.parametrize("text", CLEAR_SCAMS)
def test_obvious_scams_are_flagged(bundle, text):
    probability = bundle["pipeline"].predict_proba([text])[0, 1]
    assert probability >= bundle["threshold"], f"missed an obvious scam: {text!r}"


@pytest.mark.parametrize("text", CLEAR_LEGITIMATE)
def test_ordinary_messages_are_not_flagged(bundle, text):
    probability = bundle["pipeline"].predict_proba([text])[0, 1]
    assert probability < bundle["threshold"], f"false alarm on: {text!r}"
