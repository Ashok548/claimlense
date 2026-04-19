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
from app.rules._shared import contains_phrase, is_unclassified, normalize_text


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
      - If category is known (non-UNCLASSIFIED, non-None) and matches
        rule.item_category → direct match, no keyword scan needed.
      - Keyword loop is used only when item_category is absent/UNCLASSIFIED
        so we never skip a valid rule for an unclassified item.

    Keyword matching uses token-safe phrase matching (via _shared.contains_phrase)
    to prevent false positives like "cap" matching inside "capsule".
    """
    desc_norm = normalize_text(item.description)

    for rule in rules:
        # If rule is plan-specific, skip if we're not on that plan
        if rule.plan_codes and plan_code and plan_code not in rule.plan_codes:
            continue

        # Primary: category equality match (fast path — no keyword scan)
        # Guards against None AND "UNCLASSIFIED" so both absent states are handled.
        category_matched = (
            not is_unclassified(item_category)
            and rule.item_category
            and item_category == rule.item_category
        )

        if category_matched:
            payable = _compute_payable(item.billed_amount, rule)
            effective_status = _effective_status(rule)
            return AnalyzedLineItem(
                id=uuid.uuid4(),
                description=item.description,
                billed_amount=item.billed_amount,
                payable_amount=payable,
                status=effective_status,
                category=rule.item_category,
                rule_matched=f"INSURER:{rule.item_category}:CATEGORY_MATCH",
                confidence=0.88,
                confidence_basis=ConfidenceBasis.INSURER_RULE,
                rejection_reason=rule.reason if effective_status != PayabilityStatus.PAYABLE else None,
                recovery_action=_recovery(rule),
                llm_used=False,
            )

        # Fallback: token-safe keyword phrase match (only for unclassified items)
        if is_unclassified(item_category):
            for keyword in rule.keywords:
                if contains_phrase(desc_norm, normalize_text(keyword)):
                    payable = _compute_payable(item.billed_amount, rule)
                    effective_status = _effective_status(rule)
                    return AnalyzedLineItem(
                        id=uuid.uuid4(),
                        description=item.description,
                        billed_amount=item.billed_amount,
                        payable_amount=payable,
                        status=effective_status,
                        category=rule.item_category,
                        rule_matched=f"INSURER:{rule.item_category}:{keyword}",
                        confidence=0.85,
                        confidence_basis=ConfidenceBasis.INSURER_RULE,
                        rejection_reason=rule.reason if effective_status != PayabilityStatus.PAYABLE else None,
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
    # PARTIALLY_PAYABLE with no pct in the DB is a data quality issue.
    # Return the full billed amount so it appears as VERIFY_WITH_TPA, not silently zeroed.
    # The caller in check_insurer_rules must downgrade the status when pct is missing.
    return billed


def _effective_status(rule: InsurerRule) -> PayabilityStatus:
    """Returns the correct status, downgrading PARTIALLY_PAYABLE to VERIFY_WITH_TPA
    when the payable_pct is missing — avoids silently returning 0 or full billed."""
    if rule.verdict == "PARTIALLY_PAYABLE" and not rule.payable_pct:
        return PayabilityStatus.VERIFY_WITH_TPA
    return PayabilityStatus(rule.verdict)


def _recovery(rule: InsurerRule) -> str | None:
    if rule.verdict == "PAYABLE":
        return None
    if rule.verdict == "PARTIALLY_PAYABLE" and rule.payable_pct:
        return (
            f"Your insurer covers {rule.payable_pct}% of this charge. "
            f"The remaining {100 - rule.payable_pct}% is payable by you."
        )
    return "Check your policy document or contact your TPA for clarification."
