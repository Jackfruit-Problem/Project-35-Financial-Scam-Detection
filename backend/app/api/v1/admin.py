"""Administration. REQ-23, REQ-24, REQ-25.

Every route here is administrator-only, enforced on the router rather than
per-endpoint so a new route cannot accidentally ship unprotected.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.detection import BlacklistEntry
from app.models.enums import CaseStatus, RecoveryStatus, Role
from app.models.recovery import RecoveryRequest
from app.models.report import Case, ScamReport
from app.models.user import User
from app.schemas import (
    AnalyticsOut,
    BlacklistCreate,
    BlacklistOut,
    RoleUpdate,
    UserOut,
)
from app.services import audit

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(Role.ADMIN))],
)


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id.asc())).all())


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> User:
    """REQ-23: role assignment. This is the only way to become staff."""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    previous = target.role
    target.role = payload.role
    audit.record(
        db,
        actor_id=actor.id,
        action="admin.role_change",
        target=f"user:{target.id}",
        detail=f"{previous} -> {payload.role}",
    )
    db.commit()
    db.refresh(target)
    return target


@router.patch("/users/{user_id}/active", response_model=UserOut)
def set_active(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> User:
    """REQ-23: activation and deactivation."""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Locking the last administrator out would leave nobody able to unlock
    # anyone, including themselves.
    if not is_active and target.role == Role.ADMIN:
        remaining = db.scalar(
            select(func.count(User.id)).where(
                User.role == Role.ADMIN, User.is_active.is_(True), User.id != target.id
            )
        )
        if not remaining:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot deactivate the last active administrator",
            )

    target.is_active = is_active
    audit.record(
        db,
        actor_id=actor.id,
        action="admin.active_change",
        target=f"user:{target.id}",
        detail=f"is_active={is_active}",
    )
    db.commit()
    db.refresh(target)
    return target


@router.get("/blacklist", response_model=list[BlacklistOut])
def list_blacklist(db: Session = Depends(get_db)) -> list[BlacklistEntry]:
    return list(db.scalars(select(BlacklistEntry).order_by(BlacklistEntry.id.desc())).all())


@router.post("/blacklist", response_model=BlacklistOut, status_code=status.HTTP_201_CREATED)
def add_blacklist_entry(
    payload: BlacklistCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> BlacklistEntry:
    """REQ-25. Values are lower-cased on the way in because the detection
    lookup is exact -- otherwise Fraudster@YBL would slip past an entry for
    fraudster@ybl."""
    value = payload.value.strip().lower().rstrip("/")

    existing = db.scalars(
        select(BlacklistEntry).where(
            BlacklistEntry.entry_type == payload.entry_type, BlacklistEntry.value == value
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already blacklisted"
        )

    entry = BlacklistEntry(
        entry_type=payload.entry_type, value=value, note=payload.note, added_by_id=actor.id
    )
    db.add(entry)
    audit.record(
        db, actor_id=actor.id, action="admin.blacklist_add", target=f"{payload.entry_type}:{value}"
    )
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/blacklist/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_blacklist_entry(
    entry_id: int, db: Session = Depends(get_db), actor: User = Depends(get_current_user)
) -> None:
    """REQ-25: entries are removable, unlike evidence -- a wrongly blacklisted
    UPI ID belongs to a real person and must be correctable."""
    entry = db.get(BlacklistEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    audit.record(
        db,
        actor_id=actor.id,
        action="admin.blacklist_remove",
        target=f"{entry.entry_type}:{entry.value}",
    )
    db.delete(entry)
    db.commit()


@router.get("/analytics", response_model=AnalyticsOut)
def analytics(db: Session = Depends(get_db)) -> AnalyticsOut:
    """REQ-24: totals, resolution and recovery rates, and trending categories."""
    total_reports = db.scalar(select(func.count(ScamReport.id))) or 0
    total_cases = db.scalar(select(func.count(Case.id))) or 0
    resolved = (
        db.scalar(
            select(func.count(Case.id)).where(
                Case.status.in_((CaseStatus.RESOLVED, CaseStatus.CLOSED))
            )
        )
        or 0
    )

    reported = float(db.scalar(select(func.sum(RecoveryRequest.amount_reported))) or 0)
    recovered = float(db.scalar(select(func.sum(RecoveryRequest.amount_recovered))) or 0)

    fully_recovered = (
        db.scalar(
            select(func.count(RecoveryRequest.id)).where(
                RecoveryRequest.status == RecoveryStatus.FULLY_RECOVERED
            )
        )
        or 0
    )

    trending = [
        {"category": category, "count": count}
        for category, count in db.execute(
            select(ScamReport.category, func.count(ScamReport.id).label("count"))
            .group_by(ScamReport.category)
            .order_by(func.count(ScamReport.id).desc())
        ).all()
    ]

    return AnalyticsOut(
        total_reports=total_reports,
        total_cases=total_cases,
        resolved_cases=resolved,
        # Guarded against division by zero: an empty system reports 0%, not a crash.
        resolution_rate=round(resolved / total_cases * 100, 1) if total_cases else 0.0,
        total_amount_reported=reported,
        total_amount_recovered=recovered,
        recovery_rate=round(recovered / reported * 100, 1) if reported else 0.0,
        fully_recovered_cases=fully_recovered,
        trending_categories=trending,
    )
