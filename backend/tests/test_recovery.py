"""Recovery assistance and PDF reporting. REQ-15 to REQ-19."""
from app.models.enums import RecoveryStatus, Role
from app.models.notification import Notification
from tests.conftest import HIGH_RISK_TEXT


def _case_with_investigator(client, make_user, auth_headers, amount: float = 25000) -> str:
    """A high-risk case, auto-assigned, ready for recovery action."""
    make_user("victim@example.com")
    make_user("inv1@example.com", Role.INVESTIGATOR)
    response = client.post(
        "/api/v1/reports",
        json={
            "reporter_name": "Asha Rao",
            "reporter_contact": "9876543210",
            "category": "upi_fraud",
            "description": HIGH_RISK_TEXT,
            "amount_involved": amount,
        },
        headers=auth_headers("victim@example.com"),
    )
    return response.json()["case"]["case_ref"]


def _raise(client, headers, case_ref):
    return client.post(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"bank_name": "State Bank of India", "ifsc_code": "SBIN0001234",
              "account_number": "30123456789"},
        headers=headers,
    )


def test_recovery_request_is_autopopulated_from_the_case(client, make_user, auth_headers):
    """REQ-15: the amount lost comes from the case, not from re-typing."""
    case_ref = _case_with_investigator(client, make_user, auth_headers, amount=25000)

    response = _raise(client, auth_headers("inv1@example.com"), case_ref)
    assert response.status_code == 201
    body = response.json()
    assert body["amount_reported"] == 25000
    assert body["amount_recovered"] == 0
    assert body["status"] == RecoveryStatus.REQUESTED


def test_only_one_recovery_request_per_case(client, make_user, auth_headers):
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    headers = auth_headers("inv1@example.com")

    assert _raise(client, headers, case_ref).status_code == 201
    assert _raise(client, headers, case_ref).status_code == 409


def test_victim_cannot_raise_a_recovery_request(client, make_user, auth_headers):
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    response = _raise(client, auth_headers("victim@example.com"), case_ref)
    assert response.status_code == 403


def test_recovery_status_progresses_through_the_five_values(
    client, make_user, auth_headers
):
    """REQ-16."""
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)
    _raise(client, auth_headers("inv1@example.com"), case_ref)
    officer = auth_headers("officer@example.com")

    for status_value in (
        RecoveryStatus.IN_PROGRESS,
        RecoveryStatus.PARTIALLY_RECOVERED,
        RecoveryStatus.FULLY_RECOVERED,
    ):
        response = client.patch(
            f"/api/v1/cases/{case_ref}/recovery",
            json={"status": status_value},
            headers=officer,
        )
        assert response.status_code == 200
        assert response.json()["status"] == status_value


def test_invalid_recovery_status_is_rejected(client, make_user, auth_headers):
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)
    _raise(client, auth_headers("inv1@example.com"), case_ref)

    response = client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": "money_came_back_somehow"},
        headers=auth_headers("officer@example.com"),
    )
    assert response.status_code == 422


def test_recovered_amount_cannot_exceed_the_loss(client, make_user, auth_headers):
    """REQ-19: an impossible figure would corrupt the recovery-rate analytics."""
    case_ref = _case_with_investigator(client, make_user, auth_headers, amount=10000)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)
    _raise(client, auth_headers("inv1@example.com"), case_ref)

    response = client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": RecoveryStatus.PARTIALLY_RECOVERED, "amount_recovered": 99999},
        headers=auth_headers("officer@example.com"),
    )
    assert response.status_code == 422


def test_reported_versus_recovered_is_tracked(client, make_user, auth_headers):
    """REQ-19."""
    case_ref = _case_with_investigator(client, make_user, auth_headers, amount=10000)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)
    _raise(client, auth_headers("inv1@example.com"), case_ref)

    response = client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": RecoveryStatus.PARTIALLY_RECOVERED, "amount_recovered": 4000},
        headers=auth_headers("officer@example.com"),
    )
    body = response.json()
    assert body["amount_reported"] == 10000
    assert body["amount_recovered"] == 4000


def test_victim_is_notified_of_status_changes(client, make_user, auth_headers, db_session):
    """REQ-18."""
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)
    _raise(client, auth_headers("inv1@example.com"), case_ref)

    before = db_session.query(Notification).count()
    client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": RecoveryStatus.IN_PROGRESS},
        headers=auth_headers("officer@example.com"),
    )
    after = db_session.query(Notification).all()

    assert len(after) == before + 1
    assert case_ref in after[-1].body


def test_no_notification_when_nothing_changed(client, make_user, auth_headers, db_session):
    """Re-sending the same status must not spam the victim."""
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)
    _raise(client, auth_headers("inv1@example.com"), case_ref)
    officer = auth_headers("officer@example.com")

    client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": RecoveryStatus.IN_PROGRESS},
        headers=officer,
    )
    count = db_session.query(Notification).count()

    client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": RecoveryStatus.IN_PROGRESS, "remarks": "Chasing the bank."},
        headers=officer,
    )
    assert db_session.query(Notification).count() == count


def test_investigator_cannot_record_a_recovery_outcome(client, make_user, auth_headers):
    """Recording money movement is a bank-liaison action, not an investigator one."""
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    _raise(client, auth_headers("inv1@example.com"), case_ref)

    response = client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": RecoveryStatus.FULLY_RECOVERED},
        headers=auth_headers("inv1@example.com"),
    )
    assert response.status_code == 403


def test_case_report_pdf_is_generated(client, make_user, auth_headers):
    """REQ-17."""
    case_ref = _case_with_investigator(client, make_user, auth_headers)

    response = client.get(
        f"/api/v1/cases/{case_ref}/report.pdf", headers=auth_headers("victim@example.com")
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # A real PDF starts with the magic bytes and is not a stub.
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 1000
    assert case_ref in response.headers["content-disposition"]


def test_recovery_report_pdf_is_generated(client, make_user, auth_headers):
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)
    _raise(client, auth_headers("inv1@example.com"), case_ref)

    response = client.get(
        f"/api/v1/cases/{case_ref}/recovery-report.pdf",
        headers=auth_headers("officer@example.com"),
    )
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")


def test_recovery_report_requires_a_raised_request(client, make_user, auth_headers):
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    response = client.get(
        f"/api/v1/cases/{case_ref}/recovery-report.pdf",
        headers=auth_headers("victim@example.com"),
    )
    assert response.status_code == 404


def test_stranger_cannot_download_a_case_report(client, make_user, auth_headers):
    """A PDF is still case data -- SRS 6.5 applies to it too."""
    case_ref = _case_with_investigator(client, make_user, auth_headers)
    make_user("stranger@example.com")

    response = client.get(
        f"/api/v1/cases/{case_ref}/report.pdf", headers=auth_headers("stranger@example.com")
    )
    assert response.status_code == 403
