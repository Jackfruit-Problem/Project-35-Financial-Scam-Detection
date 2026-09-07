"""Detection engine. REQ-1 to REQ-6."""
import pytest

from app.core.config import settings
from app.models.detection import BlacklistEntry, DetectionLog
from app.models.enums import RiskBand
from app.services import detection
from tests.conftest import HIGH_RISK_TEXT, LOW_RISK_TEXT


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, RiskBand.LOW),
        (settings.RISK_MEDIUM_THRESHOLD - 1, RiskBand.LOW),
        (settings.RISK_MEDIUM_THRESHOLD, RiskBand.MEDIUM),
        (settings.RISK_HIGH_THRESHOLD - 1, RiskBand.MEDIUM),
        (settings.RISK_HIGH_THRESHOLD, RiskBand.HIGH),
        (100, RiskBand.HIGH),
    ],
)
def test_risk_bands_at_boundaries(score, expected):
    """REQ-3: banding is inclusive at each threshold, including the edges."""
    assert detection.band_for(score) == expected


def test_score_is_bounded_to_100():
    """REQ-2: the scale is 0-100 even when many signals fire at once."""
    piled_on = " ".join([HIGH_RISK_TEXT] * 5)
    score, _ = detection.score_text(piled_on)
    assert 0 <= score <= 100


def test_scam_text_scores_higher_than_innocuous_text():
    scam, reasons = detection.score_text(HIGH_RISK_TEXT)
    benign, _ = detection.score_text(LOW_RISK_TEXT)
    assert scam > benign
    assert reasons, "a score must come with its reasons (SRS 5.1.2)"


def test_analyse_logs_every_request(db_session):
    """REQ-6: logged for audit and future retraining."""
    detection.analyse(db_session, LOW_RISK_TEXT)
    db_session.commit()

    logs = db_session.query(DetectionLog).all()
    assert len(logs) == 1
    assert logs[0].model_version == detection.MODEL_VERSION


def test_blacklist_short_circuits_the_model(db_session):
    """REQ-4: a blacklist hit is a fact and outranks any model opinion."""
    db_session.add(
        BlacklistEntry(entry_type="upi_id", value="fraudster@ybl", note="reported 12x")
    )
    db_session.commit()

    result = detection.analyse(db_session, "please pay fraudster@ybl for the refund")
    db_session.commit()

    assert result["matched_blacklist"] is True
    assert result["risk_score"] == 100
    assert result["risk_band"] == RiskBand.HIGH


def test_score_is_always_labelled_advisory(db_session):
    """SRS 6.2: the score must never present as a conclusive determination."""
    result = detection.analyse(db_session, HIGH_RISK_TEXT)
    assert "advisory" in result["advisory_note"].lower()


def test_analyse_endpoint_requires_authentication(client):
    response = client.post("/api/v1/detection/analyse", json={"text": LOW_RISK_TEXT})
    assert response.status_code == 401


def test_analyse_endpoint_returns_score_and_reasons(client, make_user, auth_headers):
    make_user("v@example.com")
    response = client.post(
        "/api/v1/detection/analyse",
        json={"text": HIGH_RISK_TEXT},
        headers=auth_headers("v@example.com"),
    )
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["risk_score"] <= 100
    assert body["reasons"]
