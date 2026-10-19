"""Defects found by auditing the finished system, each with its own test.

Every one of these was reachable through the running application and none of
them was caught by the existing suite, which is the point of writing them down
here rather than folding them into the module they belong to.
"""
import os

import pytest

from app.core.config import DEV_SECRET_KEY, Settings, verify_production_safety
from app.models.enums import RecoveryStatus, Role
from app.services import storage, throttle
from tests.conftest import HIGH_RISK_TEXT, LOW_RISK_TEXT


def _submit(client, headers, amount=None, description=LOW_RISK_TEXT):
    return client.post(
        "/api/v1/reports",
        json={
            "reporter_name": "Asha Rao",
            "reporter_contact": "9876543210",
            "category": "upi_fraud",
            "description": description,
            "amount_involved": amount,
        },
        headers=headers,
    ).json()


# --- evidence files were addressed relative to the working directory --------


def test_evidence_path_does_not_depend_on_the_working_directory(tmp_path, monkeypatch):
    """The stored path used to be resolved against the cwd, so evidence was
    readable only when the server had been started from the backend folder."""
    monkeypatch.setattr(storage.settings, "EVIDENCE_DIR", str(tmp_path / "ev"))

    stored_path, _ = storage.store(b"the original file", case_ref="CSE1", filename="a.txt")
    assert not os.path.isabs(stored_path), "an absolute path would pin the database to one machine"

    # Read it back from somewhere else entirely.
    monkeypatch.chdir(tmp_path.parent)
    assert storage.load(stored_path) == b"the original file"


def test_absolute_stored_paths_still_resolve(tmp_path, monkeypatch):
    """Deployments may point storage elsewhere; absolute paths must still work."""
    monkeypatch.setattr(storage.settings, "EVIDENCE_DIR", str(tmp_path / "ev"))
    relative, _ = storage.store(b"content", case_ref="CSE2", filename="b.txt")

    absolute = str(storage.resolve(relative))
    assert storage.load(absolute) == b"content"


def test_legacy_backend_relative_paths_still_resolve(tmp_path, monkeypatch):
    """Rows written before the fix carry an 'evidence_store/...' path relative
    to the backend folder. Evidence can never be regenerated, so those rows
    have to keep working."""
    legacy_root = storage.BACKEND_ROOT / "evidence_store_legacy_test"
    legacy_dir = legacy_root / "CSE3"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    try:
        monkeypatch.setattr(storage.settings, "EVIDENCE_DIR", str(tmp_path / "ev"))
        payload = b"old evidence"
        written, _ = storage.store(payload, case_ref="CSE3", filename="c.txt")
        # Move it to where an old row would have put it, and use the old style.
        (legacy_dir / "c.enc").write_bytes(storage.resolve(written).read_bytes())

        assert storage.load("evidence_store_legacy_test/CSE3/c.enc") == payload
    finally:
        for item in legacy_dir.glob("*"):
            item.unlink()
        legacy_dir.rmdir()
        legacy_root.rmdir()


def test_missing_evidence_file_reports_itself_clearly(
    client, make_user, auth_headers, db_session, tmp_path, monkeypatch
):
    """It used to raise FileNotFoundError and return a 500 with a stack trace.
    For evidence, "the file is gone" needs saying out loud."""
    from app.models.evidence import Evidence

    monkeypatch.setattr(storage.settings, "EVIDENCE_DIR", str(tmp_path / "ev"))
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)["case"]["case_ref"]

    evidence_id = client.post(
        f"/api/v1/cases/{case_ref}/evidence",
        files={"file": ("note.txt", b"some evidence", "text/plain")},
        headers=headers,
    ).json()["id"]

    # Delete the file behind the record, as a bad backup restore would.
    stored = db_session.get(Evidence, evidence_id)
    storage.resolve(stored.stored_path).unlink()

    response = client.get(f"/api/v1/evidence/{evidence_id}/download", headers=headers)
    assert response.status_code == 410
    assert "missing from storage" in response.json()["detail"]

    # The chain is unharmed; only the file is gone, and verification says so.
    verification = client.get(
        f"/api/v1/evidence/{evidence_id}/verify", headers=headers
    ).json()
    assert verification["chain_intact"] is True
    assert verification["file_intact"] is False


