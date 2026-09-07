"""Security audit trail. SRS 6.3: logins, evidence access, and status changes."""
from sqlalchemy.orm import Session

from app.models.detection import AuditLog


def record(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    target: str | None = None,
    detail: str | None = None,
) -> None:
    db.add(AuditLog(actor_id=actor_id, action=action, target=target, detail=detail))
