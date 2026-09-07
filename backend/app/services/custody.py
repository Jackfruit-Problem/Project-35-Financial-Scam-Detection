"""Hash-chained chain of custody. REQ-11, REQ-13.

Why a chain and not just a table of rows: the SRS requires evidence handling to
be *immutable* so it survives legal scrutiny. A plain audit table is one UPDATE
away from being rewritten, and nothing about the table would reveal it. Here,
each entry commits to the previous entry's hash, so any edit, reordering or
deletion of history breaks verification at the first tampered link and every
link after it.

This is deliberately the same construction a blockchain uses for its ledger,
minus the distributed consensus -- we have a single trusted writer, so the
chain alone gives us tamper-evidence, which is what the requirement asks for.
"""
import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models.evidence import CustodyEvent

# Marks the first link of a chain; hashed like any other value so the genesis
# entry has no special case at verification time.
GENESIS = "0" * 64


def canonical_ts(value: datetime) -> str:
    """Normalise a timestamp to one exact string, always.

    The hash has to survive a database round trip, and databases disagree about
    timezones: SQLite drops the offset and returns a naive datetime, Postgres
    returns an aware one. Hashing datetime.isoformat() directly would therefore
    produce a different digest on write than on read, and every chain would
    fail verification for no reason at all. Everything is pinned to naive UTC.
    """
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value.isoformat(timespec="microseconds")


def compute_entry_hash(
    *,
    evidence_id: int,
    actor_id: int,
    action: str,
    timestamp_iso: str,
    detail: str | None,
    prev_hash: str,
) -> str:
    """Digest of one link. Field order is part of the format -- never reorder."""
    payload = "|".join(
        [
            str(evidence_id),
            str(actor_id),
            action,
            timestamp_iso,
            detail or "",
            prev_hash,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_event(
    db: Session,
    *,
    evidence_id: int,
    actor_id: int,
    action: str,
    detail: str | None = None,
) -> CustodyEvent:
    """Append one link to an evidence item's chain. The only way to write custody."""
    last = db.scalars(
        select(CustodyEvent)
        .where(CustodyEvent.evidence_id == evidence_id)
        .order_by(CustodyEvent.id.desc())
        .limit(1)
    ).first()

    prev_hash = last.entry_hash if last else GENESIS

    # The timestamp is part of the digest, so it is fixed here rather than left
    # to the column default -- the row must be born already hashed. Letting the
    # default assign it at flush would mean inserting a row with a null hash.
    timestamp = utcnow()

    event = CustodyEvent(
        evidence_id=evidence_id,
        actor_id=actor_id,
        action=str(action),
        detail=detail,
        prev_hash=prev_hash,
        created_at=timestamp,
        entry_hash=compute_entry_hash(
            evidence_id=evidence_id,
            actor_id=actor_id,
            action=str(action),
            timestamp_iso=canonical_ts(timestamp),
            detail=detail,
            prev_hash=prev_hash,
        ),
    )
    db.add(event)
    db.flush()
    return event


def verify_chain(db: Session, evidence_id: int) -> tuple[bool, int | None]:
    """Recompute every link.

    Returns (is_intact, first_broken_event_id). A tampered or deleted row shows
    up as a mismatch at that link; everything after it is suspect too.
    """
    events = db.scalars(
        select(CustodyEvent)
        .where(CustodyEvent.evidence_id == evidence_id)
        .order_by(CustodyEvent.id.asc())
    ).all()

    expected_prev = GENESIS
    for event in events:
        if event.prev_hash != expected_prev:
            return False, event.id

        recomputed = compute_entry_hash(
            evidence_id=event.evidence_id,
            actor_id=event.actor_id,
            action=event.action,
            timestamp_iso=canonical_ts(event.created_at),
            detail=event.detail,
            prev_hash=event.prev_hash,
        )
        if recomputed != event.entry_hash:
            return False, event.id

        expected_prev = event.entry_hash

    return True, None
