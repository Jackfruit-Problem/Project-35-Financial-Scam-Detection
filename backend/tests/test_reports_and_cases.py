"""Report submission, case creation, assignment and lifecycle.
REQ-5, REQ-8, REQ-9, REQ-12, REQ-14.
"""
from app.models.enums import CaseStatus, RiskBand, Role
from tests.conftest import HIGH_RISK_TEXT, LOW_RISK_TEXT


def _submit(client, headers, description: str):
    return client.post(
        "/api/v1/reports",
        json={
            "reporter_name": "Asha Rao",
            "reporter_contact": "9876543210",
            "category": "upi_fraud",
            "description": description,
            "amount_involved": 15000,
        },
        headers=headers,
    )


def test_every_report_gets_a_case_reference(client, make_user, auth_headers):
    """REQ-8: a case reference for every report, not only the risky ones."""
    make_user("victim@example.com")
    response = _submit(client, auth_headers("victim@example.com"), LOW_RISK_TEXT)

    assert response.status_code == 201
    body = response.json()
    assert body["report"]["report_ref"].startswith("RPT")
    assert body["case"]["case_ref"].startswith("CSE")
    # Appendix B: 12 characters.
    assert len(body["report"]["report_ref"]) == 12
    assert len(body["case"]["case_ref"]) == 12


def test_report_references_are_unique(client, make_user, auth_headers):
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    refs = {
        _submit(client, headers, LOW_RISK_TEXT).json()["report"]["report_ref"]
        for _ in range(10)
    }
    assert len(refs) == 10


def test_low_risk_case_waits_for_a_human(client, make_user, auth_headers):
    """REQ-5: only High risk auto-activates; Low stays NEW and unassigned."""
    make_user("victim@example.com")
    make_user("inv@example.com", Role.INVESTIGATOR)

    body = _submit(client, auth_headers("victim@example.com"), LOW_RISK_TEXT).json()

    assert body["report"]["risk_band"] == RiskBand.LOW
    assert body["case"]["status"] == CaseStatus.NEW
    assert body["case"]["assigned_investigator_id"] is None


def test_high_risk_auto_creates_and_assigns(client, make_user, auth_headers):
    """REQ-5 + REQ-9: high risk enters the queue without waiting for an admin."""
    make_user("victim@example.com")
    investigator = make_user("inv@example.com", Role.INVESTIGATOR)

    body = _submit(client, auth_headers("victim@example.com"), HIGH_RISK_TEXT).json()

    assert body["report"]["risk_band"] == RiskBand.HIGH
    assert body["case"]["status"] == CaseStatus.UNDER_INVESTIGATION
    assert body["case"]["assigned_investigator_id"] == investigator.id


def test_high_risk_with_no_investigators_still_opens_a_case(
    client, make_user, auth_headers
):
    """An empty roster must not lose the report -- it stays NEW for triage."""
    make_user("victim@example.com")
    body = _submit(client, auth_headers("victim@example.com"), HIGH_RISK_TEXT).json()

    assert body["case"]["case_ref"]
    assert body["case"]["status"] == CaseStatus.NEW
    assert body["case"]["assigned_investigator_id"] is None


def test_round_robin_spreads_load(client, make_user, auth_headers):
    """REQ-9: allocation goes to the least-loaded investigator, not always the first."""
    make_user("victim@example.com")
    first = make_user("inv1@example.com", Role.INVESTIGATOR)
    second = make_user("inv2@example.com", Role.INVESTIGATOR)
    headers = auth_headers("victim@example.com")

    assigned = [
        _submit(client, headers, HIGH_RISK_TEXT).json()["case"]["assigned_investigator_id"]
        for _ in range(4)
    ]

    assert assigned.count(first.id) == 2
    assert assigned.count(second.id) == 2


def test_victim_sees_only_their_own_reports(client, make_user, auth_headers):
    """SRS 6.5: PII is not visible across victims."""
    make_user("a@example.com")
    make_user("b@example.com")
    _submit(client, auth_headers("a@example.com"), LOW_RISK_TEXT)

    mine = client.get("/api/v1/reports/mine", headers=auth_headers("b@example.com"))
    assert mine.status_code == 200
    assert mine.json() == []


def test_victim_cannot_read_another_victims_report(client, make_user, auth_headers):
    make_user("a@example.com")
    make_user("b@example.com")
    ref = _submit(client, auth_headers("a@example.com"), LOW_RISK_TEXT).json()["report"][
        "report_ref"
    ]

    response = client.get(
        f"/api/v1/reports/{ref}", headers=auth_headers("b@example.com")
    )
    assert response.status_code == 403


