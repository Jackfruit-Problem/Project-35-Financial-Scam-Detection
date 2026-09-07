"""Round-robin case allocation. REQ-9.

Round-robin here means "the active investigator holding the fewest open cases",
which is fairer than a rotating pointer: a pointer keeps handing out work to
someone who is already buried, and it resets badly when investigators are
added or deactivated mid-semester.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import CaseStatus, Role
from app.models.report import Case
from app.models.user import User

_OPEN_STATUSES = (
    CaseStatus.NEW,
    CaseStatus.UNDER_INVESTIGATION,
    CaseStatus.ESCALATED,
)


def next_investigator(db: Session) -> User | None:
    """Least-loaded active investigator, or None if there are none to assign to."""
    open_load = (
        select(Case.assigned_investigator_id, func.count(Case.id).label("open_cases"))
        .where(Case.status.in_(_OPEN_STATUSES))
        .group_by(Case.assigned_investigator_id)
        .subquery()
    )

    row = db.execute(
        select(User)
        .outerjoin(open_load, open_load.c.assigned_investigator_id == User.id)
        .where(User.role == Role.INVESTIGATOR, User.is_active.is_(True))
        # Ties break by id so allocation is deterministic and therefore testable.
        .order_by(func.coalesce(open_load.c.open_cases, 0).asc(), User.id.asc())
        .limit(1)
    ).scalars().first()

    return row
