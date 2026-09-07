"""Evidence upload, access control, encryption at rest and archiving.
REQ-10, REQ-11, REQ-13, SRS 3.3, SRS 6.3.
"""
import pytest

from app.core.config import settings
from app.models.enums import Role
from app.services import storage
from tests.conftest import HIGH_RISK_TEXT, LOW_RISK_TEXT


@pytest.fixture(autouse=True)
def isolated_evidence_dir(tmp_path, monkeypatch):
    """Keep uploaded files out of the working tree and out of other tests."""
    monkeypatch.setattr(settings, "EVIDENCE_DIR", str(tmp_path / "evidence"))


def _submit(client, headers, description: str = LOW_RISK_TEXT) -> str:
    response = client.post(
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
    return response.json()["case"]["case_ref"]


def _upload(client, headers, case_ref, *, name="screenshot.png", content=b"fake-png-bytes",
            content_type="image/png"):
    return client.post(
        f"/api/v1/cases/{case_ref}/evidence",
        files={"file": (name, content, content_type)},
        headers=headers,
    )


def test_victim_can_upload_to_their_own_case(client, make_user, auth_headers):
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)

    response = _upload(client, headers, case_ref)
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "screenshot.png"
    assert len(body["sha256"]) == 64
    assert body["is_archived"] is False


def test_upload_is_encrypted_at_rest(client, make_user, auth_headers, db_session):
    """SRS 6.3: the bytes on disk must not be the bytes that were uploaded."""
    from app.models.evidence import Evidence

    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)
    secret = b"account number 1234567890 and my OTP is 998877"
    _upload(client, headers, case_ref, name="note.txt", content=secret,
            content_type="text/plain")

    stored = db_session.query(Evidence).one()
    on_disk = open(stored.stored_path, "rb").read()

    assert secret not in on_disk
    # ...but it still decrypts back to exactly what was submitted.
    assert storage.load(stored.stored_path) == secret


def test_upload_records_a_custody_event(client, make_user, auth_headers):
    """REQ-11: the upload itself is the first link in the chain."""
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)
    evidence_id = _upload(client, headers, case_ref).json()["id"]

    chain = client.get(f"/api/v1/evidence/{evidence_id}/custody", headers=headers)
    assert chain.status_code == 200
    events = chain.json()
    assert len(events) == 1
    assert events[0]["action"] == "uploaded"
    assert events[0]["prev_hash"] == "0" * 64


def test_download_appends_to_the_chain(client, make_user, auth_headers):
    """Viewing evidence is itself a custody event -- that is the point."""
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)
    evidence_id = _upload(client, headers, case_ref).json()["id"]

    downloaded = client.get(f"/api/v1/evidence/{evidence_id}/download", headers=headers)
    assert downloaded.status_code == 200
    assert downloaded.content == b"fake-png-bytes"

    events = client.get(f"/api/v1/evidence/{evidence_id}/custody", headers=headers).json()
    assert [e["action"] for e in events] == ["uploaded", "downloaded"]


def test_verify_endpoint_reports_an_intact_chain(client, make_user, auth_headers):
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)
    evidence_id = _upload(client, headers, case_ref).json()["id"]

    verification = client.get(f"/api/v1/evidence/{evidence_id}/verify", headers=headers)
    assert verification.status_code == 200
    assert verification.json() == {
        "evidence_id": evidence_id,
        "chain_intact": True,
        "file_intact": True,
        "broken_at_event_id": None,
    }


def test_verify_detects_a_swapped_file(client, make_user, auth_headers, db_session):
    """The chain protects the log; the digest protects the file itself."""
    from app.models.evidence import Evidence

    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)
    evidence_id = _upload(client, headers, case_ref).json()["id"]

    # Replace the stored ciphertext with a valid encryption of different bytes.
    stored = db_session.get(Evidence, evidence_id)
    replacement_path, _ = storage.store(
        b"totally different content", case_ref=case_ref, filename="x"
    )
    stored.stored_path = replacement_path
    db_session.commit()

    verification = client.get(
        f"/api/v1/evidence/{evidence_id}/verify", headers=headers
    ).json()
    assert verification["chain_intact"] is True
    assert verification["file_intact"] is False


def test_oversized_upload_is_rejected(client, make_user, auth_headers):
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)

    too_big = b"x" * (storage.MAX_UPLOAD_BYTES + 1)
    response = _upload(client, headers, case_ref, name="big.txt", content=too_big,
                       content_type="text/plain")
    assert response.status_code == 422
    assert "limit" in response.json()["detail"].lower()


def test_unsupported_file_type_is_rejected(client, make_user, auth_headers):
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)

    response = _upload(client, headers, case_ref, name="payload.exe",
                       content=b"MZ...", content_type="application/x-msdownload")
    assert response.status_code == 422


