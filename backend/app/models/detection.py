"""Detection-side persistence: blacklist, request log, security audit log."""
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class BlacklistEntry(Base, TimestampMixin):
    """REQ-4, REQ-25. Checked before the ML model is invoked."""

    __tablename__ = "blacklist_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str] = mapped_column(String(20), index=True)
    value: Mapped[str] = mapped_column(String(255), index=True)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    added_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)


class DetectionLog(Base, TimestampMixin):
    """REQ-6: every detection request and result, for audit and retraining."""

    __tablename__ = "detection_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    requested_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    input_text: Mapped[str] = mapped_column(Text)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_band: Mapped[str] = mapped_column(String(10))
    matched_blacklist: Mapped[bool] = mapped_column(Boolean, default=False)
    model_version: Mapped[str] = mapped_column(String(40), default="rules-v0")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)


class AuditLog(Base, TimestampMixin):
    """SRS 6.3: login, evidence access, and status changes are all recorded."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    action: Mapped[str] = mapped_column(String(60), index=True)
    target: Mapped[str | None] = mapped_column(String(120), default=None)
    detail: Mapped[str | None] = mapped_column(Text, default=None)
