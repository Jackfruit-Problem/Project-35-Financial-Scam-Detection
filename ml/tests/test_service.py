"""The model service's HTTP contract. REQ-1, REQ-2, SRS 3.2.

The main application depends on this shape, so these tests guard the boundary
between the two services rather than the model's accuracy.
"""
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import HIGH_BAND_SCORE, app, score_from_probability

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
HAS_MODEL = (ARTIFACTS / "model.joblib").exists()

SCAM = (
    "URGENT: your SBI account will be blocked in 2 hours. Complete KYC now and "
    "share your OTP at http://bit.ly/kyc-verify"
)
ORDINARY = "Your Amazon order has been shipped and arrives on 14 April."


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_is_always_answerable(client):
    """Used by the launcher to decide when the system is ready, so it must
    respond even with no model loaded."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "no_model"}


# --- the probability to score mapping, which needs no model ----------------


def test_threshold_maps_exactly_to_the_high_band():
    """A message the model calls a scam must score High in the application.
    If these ever disagreed, the system would flag something as a scam while
    displaying a middling score."""
    assert score_from_probability(0.17, 0.17) == HIGH_BAND_SCORE


def test_below_the_threshold_never_reaches_the_high_band():
    for probability in (0.0, 0.05, 0.1, 0.169):
        assert score_from_probability(probability, 0.17) < HIGH_BAND_SCORE


def test_certainty_maps_to_100():
    assert score_from_probability(1.0, 0.17) == 100


def test_score_rises_with_probability():
    scores = [score_from_probability(p / 20, 0.17) for p in range(21)]
    assert scores == sorted(scores)


def test_mapping_survives_a_degenerate_threshold():
    """A threshold of 0 or 1 should not divide by zero."""
    assert 0 <= score_from_probability(0.5, 0.0) <= 100
    assert 0 <= score_from_probability(1.0, 1.0) <= 100


# --- prediction -------------------------------------------------------------

pytestmark_model = pytest.mark.skipif(
    not HAS_MODEL, reason="no trained model; run python train.py"
)


@pytestmark_model
def test_predict_returns_the_agreed_shape(client):
    body = client.post("/predict", json={"text": SCAM}).json()

    assert set(body) == {
        "risk_score", "probability", "is_scam", "reasons", "model_version",
    }
    assert 0 <= body["risk_score"] <= 100
    assert 0.0 <= body["probability"] <= 1.0
    assert isinstance(body["is_scam"], bool)


@pytestmark_model
def test_predict_flags_a_clear_scam(client):
    body = client.post("/predict", json={"text": SCAM}).json()
    assert body["is_scam"] is True
    assert body["risk_score"] >= HIGH_BAND_SCORE


@pytestmark_model
def test_predict_does_not_flag_an_ordinary_message(client):
    body = client.post("/predict", json={"text": ORDINARY}).json()
    assert body["is_scam"] is False
    assert body["risk_score"] < HIGH_BAND_SCORE


@pytestmark_model
def test_reasons_are_returned_for_a_scam(client):
    """SRS 5.1.2: the score must be accompanied by a brief explanation."""
    body = client.post("/predict", json={"text": SCAM}).json()
    assert body["reasons"], "a flagged message must say what drove the score"
    assert all(isinstance(r, str) and r for r in body["reasons"])


@pytestmark_model
def test_prediction_is_well_inside_the_latency_budget(client):
    """REQ-2 allows 5 seconds for 95% of requests; this should be milliseconds."""
    started = time.perf_counter()
    client.post("/predict", json={"text": SCAM})
    assert (time.perf_counter() - started) < 2.0


@pytestmark_model
def test_info_reports_measured_metrics(client):
    body = client.get("/info").json()
    assert body["model_version"]
    assert 0 <= body["overall"]["precision"] <= 1
    assert 0 <= body["overall"]["recall"] <= 1
    assert body["honest_limitations"]


def test_empty_text_is_rejected(client):
    assert client.post("/predict", json={"text": ""}).status_code == 422


def test_overlong_text_is_rejected(client):
    assert client.post("/predict", json={"text": "x" * 5001}).status_code == 422


def test_missing_field_is_rejected(client):
    assert client.post("/predict", json={}).status_code == 422
