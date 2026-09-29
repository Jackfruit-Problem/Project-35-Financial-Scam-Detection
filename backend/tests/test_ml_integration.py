"""How the application behaves around the model service. REQ-2, REQ-6, SRS 2.6.

These tests are about integration, not model quality: what happens when the
model answers, when it does not, and when it answers badly. Model quality is
measured separately in ml/tests/test_model_quality.py against a held-out split.
"""
import httpx

from app.models.detection import DetectionLog
from app.models.enums import CaseStatus, RiskBand, Role
from app.services import detection, ml_client
from tests.conftest import HIGH_RISK_TEXT, LOW_RISK_TEXT


def test_model_score_is_used_when_the_service_answers(db_session, fake_model):
    fake_model(82, reasons=['the wording "share your otp"'])

    result = detection.analyse(db_session, "anything at all")

    assert result["risk_score"] == 82
    assert result["risk_band"] == RiskBand.HIGH
    assert result["model_version"] == "tfidf-logreg-v1"
    assert 'the wording "share your otp"' in result["reasons"]


def test_falls_back_to_rules_when_the_service_is_down(db_session):
    """SRS 2.6: a model outage must degrade the score, not block reporting."""
    # The autouse fixture already simulates an unreachable service.
    result = detection.analyse(db_session, HIGH_RISK_TEXT)

    assert result["risk_score"] > 0
    assert "unavailable" in result["model_version"]
    assert result["reasons"]


def test_fallback_is_recorded_in_the_log(db_session):
    """REQ-6: a run of low scores must be traceable to the model being down."""
    detection.analyse(db_session, LOW_RISK_TEXT)
    db_session.commit()

    logged = db_session.query(DetectionLog).one()
    assert "unavailable" in logged.model_version


def test_model_version_is_recorded_when_the_model_answers(db_session, fake_model):
    fake_model(55, version="tfidf-logreg-v1")
    detection.analyse(db_session, "anything")
    db_session.commit()

    logged = db_session.query(DetectionLog).one()
    assert logged.model_version == "tfidf-logreg-v1"
    assert logged.risk_score == 55


def test_blacklist_still_outranks_the_model(db_session, fake_model):
    """A recorded fraudulent identifier is a fact; the model must not soften it."""
    from app.models.detection import BlacklistEntry

    db_session.add(BlacklistEntry(entry_type="upi_id", value="fraudster@ybl"))
    db_session.commit()
    fake_model(3, reasons=["looks fine to me"])

    result = detection.analyse(db_session, "send it to fraudster@ybl please")

    assert result["risk_score"] == 100
    assert result["matched_blacklist"] is True


def test_high_model_score_auto_assigns_the_case(client, make_user, auth_headers, fake_model):
    """REQ-5 must key off the model's score, not only the rules."""
    make_user("victim@example.com")
    investigator = make_user("inv@example.com", Role.INVESTIGATOR)
    fake_model(95)

    body = client.post(
        "/api/v1/reports",
        json={
            "reporter_name": "Asha Rao",
            "reporter_contact": "9876543210",
            "category": "upi_fraud",
            # Text the rules would score as harmless, so only the model can
            # be responsible for the High band.
            "description": "A neighbour asked me to transfer some money today.",
            "amount_involved": 5000,
        },
        headers=auth_headers("victim@example.com"),
    ).json()

    assert body["report"]["risk_band"] == RiskBand.HIGH
    assert body["case"]["status"] == CaseStatus.UNDER_INVESTIGATION
    assert body["case"]["assigned_investigator_id"] == investigator.id


# --- the client's own defences ---------------------------------------------


class _FakeClient:
    """Stands in for the pooled httpx client the module now reuses."""

    def __init__(self, handler):
        self._handler = handler

    def post(self, *args, **kwargs):
        return self._handler(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self._handler(*args, **kwargs)


def _patch_post(monkeypatch, handler):
    monkeypatch.setattr(ml_client, "_client", lambda: _FakeClient(handler))


def _response(**kwargs) -> httpx.Response:
    """A fake response that behaves like a real one.

    httpx refuses to run raise_for_status() on a response with no request
    attached, so the request has to be supplied even though nothing sends it.
    """
    return httpx.Response(
        request=httpx.Request("POST", "http://127.0.0.1:8001/predict"), **kwargs
    )


def test_client_returns_none_on_connection_error(monkeypatch, real_ml_client):
    def refuse(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    _patch_post(monkeypatch, refuse)
    assert ml_client.predict("hello") is None


def test_client_returns_none_on_timeout(monkeypatch, real_ml_client):
    def stall(*args, **kwargs):
        raise httpx.ReadTimeout("too slow")

    _patch_post(monkeypatch, stall)
    assert ml_client.predict("hello") is None


def test_client_rejects_a_response_missing_fields(monkeypatch, real_ml_client):
    """A reachable but wrong-shaped service is more dangerous than a dead one,
    because it would silently produce nonsense scores."""
    def wrong_shape(*args, **kwargs):
        return _response(status_code=200, json={"something_else": 1})

    _patch_post(monkeypatch, wrong_shape)
    assert ml_client.predict("hello") is None


def test_client_rejects_an_out_of_range_score(monkeypatch, real_ml_client):
    """REQ-2 fixes the scale at 0-100; anything else is a bug upstream."""
    def out_of_range(*args, **kwargs):
        return _response(
            status_code=200,
            json={"risk_score": 4000, "model_version": "x", "reasons": []},
        )

    _patch_post(monkeypatch, out_of_range)
    assert ml_client.predict("hello") is None


def test_client_survives_a_non_json_body(monkeypatch, real_ml_client):
    def html(*args, **kwargs):
        return _response(status_code=200, text="<html>nope</html>")

    _patch_post(monkeypatch, html)
    assert ml_client.predict("hello") is None


def test_client_tolerates_missing_reasons(monkeypatch, real_ml_client):
    """Reasons are desirable but not worth discarding a valid score over."""
    def no_reasons(*args, **kwargs):
        return _response(status_code=200, json={"risk_score": 60, "model_version": "x"})

    _patch_post(monkeypatch, no_reasons)
    result = ml_client.predict("hello")
    assert result is not None
    assert result["risk_score"] == 60
    assert result["reasons"] == []


# --- the administration screen ---------------------------------------------


def test_model_screen_reports_unavailable_rather_than_failing(
    client, make_user, auth_headers, monkeypatch
):
    """The SRS makes the model independently deployable, so 'not running' is a
    normal state the screen has to display, not a 500."""
    monkeypatch.setattr(ml_client, "info", lambda: None)
    make_user("admin@example.com", Role.ADMIN)

    response = client.get("/api/v1/admin/model", headers=auth_headers("admin@example.com"))

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert "fall" in response.json()["detail"].lower()


def test_model_screen_shows_measured_metrics(client, make_user, auth_headers, monkeypatch):
    monkeypatch.setattr(
        ml_client,
        "info",
        lambda: {"model_version": "tfidf-logreg-v1", "overall": {"precision": 0.95}},
    )
    make_user("admin@example.com", Role.ADMIN)

    body = client.get(
        "/api/v1/admin/model", headers=auth_headers("admin@example.com")
    ).json()

    assert body["available"] is True
    assert body["model_version"] == "tfidf-logreg-v1"
    assert body["overall"]["precision"] == 0.95


def test_model_screen_is_admin_only(client, make_user, auth_headers):
    make_user("inv@example.com", Role.INVESTIGATOR)
    response = client.get("/api/v1/admin/model", headers=auth_headers("inv@example.com"))
    assert response.status_code == 403
