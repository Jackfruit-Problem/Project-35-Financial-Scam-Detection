"""The explanation attached to a score. SRS 5.1.2.

An explanation that lists "your" and "http" is worse than no explanation: it
makes a defensible model look unserious, and in a viva it invites exactly the
wrong question. These tests hold the quality of what the user reads.
"""
from pathlib import Path

import joblib
import pytest

from app.main import explain

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

pytestmark = pytest.mark.skipif(
    not (ARTIFACTS / "model.joblib").exists(),
    reason="no trained model; run python train.py in the ml folder",
)

SCAM = (
    "URGENT: your SBI account will be blocked in 2 hours. Complete KYC now and "
    "share your OTP and PAN card at http://bit.ly/kyc-verify"
)
ORDINARY = "Your Amazon order has been shipped and arrives on Tuesday."


@pytest.fixture(scope="module")
def loaded(monkeypatch_module=None):
    """Load the model into the module state explain() reads from."""
    from app import main

    bundle = joblib.load(ARTIFACTS / "model.joblib")
    pipeline = bundle["pipeline"]
    main._state.update({
        "pipeline": pipeline,
        "threshold": bundle["threshold"],
        "version": bundle["version"],
        "features": pipeline.named_steps["features"],
        "coefficients": pipeline.named_steps["clf"].coef_[0],
        "feature_names": pipeline.named_steps["features"].get_feature_names_out(),
    })
    return bundle


def _probability(loaded, text: str) -> float:
    return float(loaded["pipeline"].predict_proba([text])[0, 1])


def test_a_scam_gets_reasons(loaded):
    reasons = explain(SCAM, _probability(loaded, SCAM), loaded["threshold"])
    assert reasons, "a flagged message must say what drove the score"


def test_reasons_are_not_bare_function_words(loaded):
    """The exact defect this filter exists for: "your", "http", "been"."""
    reasons = explain(SCAM, _probability(loaded, SCAM), loaded["threshold"])
    banned = {"your", "http", "https", "been", "the", "you", "and", "of", "is"}

    for reason in reasons:
        phrase = reason.split('"')[1]
        if len(phrase.split()) == 1:
            assert phrase not in banned, f"uninformative reason offered: {reason}"


def test_an_ordinary_message_gets_no_reasons(loaded):
    """Listing reasons behind a score of 5 implies a suspicion that is absent."""
    reasons = explain(ORDINARY, _probability(loaded, ORDINARY), loaded["threshold"])
    assert reasons == []


def test_reasons_are_limited_in_number(loaded):
    reasons = explain(SCAM, _probability(loaded, SCAM), loaded["threshold"], limit=3)
    assert len(reasons) <= 3


def test_reasons_are_unique(loaded):
    reasons = explain(SCAM, _probability(loaded, SCAM), loaded["threshold"])
    assert len(reasons) == len(set(reasons))


def test_reasons_mention_scam_relevant_wording(loaded):
    """Not a guarantee about any single word -- just that at least one reason
    is recognisably about the fraud rather than grammar."""
    reasons = " ".join(
        explain(SCAM, _probability(loaded, SCAM), loaded["threshold"])
    ).lower()
    assert any(
        term in reasons
        for term in ("kyc", "otp", "urgent", "blocked", "verify", "pan", "share", "account")
    ), f"no recognisably scam-related wording in: {reasons}"
