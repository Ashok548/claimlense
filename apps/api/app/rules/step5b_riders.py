"""
Step 5b: Rider and Plan Coverage Overrides.
This step evaluates if the current plan or any selected rider provides extended coverage
that rescues an item previously marked as NOT_PAYABLE (e.g. Consumables or OPD).

Config-driven path (post-015 migration):
  Rider benefits are driven by rider_coverage_clauses rows instead of the five
  boolean columns (covers_consumables / covers_opd / covers_maternity / etc.).
  A new benefit type is enabled by inserting a rider_coverage_clauses row — zero
  Python code changes required.

Legacy fallback (_legacy_boolean_check):
  Retained as dead code for reference only.  It is no longer invoked from the
  main path — see _warn_and_skip_legacy() below.  Migration 020 asserts that
  every rider with boolean flags has corresponding clause rows so this path
  should never be needed.  Delete after all insurers are confirmed on clauses.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Plan, Rider

logger = logging.getLogger(__name__)
from app.schemas import AnalyzedLineItem, BillItemInput, PayabilityStatus, ConfidenceBasis
from app.rules._shared import contains_phrase, normalize_text
import uuid

# ─── Compile-time fallback category sets (used as legacy path only) ─────────────
CONSUMABLE_CATEGORIES = ["CONSUMABLE", "CONSUMABLE_OVERRIDE", "CONSUMABLE_SUBLIMIT"]
OPD_CATEGORIES = ["OPD", "CONSULTATION"]
MATERNITY_CATEGORIES = ["MATERNITY", "DELIVERY"]

MATERNITY_KEYWORDS = [
    "maternity", "delivery", "c-section", "caesarean", "lscs",
    "obstetric", "obstetrics", "antenatal", "ante natal",
    "postnatal", "post natal", "prenatal", "pre natal",
    "episiotomy", "neonatal", "newborn care", "new born care",
    "vacuum delivery", "forceps delivery",
    "labour charge", "labor charge", "labour room", "labor room",
    "normal delivery", "assisted delivery",
]


async def load_rider_clauses(db: AsyncSession, rider_ids: list) -> list:
    """Load RiderCoverageClause rows for the given rider IDs.

    Eagerly loads fallback_kw_set so keyword matching works without extra queries.
    Returns [] if the table does not exist (pre-014 migration) or rider_ids is empty.
    """
    if not rider_ids:
        return []
    try:
        from app.models import RiderCoverageClause
        stmt = (
            select(RiderCoverageClause)
            .options(selectinload(RiderCoverageClause.fallback_kw_set))
            .where(RiderCoverageClause.rider_id.in_(rider_ids))
            .order_by(RiderCoverageClause.priority.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    except Exception:
        return []

def _mark_payable(item: BillItemInput, current_result: AnalyzedLineItem | None, reason: str, confidence_basis: ConfidenceBasis) -> AnalyzedLineItem:
    if current_result is None:
        return AnalyzedLineItem(
            id=uuid.uuid4(),
            description=item.description,
            billed_amount=item.billed_amount,
            payable_amount=item.billed_amount,
            status=PayabilityStatus.PAYABLE,
            category=None,
            rule_matched=reason,
            confidence=0.95,
            confidence_basis=confidence_basis,
            rejection_reason=None,
            recovery_action=None,
            llm_used=False
        )
    return current_result.model_copy(update={
        "status": PayabilityStatus.PAYABLE,
        "payable_amount": current_result.billed_amount,
        "rule_matched": reason,
        "confidence": 0.95,
        "confidence_basis": confidence_basis,
        "decision_source": "RIDER_OR_PLAN_OVERRIDE",
        "policy_basis_id": reason,
        "policy_basis_text": reason,
        "payable_pct_source": "deterministic",
        "rejection_reason": None,
        "recovery_action": None,
    })


def _ordered_riders(riders: list[Rider]) -> list[Rider]:
    """Deterministic precedence: finite rider caps are consumed first, then uncapped riders."""
    return sorted(
        riders,
        key=lambda r: (
            r.additional_sum_insured is None,
            float(r.additional_sum_insured) if r.additional_sum_insured is not None else 0.0,
            r.code,
        ),
    )


def _apply_rider_with_cap(
    item: BillItemInput,
    current_result: AnalyzedLineItem,
    rider: Rider,
    reason: str,
    rider_remaining: dict[uuid.UUID, float | None] | None,
) -> AnalyzedLineItem:
    if rider_remaining is None:
        return _mark_payable(item, current_result, reason, ConfidenceBasis.INSURER_RULE)

    remaining = rider_remaining.get(rider.id)
    if remaining is None:
        # Uncapped rider behaves as full rescue.
        return _mark_payable(item, current_result, reason, ConfidenceBasis.INSURER_RULE)

    if remaining <= 0:
        return current_result

    currently_payable = float(current_result.payable_amount)
    shortfall = max(0.0, float(item.billed_amount) - currently_payable)
    if shortfall <= 0:
        return current_result

    allocated = min(shortfall, remaining)
    rider_remaining[rider.id] = round(remaining - allocated, 2)
    new_payable = round(currently_payable + allocated, 2)
    is_full = new_payable >= float(item.billed_amount)

    return current_result.model_copy(update={
        "status": PayabilityStatus.PAYABLE if is_full else PayabilityStatus.PARTIALLY_PAYABLE,
        "payable_amount": new_payable,
        "rule_matched": (
            f"{reason}|ALLOC:{allocated:.2f}|REM:{rider_remaining[rider.id]:.2f}"
        ),
        "confidence": 0.95,
        "confidence_basis": ConfidenceBasis.INSURER_RULE,
        "decision_source": "RIDER_CAP_ALLOCATION",
        "policy_basis_id": f"RIDER:{rider.id}",
        "policy_basis_text": reason,
        "payable_pct_source": "deterministic",
        "rejection_reason": None if is_full else "Rider cap exhausted before full coverage",
        "recovery_action": None,
    })


def check_rider_and_plan_coverage(
    item: BillItemInput,
    current_result: AnalyzedLineItem | None,
    plan: Plan,
    riders: list[Rider],
    rider_clauses: list | None = None,
    item_category: str | None = None,
    rider_remaining: dict[uuid.UUID, float | None] | None = None,
) -> AnalyzedLineItem | None:
    """Override payability based on active plan inclusions or rider coverage.

    rider_clauses: list of RiderCoverageClause ORM rows loaded by the engine.
      When non-empty, uses the generic DB-driven clause loop (config-driven path).
      When None/empty, falls back to the legacy boolean column checks.
    """
    category = item_category or (current_result.category if current_result else None)

    # Guard: never override deliberate partial payout set by an insurer rule
    if (
        current_result is not None
        and current_result.status == PayabilityStatus.PARTIALLY_PAYABLE
        and current_result.confidence_basis == ConfidenceBasis.INSURER_RULE
    ):
        return current_result

    # Already payable — nothing to do
    if current_result is not None and current_result.status == PayabilityStatus.PAYABLE:
        return current_result

    desc_norm = normalize_text(item.description)

    # ── Plan-level consumables override (DB column — always config-driven) ─────────
    if current_result and current_result.status != PayabilityStatus.PAYABLE:
        is_consumable = (
            category in CONSUMABLE_CATEGORIES
            if category and category not in ("UNCLASSIFIED", None)
            else any(contains_phrase(desc_norm, normalize_text(k)) for k in ["gloves", "syringe", "mask", "disposable", "consumable"])
        )
        if is_consumable and plan.consumables_covered:
            return _mark_payable(
                item, current_result,
                f"Plan '{plan.name}' covers consumables",
                ConfidenceBasis.INSURER_RULE,
            )

    # ── Rider clause evaluation ─────────────────────────────────────────────
    rider_by_id: dict = {r.id: r for r in riders}

    if rider_clauses:
        return _check_with_clauses(
            item, current_result, rider_by_id, rider_clauses, category, desc_norm, rider_remaining
        )

    # No clause rows loaded — warn loudly instead of silently activating hardcoded
    # keyword lists.  Migration 020 asserts this never happens in production.
    _warn_and_skip_legacy(riders)
    return current_result


def _check_with_clauses(
    item: BillItemInput,
    current_result: AnalyzedLineItem | None,
    rider_by_id: dict,
    rider_clauses: list,
    category: str | None,
    desc_norm: str,
    rider_remaining: dict | None,
) -> AnalyzedLineItem | None:
    """Generic clause-iteration path (config-driven)."""
    current_status = current_result.status.value if current_result else "NOT_PAYABLE"

    for clause in rider_clauses:  # already sorted by priority desc from loader
        # Status guard: skip if this item's current status isn't in the rescue list
        if current_status not in clause.only_rescues_status:
            continue

        # Find the rider this clause belongs to
        rider = rider_by_id.get(clause.rider_id)
        if rider is None:
            continue

        matched = False

        # Category match (fast path)
        if category and category not in ("UNCLASSIFIED", None):
            matched = category in clause.target_categories
        elif clause.fallback_kw_set:
            # Keyword fallback for UNCLASSIFIED items
            matched = any(contains_phrase(desc_norm, normalize_text(kw)) for kw in clause.fallback_kw_set.keywords)

        if not matched:
            continue

        return _apply_rider_with_cap(
            item, current_result, rider, clause.reason_template, rider_remaining
        )

    return current_result


def _warn_and_skip_legacy(riders: list[Rider]) -> None:
    """Emit a warning when riders exist with boolean flags but no clause rows.

    This replaces the old silent fallback to _legacy_boolean_check.  The warning
    makes misconfigured insurers visible in logs immediately instead of silently
    applying hardcoded keyword lists that may not match the insurer's actual policy.

    Fix: run `python seeds/runner.py --insurer <CODE>` to re-seed clause rows.
    """
    flagged = [
        r.code for r in riders
        if any([
            r.covers_consumables, r.covers_opd, r.covers_maternity,
            r.covers_dental, r.covers_critical_illness,
        ])
    ]
    if flagged:
        logger.warning(
            "step5b: riders %s have boolean coverage flags but NO rider_coverage_clauses rows. "
            "Rider rescue skipped for this item — re-seed the insurer to fix. "
            "(Migration 020 asserts this never happens in production.)",
            flagged,
        )


def _legacy_boolean_check(
    item: BillItemInput,
    current_result: AnalyzedLineItem | None,
    riders: list[Rider],
    category: str | None,
    desc_norm: str,
    rider_remaining: dict | None,
) -> AnalyzedLineItem | None:
    """Original boolean-column check preserved for backward compatibility."""
    if category and category not in ("UNCLASSIFIED", None):
        is_consumable = category in CONSUMABLE_CATEGORIES
        is_opd = category in OPD_CATEGORIES
        is_maternity = category in MATERNITY_CATEGORIES
    else:
        is_consumable = any(contains_phrase(desc_norm, normalize_text(k)) for k in ["gloves", "syringe", "mask", "disposable", "consumable"])
        is_opd = any(contains_phrase(desc_norm, normalize_text(k)) for k in ["opd", "outpatient", "consultation"])
        is_maternity = any(contains_phrase(desc_norm, normalize_text(k)) for k in MATERNITY_KEYWORDS)

    if is_consumable and current_result and current_result.status != PayabilityStatus.PAYABLE:
        for rider in _ordered_riders(riders):
            if rider.covers_consumables:
                return _apply_rider_with_cap(
                    item, current_result, rider,
                    f"Rider '{rider.name}' covers consumables", rider_remaining,
                )

    if is_opd and current_result and current_result.status != PayabilityStatus.PAYABLE:
        for rider in _ordered_riders(riders):
            if rider.covers_opd:
                return _apply_rider_with_cap(
                    item, current_result, rider,
                    f"Rider '{rider.name}' covers OPD", rider_remaining,
                )

    if is_maternity and current_result and current_result.status != PayabilityStatus.PAYABLE:
        for rider in _ordered_riders(riders):
            if rider.covers_maternity:
                return _apply_rider_with_cap(
                    item, current_result, rider,
                    f"Rider '{rider.name}' covers maternity", rider_remaining,
                )

    return current_result
