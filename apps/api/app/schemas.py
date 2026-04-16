"""
Pydantic v2 request/response schemas for the FastAPI intelligence layer.
These are SEPARATE from SQLAlchemy ORM models.
"""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ─── Enums ────────────────────────────────────────────────────────────────────


class PayabilityStatus(str, Enum):
    PAYABLE = "PAYABLE"
    NOT_PAYABLE = "NOT_PAYABLE"
    PARTIALLY_PAYABLE = "PARTIALLY_PAYABLE"
    VERIFY_WITH_TPA = "VERIFY_WITH_TPA"


class BillingMode(str, Enum):
    ITEMIZED = "itemized"
    PACKAGE = "package"
    MIXED = "mixed"


class PolicyType(str, Enum):
    INDIVIDUAL = "individual"
    FLOATER = "floater"
    GROUP = "group"


class HospitalType(str, Enum):
    EMPANELLED = "empanelled"
    NON_EMPANELLED = "non_empanelled"


class ConfidenceBasis(str, Enum):
    IRDAI_RULE = "IRDAI_RULE"
    DIAGNOSIS_OVERRIDE = "DIAGNOSIS_OVERRIDE"
    INSURER_RULE = "INSURER_RULE"
    BILLING_MODE = "BILLING_MODE"
    CALCULATION = "CALCULATION"
    LLM_REASONING = "LLM_REASONING"
    UNCLASSIFIED = "UNCLASSIFIED"


# ─── Request Schemas ──────────────────────────────────────────────────────────


class BillItemInput(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    billed_amount: float = Field(..., gt=0)

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return v.strip()


class AnalyzeRequest(BaseModel):
    insurer_code: str = Field(..., description="e.g. STAR_HEALTH, HDFC_ERGO")
    plan_code: str = Field(..., description="Plan code selected by user")
    rider_codes: list[str] = Field(default_factory=list, description="List of selected rider codes for the plan")
    policy_type: PolicyType = PolicyType.INDIVIDUAL
    hospital_type: HospitalType = HospitalType.EMPANELLED
    billing_mode: BillingMode = BillingMode.ITEMIZED
    diagnosis: str | None = Field(None, max_length=300)
    sum_insured: float = Field(..., gt=0)
    icu_days: int | None = Field(None, gt=0, description="Days spent in ICU/ICCU/HDU/NICU/PICU")
    general_ward_days: int | None = Field(None, gt=0, description="Days spent in general/private/AC ward")
    bill_items: list[BillItemInput] = Field(..., min_length=1)
    user_ref: uuid.UUID | None = None  # Passed from Next.js BFF


class ParseRequest(BaseModel):
    s3_key: str = Field(..., description="R2 object key for the uploaded file")
    file_type: str = Field(..., description="pdf or image")
    job_id: uuid.UUID


# ─── Response Schemas ─────────────────────────────────────────────────────────


class AnalyzedLineItem(BaseModel):
    id: uuid.UUID
    description: str
    billed_amount: float
    payable_amount: float
    status: PayabilityStatus
    category: str | None
    rule_matched: str | None
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_basis: ConfidenceBasis
    rejection_reason: str | None
    recovery_action: str | None
    llm_used: bool = False


class AnalysisSummary(BaseModel):
    total_billed: float
    total_payable: float
    total_at_risk: float
    rejection_rate_pct: float
    items_count: int
    not_payable_count: int
    partial_count: int
    verify_count: int
    top_rejection_categories: list[str]


class AnalyzeResponse(BaseModel):
    analysis_id: uuid.UUID
    insurer_name: str
    insurer_code: str
    billing_mode: BillingMode
    diagnosis: str | None
    line_items: list[AnalyzedLineItem]
    summary: AnalysisSummary
    action_items: list[str]
    disclaimer: str = (
        "This analysis is an estimate based on IRDAI guidelines and insurer patterns. "
        "Final claim payability is determined by your TPA/insurer. "
        "This is not legal or financial advice."
    )


class ParsedItem(BaseModel):
    description: str
    billed_amount: float
    days: int | None = None  # Detected from item text, e.g. "ICU - 5 days @ ₹3,000"


class ParseResponse(BaseModel):
    job_id: uuid.UUID
    items: list[ParsedItem]
    raw_item_count: int
    parse_method: str  # "pdfplumber", "pytesseract", "gpt4o"
    # Hospital stay duration extracted from the bill
    admission_date: str | None = None
    discharge_date: str | None = None
    icu_days: int | None = None
    general_ward_days: int | None = None
    total_days: int | None = None


class RiderDetail(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    covers_consumables: bool = False
    covers_opd: bool = False
    covers_maternity: bool = False
    covers_dental: bool = False
    covers_critical_illness: bool = False
    additional_sum_insured: float | None = None


class PlanDetail(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    room_rent_limit_pct: float | None = None
    room_rent_limit_abs: float | None = None
    co_pay_pct: float | None = None
    icu_limit_pct: float | None = None
    consumables_covered: bool = False
    consumables_sublimit: float | None = None
    riders: list[RiderDetail] = Field(default_factory=list)


class InsurerPlan(BaseModel):
    name: str
    code: str
    features: list[str]


class InsurerResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    logo_url: str | None
    plans: list[PlanDetail] | None
    room_rent_default: int | None


class ReportRequest(BaseModel):
    analysis_id: uuid.UUID


class ReportResponse(BaseModel):
    analysis_id: uuid.UUID
    r2_key: str
    download_url: str  # Presigned URL
