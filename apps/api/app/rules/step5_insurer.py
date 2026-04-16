"""
Step 5 — Insurer-Specific Rules
Queries insurer_rules table for the given insurer.
These can OVERRIDE universal exclusions (e.g., HDFC Optima Secure covers consumables).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InsurerRule
from app.schemas import AnalyzedLineItem, BillItemInput, ConfidenceBasis, PayabilityStatus


async def load_insurer_rules(insurer_id: uuid.UUID, db: AsyncSession) -> list:
    """Load all insurer-specific rules once before the item loop."""
    result = await db.execute(
        select(InsurerRule).where(InsurerRule.insurer_id == insurer_id)
    )
    return result.scalars().all()


def check_insurer_rules(
    item: BillItemInput,
    rules: list,
    plan_code: str | None,
    item_category: str | None = None,
) -> AnalyzedLineItem | None:
    """
    Returns an AnalyzedLineItem if item matches an insurer-specific rule.
    Returns None if no match.

    item_category: pre-assigned category from Step 0.
      - If category matches rule.item_category → match without keyword loop.
      - Keyword loop is fallback for UNCLASSIFIED or missing category.
    """
    desc_lower = item.description.lower()

    for rule in rules:
        # If rule is plan-specific, skip if we're not on that plan
        if rule.plan_codes and plan_code and plan_code not in rule.plan_codes:
            continue

        # Primary: category equality match
        category_matched = (
            item_category
            and item_category not in ("UNCLASSIFIED",)
            and rule.item_category
            and item_category == rule.item_category
        )

        if category_matched:
            payable = _compute_payable(item.billed_amount, rule)
            return AnalyzedLineItem(
                id=uuid.uuid4(),
                description=item.description,
                billed_amount=item.billed_amount,
                payable_amount=payable,
                status=PayabilityStatus(rule.verdict),
                category=rule.item_category,
                rule_matched=f"INSURER:{rule.item_category}:CATEGORY_MATCH",
                confidence=0.88,
                confidence_basis=ConfidenceBasis.INSURER_RULE,
                rejection_reason=rule.reason if rule.verdict != "PAYABLE" else None,
                recovery_action=_recovery(rule),
                llm_used=False,
            )

        # Fallback: keyword substring match
        if not item_category or item_category == "UNCLASSIFIED":
            for keyword in rule.keywords:
                if keyword.lower() in desc_lower:
                    payable = _compute_payable(item.billed_amount, rule)
                    return AnalyzedLineItem(
                        id=uuid.uuid4(),
                        description=item.description,
                        billed_amount=item.billed_amount,
                        payable_amount=payable,
                        status=PayabilityStatus(rule.verdict),
                        category=rule.item_category,
                        rule_matched=f"INSURER:{rule.item_category}:{keyword}",
                        confidence=0.85,
                        confidence_basis=ConfidenceBasis.INSURER_RULE,
                        rejection_reason=rule.reason
                        if rule.verdict != "PAYABLE"
                        else None,
                        recovery_action=_recovery(rule),
                        llm_used=False,
                    )

    return None


def _compute_payable(billed: float, rule: InsurerRule) -> float:
    if rule.verdict == "PAYABLE":
        return billed
    if rule.verdict == "NOT_PAYABLE":
        return 0.0
    if rule.verdict == "PARTIALLY_PAYABLE" and rule.payable_pct:
        return round(billed * (rule.payable_pct / 100), 2)
    return 0.0


def _recovery(rule: InsurerRule) -> str | None:
    if rule.verdict == "PAYABLE":
        return None
    if rule.verdict == "PARTIALLY_PAYABLE" and rule.payable_pct:
        return (
            f"Your insurer covers {rule.payable_pct}% of this charge. "
            f"The remaining {100 - rule.payable_pct}% is payable by you."
        )
    return "Check your policy document or contact your TPA for clarification."
