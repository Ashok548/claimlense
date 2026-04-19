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
    coverage_clauses: Mapped[list["RiderCoverageClause"]] = relationship(
        back_populates="rider", cascade="all, delete-orphan"
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

    decision_source: Mapped[str | None] = mapped_column(String(100))
    policy_basis_id: Mapped[str | None] = mapped_column(String(200))
    policy_basis_text: Mapped[str | None] = mapped_column(Text)
    payable_pct_source: Mapped[str | None] = mapped_column(String(50))

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


# ─── Config-driven tables (Phase 1-4 refactor) ───────────────────────────────


class KeywordSet(Base):
    """Named, versioned keyword lists — replaces all hardcoded Python keyword constants."""

    __tablename__ = "keyword_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ItemCategory(Base):
    """
    Canonical category registry.
    Replaces: _NEVER_EXCLUDED_CATEGORIES set in step1, _recovery_action() dict,
    VALID_CATEGORIES set, and the hardcoded SYSTEM_PROMPT in step0_categorize.
    """

    __tablename__ = "item_categories"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # When true, step1 (IRDAI universal exclusions) never rejects this category
    never_excluded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_payable_by_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Fed into the Step 0 LLM categorisation prompt
    llm_examples: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    # Shown as recovery action when step1 rejects this category
    recovery_template: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DiagnosisSynonymGroup(Base):
    """
    DB-driven diagnosis synonym expansion.
    Replaces: DIAGNOSIS_SYNONYMS compile-time dict in step2_diagnosis.py.
    A new synonym mapping is added by inserting a row — zero code change.

    base_term: normalised canonical diagnosis name (e.g. "myocardial infarction")
    synonyms:  array of alternative spellings/abbreviations (e.g. ["mi", "heart attack"])
    """

    __tablename__ = "diagnosis_synonym_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    base_term: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    synonyms: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RoomRentConfig(Base):
    """
    Per-insurer (or global) room-rent detection and deduction settings.
    Replaces: ROOM_RENT_KEYWORDS and ICU_KEYWORDS constants in step4_room_rent.
    insurer_id=NULL → global default applied to all insurers without a specific row.
    """

    __tablename__ = "room_rent_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insurer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurers.id")
    )
    plan_codes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    detection_kw_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keyword_sets.id"), nullable=False
    )
    icu_kw_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keyword_sets.id"), nullable=False
    )
    # 'proportional' | 'room_only' | 'none'
    deduction_method: Mapped[str] = mapped_column(
        String(30), default="proportional", nullable=False
    )
    # When True, ICU and ward deduction ratios are tracked independently
    icu_deduction_separate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Higher priority row wins when multiple rows match the same insurer+plan
    priority: Mapped[int] = mapped_column(default=0, nullable=False)

    detection_keyword_set: Mapped["KeywordSet"] = relationship(
        "KeywordSet", foreign_keys=[detection_kw_set_id]
    )
    icu_keyword_set: Mapped["KeywordSet"] = relationship(
        "KeywordSet", foreign_keys=[icu_kw_set_id]
    )


class BillingModeRule(Base):
    """
    Billing-mode payability rules indexed by category + billing_mode.
    Replaces: CONSUMABLE_KEYWORDS constant and branch logic in step3_billing.
    insurer_id=NULL + plan_codes=NULL → universal rule applied to all insurers.
    """

    __tablename__ = "billing_mode_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insurer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurers.id")
    )
    plan_codes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    # Canonical category code this rule applies to
    item_category: Mapped[str] = mapped_column(String(50), nullable=False)
    # 'itemized' | 'package' | 'mixed'
    billing_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    verdict: Mapped[str] = mapped_column(String(30), nullable=False)
    payable_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recovery: Mapped[str | None] = mapped_column(Text)
    # Optional fallback keyword set for UNCLASSIFIED items
    fallback_kw_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keyword_sets.id")
    )
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    # Categories that bypass step3 entirely (never processed by billing-mode logic).
    # The highest-priority row with this set non-null wins.  insurer_id=NULL row
    # provides the global default; an insurer-specific row can narrow or widen it.
    bypass_categories: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    fallback_kw_set: Mapped["KeywordSet | None"] = relationship(
        "KeywordSet", foreign_keys=[fallback_kw_set_id]
    )


class RiderCoverageClause(Base):
    """
    Generic rider coverage clause — replaces the five boolean columns on riders
    (covers_consumables, covers_opd, covers_maternity, covers_dental, covers_critical_illness)
    and the hardcoded category sets / keyword fallbacks in step5b_riders.

    Each rider can have multiple clauses covering different item categories.
    A new rider benefit type is added by inserting a row here — zero code change.
    """

    __tablename__ = "rider_coverage_clauses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("riders.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Canonical category codes this clause rescues
    target_categories: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    # Optional fallback kw set for UNCLASSIFIED items (None = category-match only)
    fallback_kw_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keyword_sets.id")
    )
    verdict: Mapped[str] = mapped_column(String(30), default="PAYABLE", nullable=False)
    payable_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    # This clause only fires when the item's current status is in this list
    only_rescues_status: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=lambda: ["NOT_PAYABLE", "VERIFY_WITH_TPA"]
    )
    # Lower number = evaluated last (higher number = higher priority)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    reason_template: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    fallback_kw_set: Mapped["KeywordSet | None"] = relationship(
        "KeywordSet", foreign_keys=[fallback_kw_set_id]
    )
    rider: Mapped["Rider"] = relationship(back_populates="coverage_clauses")
