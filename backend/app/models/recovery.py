"""Fund-recovery tracking. REQ-15 to REQ-19."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, utcnow
from app.models.enums import RecoveryStatus


class RecoveryRequest(Base, TimestampMixin):
    """Auto-populated from the case record (REQ-15); fields per Appendix B."""

    __tablename__ = "recovery_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), unique=True, index=True)
    raised_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    bank_name: Mapped[str | None] = mapped_column(String(120), default=None)
    ifsc_code: Mapped[str | None] = mapped_column(String(11), default=None)
    account_number: Mapped[str | None] = mapped_column(String(20), default=None)

    # REQ-19: reported vs recovered, tracked side by side.
    amount_reported: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_recovered: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    status: Mapped[str] = mapped_column(String(25), default=RecoveryStatus.REQUESTED)
    remarks: Mapped[str | None] = mapped_column(Text, default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
