"""
SQLAlchemy ORM models for FastAPI intelligence layer.
Tables: insurers, exclusion_rules, insurer_rules, diagnosis_overrides,
        claim_analyses, bill_line_items
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ─── Enums ────────────────────────────────────────────────────────────────────

PayabilityStatus = Enum(
    "PAYABLE",
    "NOT_PAYABLE",
    "PARTIALLY_PAYABLE",
    "VERIFY_WITH_TPA",
    name="payability_status",
)

BillingMode = Enum("itemized", "package", "mixed", name="billing_mode")
PolicyType = Enum("individual", "floater", "group", name="policy_type")
HospitalType = Enum("empanelled", "non_empanelled", name="hospital_type")


# ─── Reference / Rule Tables ──────────────────────────────────────────────────


class Insurer(Base):
    __tablename__ = "insurers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    plans: Mapped[dict | None] = mapped_column(JSON)  # Legacy JSON blob
    room_rent_default: Mapped[int | None] = mapped_column()  # ₹/day
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    insurer_rules: Mapped[list["InsurerRule"]] = relationship(back_populates="insurer")
    analyses: Mapped[list["ClaimAnalysis"]] = relationship(back_populates="insurer")
    plans_rel: Mapped[list["Plan"]] = relationship(back_populates="insurer")
    riders_rel: Mapped[list["Rider"]] = relationship(back_populates="insurer")


class PlanRider(Base):
    __tablename__ = "plan_riders"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), primary_key=True
    )
    rider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("riders.id", ondelete="CASCADE"), primary_key=True
    )


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insurer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurers.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    room_rent_limit_pct: Mapped[float | None] = mapped_column(Numeric(4, 2))
    room_rent_limit_abs: Mapped[float | None] = mapped_column(Numeric(10, 2))
    icu_room_rent_limit_abs: Mapped[float | None] = mapped_column(Numeric(10, 2))  # Per-day ICU rate cap
    co_pay_pct: Mapped[float | None] = mapped_column(Numeric(4, 2), default=0)
    icu_limit_pct: Mapped[float | None] = mapped_column(Numeric(4, 2))
    consumables_covered: Mapped[bool] = mapped_column(Boolean, default=False)
    consumables_sublimit: Mapped[float | None] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_col: Mapped[dict | None] = mapped_column("metadata", JSON)  # Avoid conflict with Base.metadata

    insurer: Mapped["Insurer"] = relationship(back_populates="plans_rel")
    riders: Mapped[list["Rider"]] = relationship(
        secondary="plan_riders", back_populates="plans"
    )


class Rider(Base):
    __tablename__ = "riders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insurer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurers.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    covers_consumables: Mapped[bool] = mapped_column(Boolean, default=False)
    covers_opd: Mapped[bool] = mapped_column(Boolean, default=False)
    covers_maternity: Mapped[bool] = mapped_column(Boolean, default=False)
    covers_dental: Mapped[bool] = mapped_column(Boolean, default=False)
    covers_critical_illness: Mapped[bool] = mapped_column(Boolean, default=False)
    additional_sum_insured: Mapped[float | None] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_col: Mapped[dict | None] = mapped_column("metadata", JSON)

    insurer: Mapped["Insurer"] = relationship(back_populates="riders_rel")
    plans: Mapped[list["Plan"]] = relationship(
        secondary="plan_riders", back_populates="riders"
    )


class ExclusionRule(Base):
    """IRDAI universal exclusions — apply to ALL insurers."""

    __tablename__ = "exclusion_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_circular: Mapped[str | None] = mapped_column(String(200))
    applies_to_all: Mapped[bool] = mapped_column(Boolean, default=True)


class InsurerRule(Base):
    """Insurer-specific rule overrides on top of IRDAI universals."""

    __tablename__ = "insurer_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insurer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurers.id"), nullable=False
    )
    item_category: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    verdict: Mapped[str] = mapped_column(PayabilityStatus, nullable=False)
    payable_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    plan_codes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))  # None = all plans

    insurer: Mapped["Insurer"] = relationship(back_populates="insurer_rules")


class DiagnosisOverride(Base):
    """
    Diagnosis-aware payability overrides.
    These run BEFORE exclusion rules to prevent false rejections
    (e.g., knee implants should not be rejected as 'equipment').
    """

    __tablename__ = "diagnosis_overrides"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    diagnosis_keyword: Mapped[str] = mapped_column(String(200), nullable=False)
    item_category: Mapped[str] = mapped_column(String(100), nullable=False)
    item_keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    override_status: Mapped[str] = mapped_column(PayabilityStatus, nullable=False)
    payable_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


# ─── Analysis / Claim Tables ──────────────────────────────────────────────────


class ClaimAnalysis(Base):
    __tablename__ = "claim_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insurer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurers.id"), nullable=False
    )
    # user_ref links to Next.js users table (same DB, no FK constraint across ORM owners)
    user_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    billing_mode: Mapped[str] = mapped_column(BillingMode, default="itemized")
    policy_type: Mapped[str] = mapped_column(PolicyType, default="individual")
    hospital_type: Mapped[str] = mapped_column(HospitalType, default="empanelled")
    diagnosis: Mapped[str | None] = mapped_column(String(300))

    sum_insured: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    room_rent_limit: Mapped[float | None] = mapped_column(Numeric(10, 2))

    total_billed: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_payable: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_pending_verification: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_at_risk: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    rejection_rate_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    action_items: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    insurer: Mapped["Insurer"] = relationship(back_populates="analyses")
    line_items: Mapped[list["BillLineItem"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class BillLineItem(Base):
    __tablename__ = "bill_line_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_analyses.id"), nullable=False
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)
    billed_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payable_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    status: Mapped[str] = mapped_column(PayabilityStatus, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    rule_matched: Mapped[str | None] = mapped_column(String(200))  # which rule fired
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=0.55)

    rejection_reason: Mapped[str | None] = mapped_column(Text)
    recovery_action: Mapped[str | None] = mapped_column(Text)
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False)

    analysis: Mapped["ClaimAnalysis"] = relationship(back_populates="line_items")


class SubLimitRule(Base):
    """
    Per-claim aggregate sub-limits for specific item categories.
    Applied after individual verdicts — caps total payable for all matched items.
    e.g. insurer pays max ₹50,000 for consumables even if item verdicts sum to more.
    """

    __tablename__ = "sublimit_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insurer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurers.id"), nullable=False
    )
    # Item category this limit applies to (matches Step 0 taxonomy)
    item_category: Mapped[str] = mapped_column(String(100), nullable=False)
    # Optional: restrict to specific plan codes (NULL = applies to all plans)
    plan_codes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    # Maximum payable across all items of this category in a single claim
    max_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    # Human-readable note for auditing (e.g. "IRDAI caps consumables at ₹50K under Optima")
    note: Mapped[str | None] = mapped_column(Text)

    insurer: Mapped["Insurer"] = relationship()