def test_malware_scan_blocks_a_known_bad_file(client, make_user, auth_headers):
    """SRS 3.3: uploads are scanned before storage, not after."""
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)

    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    response = _upload(client, headers, case_ref, name="eicar.txt", content=eicar,
                       content_type="text/plain")
    assert response.status_code == 422
    assert "malware" in response.json()["detail"].lower()


def test_empty_upload_is_rejected(client, make_user, auth_headers):
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)

    response = _upload(client, headers, case_ref, name="empty.txt", content=b"",
                       content_type="text/plain")
    assert response.status_code == 422


def test_unrelated_victim_cannot_see_evidence(client, make_user, auth_headers):
    """SRS 6.3: evidence access is restricted, not merely unlisted."""
    make_user("a@example.com")
    make_user("b@example.com")
    owner = auth_headers("a@example.com")
    case_ref = _submit(client, owner)
    evidence_id = _upload(client, owner, case_ref).json()["id"]

    stranger = auth_headers("b@example.com")
    assert client.get(
        f"/api/v1/cases/{case_ref}/evidence", headers=stranger
    ).status_code == 403
    assert client.get(
        f"/api/v1/evidence/{evidence_id}/download", headers=stranger
    ).status_code == 403


def test_unassigned_investigator_cannot_see_evidence(client, make_user, auth_headers):
    make_user("victim@example.com")
    make_user("inv1@example.com", Role.INVESTIGATOR)
    make_user("inv2@example.com", Role.INVESTIGATOR)

    owner = auth_headers("victim@example.com")
    case_ref = _submit(client, owner, HIGH_RISK_TEXT)  # auto-assigns to inv1
    _upload(client, owner, case_ref)

    response = client.get(
        f"/api/v1/cases/{case_ref}/evidence", headers=auth_headers("inv2@example.com")
    )
    assert response.status_code == 403


def test_evidence_cannot_be_deleted_only_archived(client, make_user, auth_headers):
    """REQ-13: there is no delete route at all, by design."""
    make_user("victim@example.com")
    make_user("inv1@example.com", Role.INVESTIGATOR)
    owner = auth_headers("victim@example.com")
    case_ref = _submit(client, owner, HIGH_RISK_TEXT)
    evidence_id = _upload(client, owner, case_ref).json()["id"]

    assert client.delete(
        f"/api/v1/evidence/{evidence_id}", headers=auth_headers("inv1@example.com")
    ).status_code in (404, 405)

    archived = client.post(
        f"/api/v1/evidence/{evidence_id}/archive",
        json={"reason": "Duplicate of the earlier screenshot."},
        headers=auth_headers("inv1@example.com"),
    )
    assert archived.status_code == 200
    assert archived.json()["is_archived"] is True
    assert archived.json()["archive_reason"]


def test_archiving_requires_a_reason(client, make_user, auth_headers):
    make_user("victim@example.com")
    make_user("inv1@example.com", Role.INVESTIGATOR)
    owner = auth_headers("victim@example.com")
    case_ref = _submit(client, owner, HIGH_RISK_TEXT)
    evidence_id = _upload(client, owner, case_ref).json()["id"]

    response = client.post(
        f"/api/v1/evidence/{evidence_id}/archive",
        json={"reason": ""},
        headers=auth_headers("inv1@example.com"),
    )
    assert response.status_code == 422


def test_victim_cannot_archive_evidence(client, make_user, auth_headers):
    make_user("victim@example.com")
    headers = auth_headers("victim@example.com")
    case_ref = _submit(client, headers)
    evidence_id = _upload(client, headers, case_ref).json()["id"]

    response = client.post(
        f"/api/v1/evidence/{evidence_id}/archive",
        json={"reason": "I changed my mind about this one."},
        headers=headers,
    )
    assert response.status_code == 403


def test_archived_evidence_survives_in_the_chain(client, make_user, auth_headers):
    make_user("victim@example.com")
    make_user("inv1@example.com", Role.INVESTIGATOR)
    owner = auth_headers("victim@example.com")
    case_ref = _submit(client, owner, HIGH_RISK_TEXT)
    evidence_id = _upload(client, owner, case_ref).json()["id"]

    client.post(
        f"/api/v1/evidence/{evidence_id}/archive",
        json={"reason": "Superseded by a clearer capture."},
        headers=auth_headers("inv1@example.com"),
    )

    verification = client.get(
        f"/api/v1/evidence/{evidence_id}/verify", headers=owner
    ).json()
    assert verification["chain_intact"] is True

    events = client.get(f"/api/v1/evidence/{evidence_id}/custody", headers=owner).json()
    assert events[-1]["action"] == "archived"
    assert events[-1]["detail"] == "Superseded by a clearer capture."
