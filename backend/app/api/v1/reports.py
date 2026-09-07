"""Scam report submission -- the spine of the system. REQ-1..REQ-5, REQ-8, REQ-9.

One submission runs the whole detection-to-case path: score the description,
persist the report, open a case for it, and put high-risk cases straight into
the investigator queue.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import CaseStatus, RiskBand, Role
from app.models.report import Case, ScamReport
from app.models.user import User
from app.schemas import (
    AnalyseRequest,
    AnalyseResponse,
    ReportCreate,
    ReportOut,
    ReportSubmissionResult,
)
from app.services import audit, detection, refs
from app.services.assignment import next_investigator

router = APIRouter(tags=["reports"])


@router.post("/detection/analyse", response_model=AnalyseResponse)
def analyse(
    payload: AnalyseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalyseResponse:
    """REQ-1, REQ-2, REQ-3: score a message, URL, or transaction detail."""
    result = detection.analyse(db, payload.text, requested_by_id=user.id)
    db.commit()
    return AnalyseResponse(**result)


@router.post(
    "/reports",
    response_model=ReportSubmissionResult,
    status_code=status.HTTP_201_CREATED,
)
def submit_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportSubmissionResult:
    """Submit a scam report.

    REQ-8 reads "a Case ID for every report" and REQ-5 reads "auto-create a
    case when High risk". Taken literally those conflict, so we satisfy both:
    every report opens a case record with a reference, but only a High-risk
    case is auto-assigned and moved into investigation. Low and Medium sit in
    NEW until a human picks them up.
    """
    result = detection.analyse(db, payload.description, requested_by_id=user.id)

    report = ScamReport(
        report_ref=refs.new_report_ref(),
        reporter_id=user.id,
        reporter_name=payload.reporter_name,
        reporter_contact=payload.reporter_contact,
        category=payload.category,
        description=payload.description,
        amount_involved=payload.amount_involved,
        risk_score=result["risk_score"],
        risk_band=result["risk_band"],
    )
    db.add(report)
    db.flush()

    case = Case(case_ref=refs.new_case_ref(), report_id=report.id)

    if result["risk_band"] == RiskBand.HIGH:
        # REQ-5 + REQ-9: high risk enters the queue without waiting for an admin.
        investigator = next_investigator(db)
        if investigator is not None:
            case.assigned_investigator_id = investigator.id
            case.status = CaseStatus.UNDER_INVESTIGATION

    db.add(case)
    db.flush()

    audit.record(
        db,
        actor_id=user.id,
        action="report.submit",
        target=f"case:{case.case_ref}",
        detail=f"risk={result['risk_score']} band={result['risk_band']}",
    )
    db.commit()
    db.refresh(report)
    db.refresh(case)

    return ReportSubmissionResult(
        report=ReportOut.model_validate(report),
        case=case,
        detection=AnalyseResponse(**result),
    )


@router.get("/reports/mine", response_model=list[ReportOut])
def my_reports(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ScamReport]:
    """A victim tracks their own submissions and nothing else (SRS 6.5: PII)."""
    return list(
        db.scalars(
            select(ScamReport)
            .where(ScamReport.reporter_id == user.id)
            .order_by(ScamReport.id.desc())
        ).all()
    )


@router.get("/reports/{report_ref}", response_model=ReportOut)
def get_report(
    report_ref: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScamReport:
    report = db.scalars(
        select(ScamReport).where(ScamReport.report_ref == report_ref)
    ).first()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # SRS 6.5: PII is visible to the reporter and to staff, not to other victims.
    staff = {Role.INVESTIGATOR, Role.RECOVERY_OFFICER, Role.ADMIN}
    if report.reporter_id != user.id and user.role not in staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to view this report"
        )
    return report


@router.get(
    "/reports",
    response_model=list[ReportOut],
    dependencies=[Depends(require_roles(Role.INVESTIGATOR, Role.RECOVERY_OFFICER, Role.ADMIN))],
)
def list_reports(db: Session = Depends(get_db)) -> list[ScamReport]:
    return list(db.scalars(select(ScamReport).order_by(ScamReport.id.desc())).all())
