"""The scam-detection model service. SRS 3.2, REQ-2.

A separate service, as the SRS requires, so the model can be retrained,
replaced or scaled without touching the main application. The main application
talks to it over HTTP and falls back to its own rules if this service is
unreachable, so a model outage degrades the score rather than breaking report
submission.
"""
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

# Anchored so that "High risk" in the application means exactly the model's own
# decision point. The application treats 70 and above as High, so a message the
# model would call a scam scores 70 or more, and one it would not scores less.
# Without anchoring, the 0-100 score and the model's decision could disagree --
# a message flagged as a scam but scoring 45 would be indefensible in a viva.
HIGH_BAND_SCORE = 70

_state: dict[str, Any] = {}


class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class PredictResponse(BaseModel):
    risk_score: int
    probability: float
    is_scam: bool
    reasons: list[str]
    model_version: str


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Load the model once. Loading per request would dominate the latency
    budget in REQ-2 (5 seconds for 95% of requests)."""
    model_path = ARTIFACTS / "model.joblib"
    metrics_path = ARTIFACTS / "metrics.json"

    if model_path.exists():
        bundle = joblib.load(model_path)
        pipeline = bundle["pipeline"]
        _state["pipeline"] = pipeline
        _state["threshold"] = bundle["threshold"]
        _state["version"] = bundle["version"]
        # Cached for the explanation path; recomputing per request is wasteful.
        _state["features"] = pipeline.named_steps["features"]
        _state["coefficients"] = pipeline.named_steps["clf"].coef_[0]
        _state["feature_names"] = _state["features"].get_feature_names_out()
        print(f"loaded model {bundle['version']} (threshold {bundle['threshold']:.3f})")
    else:
        print(f"no model at {model_path} -- run train.py. Predictions unavailable.")

    if metrics_path.exists():
        _state["metrics"] = json.loads(metrics_path.read_text(encoding="utf-8"))

    yield


app = FastAPI(
    title="FSDIRAS detection model",
    description="Risk scoring for the Financial Scam Detection system. Project ID 35.",
    version="1.0.0",
    lifespan=lifespan,
)


def score_from_probability(probability: float, threshold: float) -> int:
    """Map a probability onto 0-100 with the High band anchored on the threshold."""
    if probability >= threshold:
        span = 1.0 - threshold
        above = (probability - threshold) / span if span > 0 else 1.0
        return int(round(HIGH_BAND_SCORE + (100 - HIGH_BAND_SCORE) * above))

    below = probability / threshold if threshold > 0 else 0.0
    return int(round((HIGH_BAND_SCORE - 1) * below))


# Words that carry no meaning on their own. They can legitimately appear among
# the top contributors -- scam messages really do say "your" more often -- but
# reporting them as a reason is noise that makes the explanation look silly.
_UNINFORMATIVE = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "is", "are", "was", "be", "been", "am", "do", "does", "did",
    "have", "has", "had", "you", "your", "yours", "i", "me", "my", "we", "us",
    "our", "it", "its", "this", "that", "these", "those", "will", "can",
    "http", "https", "www", "com", "co", "rs", "not", "no", "so", "as", "by",
    "from", "now", "get", "got", "all", "any", "out", "up", "one", "two",
}

# A contribution below this share of the total positive push is rounding noise,
# not a reason.
_MIN_SHARE = 0.04


def explain(text: str, probability: float, threshold: float, limit: int = 4) -> list[str]:
    """The wording that pushed this score up, taken from the model itself.

    For a linear model each feature contributes its value times its
    coefficient, and those contributions sum to the decision. So this is not an
    approximation of the model's reasoning -- it is the reasoning.

    Three filters, all there to stop the explanation being worse than none:

    * Only word features. The character n-grams carry real signal but read as
      meaningless fragments to a human.
    * No bare function words. "your" really is more common in scams, but
      offering it as the reason makes the system look unserious.
    * Nothing for a message the model considers clearly safe. Listing the
      "reasons" behind a score of 5 implies a suspicion that is not there.
    """
    # Well below the decision point there is nothing to explain.
    if probability < threshold * 0.5:
        return []

    features = _state["features"]
    names = _state["feature_names"]
    coefficients = _state["coefficients"]

    row = features.transform([text])
    contributions = row.multiply(coefficients).tocoo()

    # Word features only, and the share is measured against their total rather
    # than the whole feature space. The character n-grams are far more numerous,
    # so including them would drag every individual share below any sensible
    # floor and the explanation would always come back empty.
    ranked = sorted(
        (
            (value, names[col])
            for col, value in zip(contributions.col, contributions.data, strict=False)
            if value > 0 and names[col].startswith("word__")
        ),
        reverse=True,
    )
    total_push = sum(value for value, _ in ranked)
    if total_push <= 0:
        return []

    reasons: list[str] = []
    seen: set[str] = set()
    for value, name in ranked:
        if value / total_push < _MIN_SHARE:
            break

        phrase = name.removeprefix("word__").strip()
        words = phrase.split()
        # A single function word says nothing; a phrase containing one can still
        # be informative ("share your otp"), so only reject the bare case.
        if len(words) == 1 and (phrase in _UNINFORMATIVE or len(phrase) < 3):
            continue
        if phrase in seen:
            continue

        seen.add(phrase)
        reasons.append(f'the wording "{phrase}"')
        if len(reasons) >= limit:
            break

    return reasons


@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    return {
        "status": "ok" if "pipeline" in _state else "no_model",
        "model_version": _state.get("version"),
    }


@app.get("/info", tags=["meta"])
def info() -> dict[str, Any]:
    """Everything known about the model in service, including how it scored.

    Exposed so the administration screen can show real measured numbers rather
    than a claim typed into a slide.
    """
    if "metrics" not in _state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No metrics available. Run train.py.",
        )
    return _state["metrics"]


@app.post("/predict", response_model=PredictResponse, tags=["detection"])
def predict(payload: PredictRequest) -> PredictResponse:
    if "pipeline" not in _state:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No trained model is loaded. Run train.py in the ml folder.",
        )

    probability = float(_state["pipeline"].predict_proba([payload.text])[0, 1])
    threshold = float(_state["threshold"])

    return PredictResponse(
        risk_score=int(np.clip(score_from_probability(probability, threshold), 0, 100)),
        probability=round(probability, 4),
        is_scam=probability >= threshold,
        reasons=explain(payload.text, probability, threshold),
        model_version=_state["version"],
    )
