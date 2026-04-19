"""
Step 7 — Sub-Limit Aggregate Cap.

After individual item verdicts are finalised (steps 1-6) this pass checks
per-claim aggregate sub-limits:

    • DB-driven: sublimit_rules table (insurer + item_category + optional plan_codes)
    • Plan-level fallback: plans.consumables_sublimit (CONSUMABLE category only)

For each matched sub-limit rule the step:
1. Collects all PAYABLE / PARTIALLY_PAYABLE items in that category (sorted
   deterministically: highest billed_amount first, then description A-Z).
2. Allocates from the cap in that order until the cap is exhausted.
3. Items beyond the cap are reduced to their remaining allowed amount with
   status PARTIALLY_PAYABLE and a clear rejection_reason; items fully beyond
   cap become NOT_PAYABLE.

Items with status VERIFY_WITH_TPA or NOT_PAYABLE are not touched — their
payable_amount is already ≤ billed or zero.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Plan, SubLimitRule
from app.schemas import AnalyzedLineItem, ConfidenceBasis, PayabilityStatus

_PAYABLE_STATUSES = (PayabilityStatus.PAYABLE, PayabilityStatus.PARTIALLY_PAYABLE)


async def load_sublimit_rules(
    insurer_id: uuid.UUID,
    db: AsyncSession,
) -> list[SubLimitRule]:
    """Return all sub-limit rules for *insurer_id* (unfiltered by plan here)."""
    result = await db.execute(
        select(SubLimitRule).where(SubLimitRule.insurer_id == insurer_id)
    )
    return list(result.scalars().all())


def apply_sublimit_cap(
    items: list[AnalyzedLineItem],
    sublimit_rules: list[SubLimitRule],
    plan_code: str | None,
    plan: Plan,
) -> list[AnalyzedLineItem]:
    """
    Apply sub-limit aggregate caps.

    Returns a *new* list (items are immutable Pydantic models; model_copy used).
    Order of items is preserved.
    """
    if not items:
        return items

    # Build effective rule set: deduplicate by category, take the *smallest* cap
    # when multiple rules match (most restrictive applies).
    effective_caps: dict[str, float] = {}

    for rule in sublimit_rules:
        # Filter by plan_codes if the rule restricts to specific plans
        if rule.plan_codes is not None and plan_code is not None:
            if plan_code not in rule.plan_codes:
                continue
        category = rule.item_category.upper()
        cap = float(rule.max_amount)
        if category not in effective_caps or cap < effective_caps[category]:
            effective_caps[category] = cap

    # Plan-level consumables_sublimit is a secondary source (lowest wins)
    if plan.consumables_sublimit:
        plan_consumables_cap = float(plan.consumables_sublimit)
        current = effective_caps.get("CONSUMABLE")
        if current is None or plan_consumables_cap < current:
            effective_caps["CONSUMABLE"] = plan_consumables_cap

    if not effective_caps:
        return items

    # Process each capped category
    # Build index: id -> position in list so we can reassemble in original order
    id_to_index: dict[uuid.UUID] = {item.id: i for i, item in enumerate(items)}
    updated: dict[uuid.UUID, AnalyzedLineItem] = {}

    for category, cap in effective_caps.items():
        # Collect eligible items (payable, matching category)
        eligible = [
            item for item in items
            if item.status in _PAYABLE_STATUSES
            and (item.category or "").upper() == category
        ]
        if not eligible:
            continue

        # Deterministic order: highest payable_amount first, then description A-Z
        eligible_sorted = sorted(
            eligible,
            key=lambda x: (-x.payable_amount, x.description.lower()),
        )

        remaining = cap
        for item in eligible_sorted:
            if remaining <= 0:
                # Fully exhausted — entire item is beyond cap
                updated[item.id] = item.model_copy(
                    update={
                        "payable_amount": 0.0,
                        "status": PayabilityStatus.NOT_PAYABLE,
                        "rejection_reason": (
                            f"Sub-limit cap of ₹{cap:,.0f} for {category} items "
                            "exceeded; this item is beyond the aggregate limit."
                        ),
                        "confidence_basis": ConfidenceBasis.INSURER_RULE,
                        "rule_matched": (item.rule_matched or "") + f"|SUBLIMIT_{category}",
                    }
                )
            elif item.payable_amount <= remaining:
                # Fully within cap — no change needed
                remaining -= item.payable_amount
            else:
                # Partially within cap
                allowed = round(remaining, 2)
                updated[item.id] = item.model_copy(
                    update={
                        "payable_amount": allowed,
                        "status": PayabilityStatus.PARTIALLY_PAYABLE,
                        "rejection_reason": (
                            f"Sub-limit cap of ₹{cap:,.0f} for {category} items; "
                            f"only ₹{allowed:,.2f} of ₹{item.payable_amount:,.2f} remains within limit."
                        ),
                        "confidence_basis": ConfidenceBasis.INSURER_RULE,
                        "rule_matched": (item.rule_matched or "") + f"|SUBLIMIT_{category}",
                    }
                )
                remaining = 0.0

    if not updated:
        return items

    # Rebuild list preserving original order
    result = list(items)
    for item_id, new_item in updated.items():
        idx = id_to_index[item_id]
        result[idx] = new_item
    return result
