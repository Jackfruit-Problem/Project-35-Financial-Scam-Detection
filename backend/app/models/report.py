"""Scam reports and the cases raised from them. SRS 5.1-5.2, Appendix B."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow
from app.models.enums import CaseStatus


class ScamReport(Base, TimestampMixin):
    """One submission by a victim. Field lengths follow SRS Appendix B."""

    __tablename__ = "scam_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Appendix B: 12-char alphanumeric, system generated.
    report_ref: Mapped[str] = mapped_column(String(12), unique=True, index=True)

    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    reporter_name: Mapped[str] = mapped_column(String(60))
    reporter_contact: Mapped[str] = mapped_column(String(15))
    report_date: Mapped[date] = mapped_column(Date, default=lambda: utcnow().date())

    category: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text)
    amount_involved: Mapped[float | None] = mapped_column(Numeric(12, 2), default=None)
    evidence_attached: Mapped[bool] = mapped_column(Boolean, default=False)

    # Populated by the detection module; advisory only (SRS 6.2).
    risk_score: Mapped[int | None] = mapped_column(Integer, default=None)
    risk_band: Mapped[str | None] = mapped_column(String(10), default=None)

    case: Mapped["Case"] = relationship(back_populates="report", uselist=False)


class Case(Base, TimestampMixin):
    """REQ-8: every report gets a case. REQ-5: high risk auto-activates it."""

    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_ref: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("scam_reports.id"), unique=True)

    assigned_investigator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None
    )
    status: Mapped[str] = mapped_column(String(25), default=CaseStatus.NEW)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    report: Mapped[ScamReport] = relationship(back_populates="case")
    notes: Mapped[list["CaseNote"]] = relationship(back_populates="case")


class CaseNote(Base, TimestampMixin):
    """REQ-14: timestamped, author-attributed notes."""

    __tablename__ = "case_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)

    case: Mapped[Case] = relationship(back_populates="notes")
