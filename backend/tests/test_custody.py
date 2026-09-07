"""Chain of custody. REQ-11, REQ-13.

These are the tests that make the SRS word "immutable" mean something. Each one
tampers with history the way an attacker (or a careless DBA) would, and asserts
that verification notices.
"""
from app.models.enums import CustodyAction, Role
from app.models.evidence import CustodyEvent, Evidence
from app.models.report import Case, ScamReport
from app.services import custody
from app.services.refs import new_case_ref, new_report_ref


def _seed_evidence(db_session, make_user) -> tuple[Evidence, int]:
    investigator = make_user("inv@example.com", Role.INVESTIGATOR)
    report = ScamReport(
        report_ref=new_report_ref(),
        reporter_name="Asha Rao",
        reporter_contact="9876543210",
        category="upi_fraud",
        description="Lost money to a fake refund call.",
    )
    db_session.add(report)
    db_session.flush()

    case = Case(case_ref=new_case_ref(), report_id=report.id)
    db_session.add(case)
    db_session.flush()

    evidence = Evidence(
        case_id=case.id,
        uploaded_by_id=investigator.id,
        filename="screenshot.png",
        stored_path="/evidence/screenshot.png",
        content_type="image/png",
        size_bytes=2048,
        sha256="a" * 64,
    )
    db_session.add(evidence)
    db_session.flush()
    return evidence, investigator.id


def test_first_link_starts_from_genesis(db_session, make_user):
    evidence, actor_id = _seed_evidence(db_session, make_user)

    event = custody.append_event(
        db_session,
        evidence_id=evidence.id,
        actor_id=actor_id,
        action=CustodyAction.UPLOADED,
    )
    db_session.commit()

    assert event.prev_hash == custody.GENESIS
    assert len(event.entry_hash) == 64


def test_each_link_commits_to_the_previous_one(db_session, make_user):
    evidence, actor_id = _seed_evidence(db_session, make_user)

    first = custody.append_event(
        db_session, evidence_id=evidence.id, actor_id=actor_id, action=CustodyAction.UPLOADED
    )
    second = custody.append_event(
        db_session, evidence_id=evidence.id, actor_id=actor_id, action=CustodyAction.VIEWED
    )
    db_session.commit()

    assert second.prev_hash == first.entry_hash


def test_intact_chain_verifies(db_session, make_user):
    evidence, actor_id = _seed_evidence(db_session, make_user)
    for action in (CustodyAction.UPLOADED, CustodyAction.VIEWED, CustodyAction.DOWNLOADED):
        custody.append_event(
            db_session, evidence_id=evidence.id, actor_id=actor_id, action=action
        )
    db_session.commit()

    intact, broken_at = custody.verify_chain(db_session, evidence.id)
    assert intact is True
    assert broken_at is None


def test_editing_a_historical_entry_is_detected(db_session, make_user):
    """The demo moment: rewrite a row directly in the database, get caught."""
    evidence, actor_id = _seed_evidence(db_session, make_user)
    events = [
        custody.append_event(
            db_session, evidence_id=evidence.id, actor_id=actor_id, action=action
        )
        for action in (CustodyAction.UPLOADED, CustodyAction.VIEWED, CustodyAction.DOWNLOADED)
    ]
    db_session.commit()

    # Falsify who handled the evidence, exactly as a bad actor would.
    events[1].actor_id = 9999
    db_session.commit()

    intact, broken_at = custody.verify_chain(db_session, evidence.id)
    assert intact is False
    assert broken_at == events[1].id


def test_deleting_a_link_is_detected(db_session, make_user):
    """REQ-13: history cannot be quietly shortened."""
    evidence, actor_id = _seed_evidence(db_session, make_user)
    events = [
        custody.append_event(
            db_session, evidence_id=evidence.id, actor_id=actor_id, action=action
        )
        for action in (CustodyAction.UPLOADED, CustodyAction.VIEWED, CustodyAction.DOWNLOADED)
    ]
    db_session.commit()

    db_session.delete(events[1])
    db_session.commit()

    intact, broken_at = custody.verify_chain(db_session, evidence.id)
    assert intact is False
    # The gap surfaces at the entry that pointed to the removed one.
    assert broken_at == events[2].id


def test_forging_a_hash_without_the_chain_fails(db_session, make_user):
    """Recomputing one hash is not enough -- the link to the previous stays wrong."""
    evidence, actor_id = _seed_evidence(db_session, make_user)
    custody.append_event(
        db_session, evidence_id=evidence.id, actor_id=actor_id, action=CustodyAction.UPLOADED
    )
    second = custody.append_event(
        db_session, evidence_id=evidence.id, actor_id=actor_id, action=CustodyAction.VIEWED
    )
    db_session.commit()

    second.actor_id = 9999
    second.entry_hash = custody.compute_entry_hash(
        evidence_id=second.evidence_id,
        actor_id=9999,
        action=second.action,
        timestamp_iso=second.created_at.isoformat(),
        detail=second.detail,
        # The forger guesses at the linkage instead of using the real prev hash.
        prev_hash=custody.GENESIS,
    )
    db_session.commit()

    intact, _ = custody.verify_chain(db_session, evidence.id)
    assert intact is False


def test_chains_are_independent_per_evidence_item(db_session, make_user):
    """Tampering with one item must not invalidate an unrelated one."""
    first_evidence, actor_id = _seed_evidence(db_session, make_user)
    second_evidence = Evidence(
        case_id=first_evidence.case_id,
        uploaded_by_id=actor_id,
        filename="chatlog.txt",
        stored_path="/evidence/chatlog.txt",
        content_type="text/plain",
        size_bytes=512,
        sha256="b" * 64,
    )
    db_session.add(second_evidence)
    db_session.flush()

    tampered = custody.append_event(
        db_session,
        evidence_id=first_evidence.id,
        actor_id=actor_id,
        action=CustodyAction.UPLOADED,
    )
    custody.append_event(
        db_session,
        evidence_id=second_evidence.id,
        actor_id=actor_id,
        action=CustodyAction.UPLOADED,
    )
    db_session.commit()

    tampered.action = CustodyAction.ARCHIVED
    db_session.commit()

    assert custody.verify_chain(db_session, first_evidence.id)[0] is False
    assert custody.verify_chain(db_session, second_evidence.id)[0] is True


def test_custody_events_are_never_updated_in_normal_operation(db_session, make_user):
    """append_event is the only write path -- it never rewrites an existing row."""
    evidence, actor_id = _seed_evidence(db_session, make_user)
    custody.append_event(
        db_session, evidence_id=evidence.id, actor_id=actor_id, action=CustodyAction.UPLOADED
    )
    db_session.commit()
    custody.append_event(
        db_session, evidence_id=evidence.id, actor_id=actor_id, action=CustodyAction.VIEWED
    )
    db_session.commit()

    assert db_session.query(CustodyEvent).count() == 2
