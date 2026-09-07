"""Request/response models. Kept separate from ORM models so the API contract
can be validated independently of the storage schema."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import (
    CaseStatus,
    RecoveryStatus,
    RiskBand,
    Role,
    ScamCategory,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- auth -------------------------------------------------------------------


class UserCreate(BaseModel):
    full_name: str = Field(max_length=60)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=15)
    password: str = Field(min_length=8, max_length=128)


class UserOut(ORMModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    role: Role
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


# --- detection --------------------------------------------------------------


class AnalyseRequest(BaseModel):
    """REQ-1: free text, a URL, or transaction metadata all arrive as text."""

    text: str = Field(min_length=1, max_length=5000)


class AnalyseResponse(BaseModel):
    risk_score: int
    risk_band: RiskBand
    reasons: list[str]
    matched_blacklist: bool
    model_version: str
    latency_ms: int
    advisory_note: str


# --- reports and cases ------------------------------------------------------


class ReportCreate(BaseModel):
    reporter_name: str = Field(max_length=60)
    reporter_contact: str = Field(max_length=15)
    category: ScamCategory
    description: str = Field(min_length=1, max_length=500)
    amount_involved: float | None = Field(default=None, ge=0)


class ReportOut(ORMModel):
    id: int
    report_ref: str
    reporter_name: str
    reporter_contact: str
    report_date: date
    category: ScamCategory
    description: str
    amount_involved: float | None
    evidence_attached: bool
    risk_score: int | None
    risk_band: RiskBand | None
    created_at: datetime


class CaseOut(ORMModel):
    id: int
    case_ref: str
    report_id: int
    assigned_investigator_id: int | None
    status: CaseStatus
    created_at: datetime
    updated_at: datetime


class ReportSubmissionResult(BaseModel):
    """What the victim sees after submitting: the report, its case, and why."""

    report: ReportOut
    case: CaseOut
    detection: AnalyseResponse


class CaseStatusUpdate(BaseModel):
    status: CaseStatus
    note: str | None = Field(default=None, max_length=1000)


class CaseNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CaseNoteOut(ORMModel):
    id: int
    case_id: int
    author_id: int
    body: str
    created_at: datetime


# --- recovery ---------------------------------------------------------------


class RecoveryRequestCreate(BaseModel):
    bank_name: str | None = Field(default=None, max_length=120)
    ifsc_code: str | None = Field(default=None, max_length=11)
    account_number: str | None = Field(default=None, max_length=20)


class RecoveryStatusUpdate(BaseModel):
    status: RecoveryStatus
    amount_recovered: float | None = Field(default=None, ge=0)
    remarks: str | None = Field(default=None, max_length=1000)


class RecoveryOut(ORMModel):
    id: int
    case_id: int
    bank_name: str | None
    ifsc_code: str | None
    account_number: str | None
    amount_reported: float
    amount_recovered: float
    status: RecoveryStatus
    remarks: str | None
    created_at: datetime
    updated_at: datetime
