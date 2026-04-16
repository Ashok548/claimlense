"""
Step 5b: Rider and Plan Coverage Overrides.
This step evaluates if the current plan or any selected rider provides extended coverage
that rescues an item previously marked as NOT_PAYABLE (e.g. Consumables or OPD).
"""

from app.models import Plan, Rider
from app.schemas import AnalyzedLineItem, BillItemInput, PayabilityStatus, ConfidenceBasis
import uuid

# Categories that can be rescued
CONSUMABLE_CATEGORIES = ["CONSUMABLE", "CONSUMABLE_OVERRIDE", "CONSUMABLE_SUBLIMIT"]
OPD_CATEGORIES = ["OPD", "CONSULTATION", "EXTERNAL_PHARMACY"]
MATERNITY_CATEGORIES = ["MATERNITY", "DELIVERY"]

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
        "rejection_reason": None,
        "recovery_action": None,
    })


def check_rider_and_plan_coverage(
    item: BillItemInput, 
    current_result: AnalyzedLineItem | None, 
    plan: Plan, 
    riders: list[Rider],
    item_category: str | None = None,
) -> AnalyzedLineItem | None:
    """Override payability based on active plan inclusions or rider coverage."""

    category = item_category or (current_result.category if current_result else None)

    # Derive flags from the authoritative category (Step 0) first;
    # keyword heuristics are only the last-resort fallback for UNCLASSIFIED items.
    desc_lower = item.description.lower()
    if category and category not in ("UNCLASSIFIED", None):
        is_consumable = category in CONSUMABLE_CATEGORIES
        is_opd = category in OPD_CATEGORIES
        is_maternity = category in MATERNITY_CATEGORIES
    else:
        # Keyword fallback (same as before) for truly unclassified items
        is_consumable = category in CONSUMABLE_CATEGORIES or any(k in desc_lower for k in ["gloves", "syringe", "mask", "disposable", "consumable"])
        is_opd = category in OPD_CATEGORIES or any(k in desc_lower for k in ["opd", "outpatient", "consultation"])
        is_maternity = category in MATERNITY_CATEGORIES or any(k in desc_lower for k in ["maternity", "delivery", "c-section", "caesarean"])

    # 1. Check Consumables
    if is_consumable and current_result and current_result.status != PayabilityStatus.PAYABLE:
        if plan.consumables_covered:
            return _mark_payable(item, current_result, f"Plan '{plan.name}' covers consumables", ConfidenceBasis.INSURER_RULE)
        for rider in riders:
            if rider.covers_consumables:
                return _mark_payable(item, current_result, f"Rider '{rider.name}' covers consumables", ConfidenceBasis.INSURER_RULE)

    # 2. Check OPD
    if is_opd and current_result and current_result.status != PayabilityStatus.PAYABLE:
        for rider in riders:
            if rider.covers_opd:
                return _mark_payable(item, current_result, f"Rider '{rider.name}' covers OPD", ConfidenceBasis.INSURER_RULE)

    # 3. Check Maternity
    if is_maternity and current_result and current_result.status != PayabilityStatus.PAYABLE:
        for rider in riders:
            if rider.covers_maternity:
                return _mark_payable(item, current_result, f"Rider '{rider.name}' covers maternity", ConfidenceBasis.INSURER_RULE)

    return current_result