# --- recovery could not be recorded when no loss was stated ----------------


def test_recovery_can_be_recorded_when_no_amount_was_reported(
    client, make_user, auth_headers
):
    """Appendix B makes the amount optional, so 0 can mean "not stated". The
    guard compared against it anyway, which made it impossible to ever record
    money coming back on those cases."""
    make_user("victim@example.com")
    make_user("inv@example.com", Role.INVESTIGATOR)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)

    case_ref = _submit(
        client, auth_headers("victim@example.com"), amount=None, description=HIGH_RISK_TEXT
    )["case"]["case_ref"]

    client.post(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"bank_name": "SBI"},
        headers=auth_headers("inv@example.com"),
    )

    response = client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": RecoveryStatus.PARTIALLY_RECOVERED, "amount_recovered": 7500},
        headers=auth_headers("officer@example.com"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["amount_recovered"] == 7500
    # The recovered figure becomes the reported one, since it is now the only
    # number anyone has, and the analytics need both to agree.
    assert body["amount_reported"] == 7500


def test_the_ceiling_still_applies_when_a_loss_was_stated(
    client, make_user, auth_headers
):
    make_user("victim@example.com")
    make_user("inv@example.com", Role.INVESTIGATOR)
    make_user("officer@example.com", Role.RECOVERY_OFFICER)

    case_ref = _submit(
        client, auth_headers("victim@example.com"), amount=5000, description=HIGH_RISK_TEXT
    )["case"]["case_ref"]
    client.post(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"bank_name": "SBI"},
        headers=auth_headers("inv@example.com"),
    )

    response = client.patch(
        f"/api/v1/cases/{case_ref}/recovery",
        json={"status": RecoveryStatus.FULLY_RECOVERED, "amount_recovered": 9000},
        headers=auth_headers("officer@example.com"),
    )
    assert response.status_code == 422


# --- a case could be assigned to a deactivated investigator ----------------


def test_a_case_cannot_be_assigned_to_a_deactivated_investigator(
    client, make_user, auth_headers, db_session
):
    """Automatic allocation skips them; manual assignment did not, leaving the
    case looking assigned with nobody able to sign in and work it."""
    make_user("victim@example.com")
    make_user("admin@example.com", Role.ADMIN)
    investigator = make_user("inv@example.com", Role.INVESTIGATOR)

    case_ref = _submit(client, auth_headers("victim@example.com"))["case"]["case_ref"]

    investigator.is_active = False
    db_session.commit()

    response = client.post(
        f"/api/v1/cases/{case_ref}/assign/{investigator.id}",
        headers=auth_headers("admin@example.com"),
    )
    assert response.status_code == 400
    assert "deactivated" in response.json()["detail"].lower()


# --- nothing stopped a password being guessed repeatedly -------------------


def test_repeated_failures_are_eventually_refused(client, make_user):
    """SRS 6.3 audits logins, which reveals an attack afterwards. This stops one
    while it is happening."""
    make_user("target@example.com")
    attempt = {"email": "target@example.com", "password": "wrong-password"}

    seen_429 = False
    for _ in range(throttle.settings.LOGIN_MAX_FAILURES + 2):
        response = client.post("/api/v1/auth/login", json=attempt)
        if response.status_code == 429:
            seen_429 = True
            assert "Retry-After" in response.headers
            break
        assert response.status_code == 401

    assert seen_429, "an unlimited number of password guesses was accepted"