def test_victim_cannot_list_all_reports(client, make_user, auth_headers):
    make_user("a@example.com")
    assert client.get("/api/v1/reports", headers=auth_headers("a@example.com")).status_code == 403


def test_only_assigned_investigator_changes_status(client, make_user, auth_headers):
    """REQ-12 and SRS 6.5 business rule."""
    make_user("victim@example.com")
    make_user("inv1@example.com", Role.INVESTIGATOR)
    make_user("inv2@example.com", Role.INVESTIGATOR)

    case_ref = _submit(client, auth_headers("victim@example.com"), HIGH_RISK_TEXT).json()[
        "case"
    ]["case_ref"]

    # inv1 is the assignee (lowest id, empty queue); inv2 must be refused.
    refused = client.patch(
        f"/api/v1/cases/{case_ref}/status",
        json={"status": CaseStatus.RESOLVED},
        headers=auth_headers("inv2@example.com"),
    )
    assert refused.status_code == 403

    allowed = client.patch(
        f"/api/v1/cases/{case_ref}/status",
        json={"status": CaseStatus.RESOLVED, "note": "Funds traced to a mule account."},
        headers=auth_headers("inv1@example.com"),
    )
    assert allowed.status_code == 200
    assert allowed.json()["status"] == CaseStatus.RESOLVED


def test_status_must_be_one_of_the_five(client, make_user, auth_headers):
    """REQ-12: the vocabulary is closed; anything else is a 422."""
    make_user("victim@example.com")
    make_user("inv1@example.com", Role.INVESTIGATOR)
    case_ref = _submit(client, auth_headers("victim@example.com"), HIGH_RISK_TEXT).json()[
        "case"
    ]["case_ref"]

    response = client.patch(
        f"/api/v1/cases/{case_ref}/status",
        json={"status": "definitely_a_scam"},
        headers=auth_headers("inv1@example.com"),
    )
    assert response.status_code == 422


def test_notes_are_attributed_and_timestamped(client, make_user, auth_headers):
    """REQ-14."""
    make_user("victim@example.com")
    investigator = make_user("inv1@example.com", Role.INVESTIGATOR)
    case_ref = _submit(client, auth_headers("victim@example.com"), HIGH_RISK_TEXT).json()[
        "case"
    ]["case_ref"]

    created = client.post(
        f"/api/v1/cases/{case_ref}/notes",
        json={"body": "Contacted the bank fraud desk."},
        headers=auth_headers("inv1@example.com"),
    )
    assert created.status_code == 201
    note = created.json()
    assert note["author_id"] == investigator.id
    assert note["created_at"]


def test_investigator_queue_is_scoped_to_them(client, make_user, auth_headers):
    make_user("victim@example.com")
    make_user("inv1@example.com", Role.INVESTIGATOR)
    make_user("inv2@example.com", Role.INVESTIGATOR)
    _submit(client, auth_headers("victim@example.com"), HIGH_RISK_TEXT)

    inv2_queue = client.get("/api/v1/cases", headers=auth_headers("inv2@example.com"))
    assert inv2_queue.status_code == 200
    assert inv2_queue.json() == []


def test_admin_can_assign_manually(client, make_user, auth_headers):
    """REQ-9, manual half."""
    make_user("victim@example.com")
    make_user("admin@example.com", Role.ADMIN)
    investigator = make_user("inv1@example.com", Role.INVESTIGATOR)

    case_ref = _submit(client, auth_headers("victim@example.com"), LOW_RISK_TEXT).json()[
        "case"
    ]["case_ref"]

    response = client.post(
        f"/api/v1/cases/{case_ref}/assign/{investigator.id}",
        headers=auth_headers("admin@example.com"),
    )
    assert response.status_code == 200
    assert response.json()["assigned_investigator_id"] == investigator.id
    assert response.json()["status"] == CaseStatus.UNDER_INVESTIGATION


def test_non_admin_cannot_assign(client, make_user, auth_headers):
    make_user("victim@example.com")
    investigator = make_user("inv1@example.com", Role.INVESTIGATOR)
    case_ref = _submit(client, auth_headers("victim@example.com"), LOW_RISK_TEXT).json()[
        "case"
    ]["case_ref"]

    response = client.post(
        f"/api/v1/cases/{case_ref}/assign/{investigator.id}",
        headers=auth_headers("inv1@example.com"),
    )
    assert response.status_code == 403
