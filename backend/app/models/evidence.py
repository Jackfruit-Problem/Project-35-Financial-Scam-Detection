"""Evidence and its chain of custody. REQ-10, REQ-11, REQ-13.

The custody log is append-only and hash-chained: each entry hashes its own
contents together with the previous entry's hash, so altering or deleting any
historical row invalidates every hash after it. That is what makes the SRS
claim of immutability checkable rather than merely asserted -- see
verify_chain() in app/services/custody.py.
"""
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    # Digest of the file itself, so tampering with storage is detectable too.
    sha256: Mapped[str] = mapped_column(String(64), index=True)

    # REQ-13: never deleted, only archived with a recorded reason.
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archive_reason: Mapped[str | None] = mapped_column(Text, default=None)

    custody_events: Mapped[list["CustodyEvent"]] = relationship(back_populates="evidence")


class CustodyEvent(Base, TimestampMixin):
    """One link in the chain. Never updated, never deleted -- only appended."""

    __tablename__ = "custody_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence.id"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(20))
    detail: Mapped[str | None] = mapped_column(Text, default=None)

    # Chain linkage. prev_hash is None only for the genesis entry of each item.
    prev_hash: Mapped[str | None] = mapped_column(String(64), default=None)
    entry_hash: Mapped[str] = mapped_column(String(64), index=True)

    evidence: Mapped[Evidence] = relationship(back_populates="custody_events")