def test_a_correct_password_clears_the_counter(client, make_user, auth_headers):
    """An honest user who mistypes a few times must not be locked out."""
    make_user("honest@example.com")

    for _ in range(throttle.settings.LOGIN_MAX_FAILURES - 1):
        client.post(
            "/api/v1/auth/login",
            json={"email": "honest@example.com", "password": "nope"},
        )

    good = client.post(
        "/api/v1/auth/login",
        json={"email": "honest@example.com", "password": "password123"},
    )
    assert good.status_code == 200

    # Counter cleared, so the next mistake is not the one that locks them out.
    again = client.post(
        "/api/v1/auth/login", json={"email": "honest@example.com", "password": "nope"}
    )
    assert again.status_code == 401


def test_throttling_is_per_address(client, make_user):
    """One account being attacked must not lock everyone else out."""
    make_user("victim-a@example.com")
    make_user("victim-b@example.com")

    for _ in range(throttle.settings.LOGIN_MAX_FAILURES + 1):
        client.post(
            "/api/v1/auth/login",
            json={"email": "victim-a@example.com", "password": "wrong"},
        )

    other = client.post(
        "/api/v1/auth/login",
        json={"email": "victim-b@example.com", "password": "password123"},
    )
    assert other.status_code == 200


# --- list endpoints returned every row ------------------------------------


def test_report_list_is_windowed(client, make_user, auth_headers):
    """SRS 6.1 asks for 500 concurrent users and three-second pages, which an
    unbounded query cannot honour once the case load is real."""
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    for _ in range(5):
        _submit(client, headers)

    page = client.get("/api/v1/reports/mine?limit=2", headers=headers).json()
    assert len(page) == 2

    second = client.get("/api/v1/reports/mine?limit=2&offset=2", headers=headers).json()
    assert len(second) == 2
    assert {r["report_ref"] for r in page}.isdisjoint({r["report_ref"] for r in second})


def test_an_unreasonable_page_size_is_refused(client, make_user, auth_headers):
    make_user("victim@example.com")
    response = client.get(
        "/api/v1/reports/mine?limit=100000", headers=auth_headers("victim@example.com")
    )
    assert response.status_code == 422


def test_case_list_is_windowed(client, make_user, auth_headers):
    make_user("victim@example.com")
    make_user("admin@example.com", Role.ADMIN)
    headers = auth_headers("victim@example.com")
    for _ in range(4):
        _submit(client, headers)

    page = client.get("/api/v1/cases?limit=3", headers=auth_headers("admin@example.com"))
    assert page.status_code == 200
    assert len(page.json()) == 3


# --- nothing checked the production configuration -------------------------


def test_the_development_secret_is_reported_as_unsafe():
    problems = verify_production_safety(
        Settings(SECRET_KEY=DEV_SECRET_KEY, DATABASE_URL="postgresql://x/y")
    )
    assert any("SECRET_KEY" in p for p in problems)


def test_a_short_secret_is_reported_as_unsafe():
    problems = verify_production_safety(
        Settings(SECRET_KEY="too-short", DATABASE_URL="postgresql://x/y")
    )
    assert any("32" in p for p in problems)


def test_sqlite_is_reported_as_unsafe_for_production():
    problems = verify_production_safety(
        Settings(SECRET_KEY="k" * 40, DATABASE_URL="sqlite:///./x.db")
    )
    assert any("SQLite" in p for p in problems)


def test_a_sound_configuration_reports_nothing():
    assert verify_production_safety(
        Settings(SECRET_KEY="k" * 40, DATABASE_URL="postgresql+psycopg://u:p@h/db")
    ) == []


def test_production_refuses_to_start_when_unsafe(monkeypatch):
    """The check must bite, not merely log, when it says it is in production."""
    from app.core import config

    monkeypatch.setattr(config.settings, "FSDIRAS_ENV", "production")
    monkeypatch.setattr(config.settings, "SECRET_KEY", DEV_SECRET_KEY)

    with pytest.raises(RuntimeError, match="Refusing to start"):
        config.enforce_production_safety()
