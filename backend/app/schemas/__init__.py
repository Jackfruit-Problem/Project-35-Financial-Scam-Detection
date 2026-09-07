"""Request/response models. Kept separate from ORM models so the API contract
can be validated independently of the storage schema."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import (
    BlacklistType,
    CaseStatus,
    CustodyAction,
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


# --- evidence and custody ---------------------------------------------------


class EvidenceOut(ORMModel):
    id: int
    case_id: int
    uploaded_by_id: int
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    is_archived: bool
    archive_reason: str | None
    created_at: datetime


class CustodyEventOut(ORMModel):
    id: int
    evidence_id: int
    actor_id: int
    action: CustodyAction
    detail: str | None
    prev_hash: str | None
    entry_hash: str
    created_at: datetime


class ChainVerification(BaseModel):
    """Two independent checks: was the log rewritten, and was the file swapped."""

    evidence_id: int
    chain_intact: bool
    file_intact: bool
    broken_at_event_id: int | None


class EvidenceArchive(BaseModel):
    # REQ-13: a reason is mandatory, so archiving can never be silent.
    reason: str = Field(min_length=3, max_length=500)


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


# --- education --------------------------------------------------------------


class ArticleCreate(BaseModel):
    title: str = Field(max_length=200)
    category: ScamCategory
    body: str = Field(min_length=1)


class ArticleUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    category: ScamCategory | None = None
    body: str | None = None
    is_published: bool | None = None


class ArticleOut(ORMModel):
    id: int
    title: str
    category: ScamCategory
    body: str
    is_published: bool
    created_at: datetime


class QuizOut(ORMModel):
    id: int
    title: str
    category: ScamCategory


class QuizQuestionOut(BaseModel):
    """Deliberately has no correct_index -- see the get_quiz docstring."""

    id: int
    prompt: str
    options: list[str]


class QuizDetail(BaseModel):
    id: int
    title: str
    category: ScamCategory
    questions: list[QuizQuestionOut]


class QuizAnswer(BaseModel):
    question_id: int
    selected_index: int = Field(ge=0)


class QuizSubmission(BaseModel):
    answers: list[QuizAnswer]


class QuizFeedback(BaseModel):
    question_id: int
    prompt: str
    selected_index: int | None
    correct_index: int
    is_correct: bool
    explanation: str | None


class QuizAttemptResult(BaseModel):
    quiz_id: int
    score: int
    total: int
    feedback: list[QuizFeedback]


# --- administration ---------------------------------------------------------


class RoleUpdate(BaseModel):
    role: Role


class BlacklistCreate(BaseModel):
    entry_type: BlacklistType
    value: str = Field(min_length=1, max_length=255)
    note: str | None = Field(default=None, max_length=500)


class BlacklistOut(ORMModel):
    id: int
    entry_type: BlacklistType
    value: str
    note: str | None
    created_at: datetime


class CategoryCount(BaseModel):
    category: ScamCategory
    count: int


class AnalyticsOut(BaseModel):
    """REQ-24: what the administrator dashboard shows."""

    total_reports: int
    total_cases: int
    resolved_cases: int
    resolution_rate: float
    total_amount_reported: float
    total_amount_recovered: float
    recovery_rate: float
    fully_recovered_cases: int
    trending_categories: list[CategoryCount]


class CaseDetail(BaseModel):
    """A case together with the report behind it.

    The list view returns cases alone, but every detail screen immediately
    needs the report too -- returning them together avoids a second round
    trip for data that is never wanted separately.
    """

    case: CaseOut
    report: ReportOut
    investigator_name: str | None = None
