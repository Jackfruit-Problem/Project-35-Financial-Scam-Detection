"""Import every model so Base.metadata is complete for Alembic and create_all."""
from app.models.detection import AuditLog, BlacklistEntry, DetectionLog
from app.models.education import AwarenessContent, Quiz, QuizAttempt, QuizQuestion
from app.models.evidence import CustodyEvent, Evidence
from app.models.recovery import RecoveryRequest
from app.models.report import Case, CaseNote, ScamReport
from app.models.user import User

__all__ = [
    "AuditLog",
    "AwarenessContent",
    "BlacklistEntry",
    "Case",
    "CaseNote",
    "CustodyEvent",
    "DetectionLog",
    "Evidence",
    "Quiz",
    "QuizAttempt",
    "QuizQuestion",
    "RecoveryRequest",
    "ScamReport",
    "User",
]
