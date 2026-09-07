"""Case lifecycle. REQ-9, REQ-12, REQ-14."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import CaseStatus, Role
from app.models.report import Case, CaseNote
from app.models.user import User
from app.schemas import (
    CaseDetail,
    CaseNoteCreate,
    CaseNoteOut,
    CaseOut,
    CaseStatusUpdate,
    ReportOut,
)
from app.services import audit

router = APIRouter(prefix="/cases", tags=["cases"])

_STAFF = (Role.INVESTIGATOR, Role.RECOVERY_OFFICER, Role.ADMIN)


def _load_case(db: Session, case_ref: str) -> Case:
    case = db.scalars(select(Case).where(Case.case_ref == case_ref)).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


def _assert_can_view(case: Case, user: User) -> None:
    """SRS 6.5: the assigned investigator, recovery officers, admins -- and the
    victim who reported it. Nobody else."""
    if user.role in (Role.ADMIN, Role.RECOVERY_OFFICER):
        return
    if user.role == Role.INVESTIGATOR and case.assigned_investigator_id == user.id:
        return
    if case.report and case.report.reporter_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to view this case"
    )


@router.get("", response_model=list[CaseOut], dependencies=[Depends(require_roles(*_STAFF))])
def list_cases(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[Case]:
    """Investigators see their own queue; recovery officers and admins see all."""
    query = select(Case).order_by(Case.id.desc())
    if user.role == Role.INVESTIGATOR:
        query = query.where(Case.assigned_investigator_id == user.id)
    return list(db.scalars(query).all())


@router.get("/{case_ref}", response_model=CaseDetail)
def get_case(
    case_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> CaseDetail:
    case = _load_case(db, case_ref)
    _assert_can_view(case, user)

    investigator = (
        db.get(User, case.assigned_investigator_id)
        if case.assigned_investigator_id
        else None
    )
    return CaseDetail(
        case=CaseOut.model_validate(case),
        report=ReportOut.model_validate(case.report),
        investigator_name=investigator.full_name if investigator else None,
    )


@router.post(
    "/{case_ref}/assign/{investigator_id}",
    response_model=CaseOut,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def assign_case(
    case_ref: str,
    investigator_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Case:
    """REQ-9, manual half: an administrator assigns a case to an investigator."""
    case = _load_case(db, case_ref)
    investigator = db.get(User, investigator_id)
    if investigator is None or investigator.role != Role.INVESTIGATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Not an investigator"
        )

    case.assigned_investigator_id = investigator.id
    if case.status == CaseStatus.NEW:
        case.status = CaseStatus.UNDER_INVESTIGATION

    audit.record(
        db,
        actor_id=user.id,
        action="case.assign",
        target=f"case:{case.case_ref}",
        detail=f"investigator:{investigator.id}",
    )
    db.commit()
    db.refresh(case)
    return case


@router.patch("/{case_ref}/status", response_model=CaseOut)
def update_status(
    case_ref: str,
    payload: CaseStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Case:
    """REQ-12 and SRS 6.5: only the assigned investigator moves a case."""
    case = _load_case(db, case_ref)

    if user.role != Role.INVESTIGATOR or case.assigned_investigator_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned investigator may change case status",
        )

    previous = case.status
    case.status = payload.status

    if payload.note:
        db.add(CaseNote(case_id=case.id, author_id=user.id, body=payload.note))

    audit.record(
        db,
        actor_id=user.id,
        action="case.status_change",
        target=f"case:{case.case_ref}",
        detail=f"{previous} -> {payload.status}",
    )
    db.commit()
    db.refresh(case)
    return case


@router.post(
    "/{case_ref}/notes",
    response_model=CaseNoteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*_STAFF))],
)
def add_note(
    case_ref: str,
    payload: CaseNoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CaseNote:
    """REQ-14: timestamped and attributed to its author."""
    case = _load_case(db, case_ref)
    _assert_can_view(case, user)

    note = CaseNote(case_id=case.id, author_id=user.id, body=payload.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{case_ref}/notes", response_model=list[CaseNoteOut])
def list_notes(
    case_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[CaseNote]:
    case = _load_case(db, case_ref)
    _assert_can_view(case, user)
    return list(
        db.scalars(
            select(CaseNote).where(CaseNote.case_id == case.id).order_by(CaseNote.id.asc())
        ).all()
    )
