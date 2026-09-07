"""Vocabulary shared across modules. Stored as plain strings for portability."""
from enum import StrEnum


class Role(StrEnum):
    """SRS 2.3 user classes. GUEST is unauthenticated and never persisted."""

    VICTIM = "victim"
    INVESTIGATOR = "investigator"
    RECOVERY_OFFICER = "recovery_officer"
    ADMIN = "admin"


class RiskBand(StrEnum):
    """REQ-3."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CaseStatus(StrEnum):
    """REQ-12 — exactly these five values."""

    NEW = "new"
    UNDER_INVESTIGATION = "under_investigation"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class RecoveryStatus(StrEnum):
    """REQ-16 — exactly these five values."""

    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    PARTIALLY_RECOVERED = "partially_recovered"
    FULLY_RECOVERED = "fully_recovered"
    REJECTED = "rejected"


class ScamCategory(StrEnum):
    """Appendix B field layout."""

    PHISHING = "phishing"
    UPI_FRAUD = "upi_fraud"
    LOAN_APP = "loan_app"
    INVESTMENT = "investment"
    OTHER = "other"


class BlacklistType(StrEnum):
    """REQ-4 / REQ-25."""

    URL = "url"
    PHONE = "phone"
    UPI_ID = "upi_id"


class CustodyAction(StrEnum):
    """REQ-11 — the actions recorded in the chain of custody."""

    UPLOADED = "uploaded"
    VIEWED = "viewed"
    DOWNLOADED = "downloaded"
    ARCHIVED = "archived"
