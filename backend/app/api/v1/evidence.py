"""Evidence upload, retrieval and custody. REQ-10, REQ-11, REQ-13.

Every read and write of an evidence item appends to its custody chain, so the
chain records who touched what and when -- including mere viewing, which is
what makes it a chain of custody rather than an upload log.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import CustodyAction, Role
from app.models.evidence import CustodyEvent, Evidence
from app.models.report import Case
from app.models.user import User
from app.schemas import (
    ChainVerification,
    CustodyEventOut,
    EvidenceArchive,
    EvidenceOut,
)
from app.services import audit, custody, storage

router = APIRouter(tags=["evidence"])


def _load_case(db: Session, case_ref: str) -> Case:
    case = db.scalars(select(Case).where(Case.case_ref == case_ref)).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


def _assert_can_access(case: Case, user: User) -> None:
    """SRS 6.3: the assigned investigator, recovery officers, admins, and the
    victim who owns the case. Nobody else sees evidence."""
    if user.role in (Role.ADMIN, Role.RECOVERY_OFFICER):
        return
    if user.role == Role.INVESTIGATOR and case.assigned_investigator_id == user.id:
        return
    if case.report and case.report.reporter_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to access this evidence"
    )


@router.post(
    "/cases/{case_ref}/evidence",
    response_model=EvidenceOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    case_ref: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Evidence:
    """REQ-10: victims and investigators upload evidence to a case."""
    case = _load_case(db, case_ref)
    _assert_can_access(case, user)

    payload = await file.read()
    try:
        storage.validate(file.filename or "unnamed", file.content_type or "", payload)
    except storage.UploadRejected as exc:
        # 422, not 500: the upload is understood and deliberately refused.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    stored_path, digest = storage.store(
        payload, case_ref=case.case_ref, filename=file.filename or "unnamed"
    )

    evidence = Evidence(
        case_id=case.id,
        uploaded_by_id=user.id,
        filename=file.filename or "unnamed",
        stored_path=stored_path,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(payload),
        sha256=digest,
    )
    db.add(evidence)
    db.flush()

    custody.append_event(
        db,
        evidence_id=evidence.id,
        actor_id=user.id,
        action=CustodyAction.UPLOADED,
        detail=f"sha256={digest}",
    )

    # Appendix B keeps this flag on the report itself.
    case.report.evidence_attached = True

    audit.record(
        db,
        actor_id=user.id,
        action="evidence.upload",
        target=f"evidence:{evidence.id}",
        detail=f"case:{case.case_ref}",
    )
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("/cases/{case_ref}/evidence", response_model=list[EvidenceOut])
def list_evidence(
    case_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[Evidence]:
    case = _load_case(db, case_ref)
    _assert_can_access(case, user)
    return list(
        db.scalars(
            select(Evidence).where(Evidence.case_id == case.id).order_by(Evidence.id.asc())
        ).all()
    )


@router.get("/evidence/{evidence_id}/download")
def download_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Decrypt and return the file, recording the access in the chain."""
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    case = db.get(Case, evidence.case_id)
    _assert_can_access(case, user)

    payload = storage.load(evidence.stored_path)

    custody.append_event(
        db,
        evidence_id=evidence.id,
        actor_id=user.id,
        action=CustodyAction.DOWNLOADED,
    )
    audit.record(
        db, actor_id=user.id, action="evidence.download", target=f"evidence:{evidence.id}"
    )
    db.commit()

    return Response(
        content=payload,
        media_type=evidence.content_type,
        headers={"Content-Disposition": f'attachment; filename="{evidence.filename}"'},
    )


@router.get("/evidence/{evidence_id}/custody", response_model=list[CustodyEventOut])
def custody_log(
    evidence_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CustodyEvent]:
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    _assert_can_access(db.get(Case, evidence.case_id), user)

    return list(
        db.scalars(
            select(CustodyEvent)
            .where(CustodyEvent.evidence_id == evidence_id)
            .order_by(CustodyEvent.id.asc())
        ).all()
    )


@router.get("/evidence/{evidence_id}/verify", response_model=ChainVerification)
def verify_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChainVerification:
    """Prove the custody chain is unbroken -- and the file itself unaltered."""
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    _assert_can_access(db.get(Case, evidence.case_id), user)

    chain_intact, broken_at = custody.verify_chain(db, evidence_id)

    # The chain proves the log was not rewritten; re-hashing the stored file
    # proves the file behind the log is still the one that was submitted.
    try:
        file_intact = storage.sha256_of(storage.load(evidence.stored_path)) == evidence.sha256
    except Exception:
        file_intact = False

    return ChainVerification(
        evidence_id=evidence_id,
        chain_intact=chain_intact,
        file_intact=file_intact,
        broken_at_event_id=broken_at,
    )


@router.post("/evidence/{evidence_id}/archive", response_model=EvidenceOut)
def archive_evidence(
    evidence_id: int,
    payload: EvidenceArchive,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Evidence:
    """REQ-13: evidence is never deleted. Archiving is the only removal, and it
    demands a recorded reason and lands in the custody chain."""
    if user.role not in (Role.INVESTIGATOR, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only investigators and administrators may archive evidence",
        )

    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    _assert_can_access(db.get(Case, evidence.case_id), user)

    evidence.is_archived = True
    evidence.archive_reason = payload.reason

    custody.append_event(
        db,
        evidence_id=evidence.id,
        actor_id=user.id,
        action=CustodyAction.ARCHIVED,
        detail=payload.reason,
    )
    audit.record(
        db,
        actor_id=user.id,
        action="evidence.archive",
        target=f"evidence:{evidence.id}",
        detail=payload.reason,
    )
    db.commit()
    db.refresh(evidence)
    return evidence
