"""Recovery and reporting assistance. REQ-15 to REQ-19.

The victim never edits recovery state -- they read it and are notified of
changes. Recording a recovery outcome is a bank-liaison action, so it is
restricted to recovery officers and administrators.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import RecoveryStatus, Role
from app.models.evidence import Evidence
from app.models.recovery import RecoveryRequest
from app.models.report import Case
from app.models.user import User
from app.schemas import (
    RecoveryOut,
    RecoveryRequestCreate,
    RecoveryStatusUpdate,
)
from app.services import audit, notifications, reports_pdf

router = APIRouter(tags=["recovery"])

_OFFICERS = (Role.RECOVERY_OFFICER, Role.ADMIN)


def _load_case(db: Session, case_ref: str) -> Case:
    case = db.scalars(select(Case).where(Case.case_ref == case_ref)).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


def _load_recovery(db: Session, case: Case) -> RecoveryRequest:
    recovery = db.scalars(
        select(RecoveryRequest).where(RecoveryRequest.case_id == case.id)
    ).first()
    if recovery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recovery request has been raised for this case",
        )
    return recovery


def _assert_can_view(case: Case, user: User) -> None:
    if user.role in _OFFICERS:
        return
    if user.role == Role.INVESTIGATOR and case.assigned_investigator_id == user.id:
        return
    if case.report and case.report.reporter_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to view this case"
    )


@router.post(
    "/cases/{case_ref}/recovery",
    response_model=RecoveryOut,
    status_code=status.HTTP_201_CREATED,
)
def raise_recovery_request(
    case_ref: str,
    payload: RecoveryRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RecoveryRequest:
    """REQ-15: auto-populated from the case record.

    The caller supplies only what the case cannot know -- the bank the money
    went to. Everything else (the amount lost, the reporter, the case) is
    lifted from data already captured, which is the whole point of the
    requirement: nobody retypes what the system already holds.
    """
    case = _load_case(db, case_ref)

    if user.role not in (*_OFFICERS, Role.INVESTIGATOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only investigators and recovery officers may raise a recovery request",
        )

    existing = db.scalars(
        select(RecoveryRequest).where(RecoveryRequest.case_id == case.id)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A recovery request already exists for this case",
        )

    recovery = RecoveryRequest(
        case_id=case.id,
        raised_by_id=user.id,
        bank_name=payload.bank_name,
        ifsc_code=payload.ifsc_code,
        account_number=payload.account_number,
        # REQ-19: seeded from the reported loss so the two figures share a source.
        amount_reported=case.report.amount_involved or 0,
        status=RecoveryStatus.REQUESTED,
    )
    db.add(recovery)
    db.flush()

    audit.record(
        db, actor_id=user.id, action="recovery.raise", target=f"case:{case.case_ref}"
    )
    notifications.notify_recovery_change(
        db, case=case, recovery=recovery, previous=None, actor_id=user.id
    )
    db.commit()
    db.refresh(recovery)
    return recovery


@router.get("/cases/{case_ref}/recovery", response_model=RecoveryOut)
def get_recovery(
    case_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> RecoveryRequest:
    case = _load_case(db, case_ref)
    _assert_can_view(case, user)
    return _load_recovery(db, case)


@router.patch(
    "/cases/{case_ref}/recovery",
    response_model=RecoveryOut,
    dependencies=[Depends(require_roles(*_OFFICERS))],
)
def update_recovery(
    case_ref: str,
    payload: RecoveryStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RecoveryRequest:
    """REQ-16, REQ-18, REQ-19: record an outcome and notify the victim."""
    case = _load_case(db, case_ref)
    recovery = _load_recovery(db, case)

    if payload.amount_recovered is not None:
        # Recovering more than was lost is not a partial success, it is a data
        # entry error, and it would corrupt the recovery-rate analytics.
        if payload.amount_recovered > float(recovery.amount_reported):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Amount recovered cannot exceed the amount reported lost",
            )
        recovery.amount_recovered = payload.amount_recovered

    previous = recovery.status
    recovery.status = payload.status
    if payload.remarks is not None:
        recovery.remarks = payload.remarks

    audit.record(
        db,
        actor_id=user.id,
        action="recovery.status_change",
        target=f"case:{case.case_ref}",
        detail=f"{previous} -> {payload.status}",
    )
    if previous != payload.status:
        notifications.notify_recovery_change(
            db, case=case, recovery=recovery, previous=previous, actor_id=user.id
        )
    db.commit()
    db.refresh(recovery)
    return recovery


@router.get("/cases/{case_ref}/report.pdf")
def download_case_report(
    case_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Response:
    """REQ-17: case summary with timeline, evidence list and risk score."""
    case = _load_case(db, case_ref)
    _assert_can_view(case, user)

    evidence = list(
        db.scalars(
            select(Evidence).where(Evidence.case_id == case.id).order_by(Evidence.id.asc())
        ).all()
    )
    investigator = (
        db.get(User, case.assigned_investigator_id)
        if case.assigned_investigator_id
        else None
    )

    pdf = reports_pdf.case_report(
        case=case, report=case.report, evidence=evidence, investigator=investigator
    )
    audit.record(
        db, actor_id=user.id, action="report.case_pdf", target=f"case:{case.case_ref}"
    )
    db.commit()

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="case-{case.case_ref}.pdf"'
        },
    )


@router.get("/cases/{case_ref}/recovery-report.pdf")
def download_recovery_report(
    case_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Response:
    """REQ-17, recovery variant -- the document a bank actually receives."""
    case = _load_case(db, case_ref)
    _assert_can_view(case, user)
    recovery = _load_recovery(db, case)

    pdf = reports_pdf.recovery_report(case=case, report=case.report, recovery=recovery)
    audit.record(
        db, actor_id=user.id, action="report.recovery_pdf", target=f"case:{case.case_ref}"
    )
    db.commit()

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="recovery-{case.case_ref}.pdf"'
        },
    )
