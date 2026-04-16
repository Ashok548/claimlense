"""
Step 1 — IRDAI Universal Exclusions
Queries the exclusion_rules table (applies_to_all=true).
Returns a match if any keyword in the rule's array appears in the item description.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExclusionRule
from app.schemas import AnalyzedLineItem, BillItemInput, ConfidenceBasis, PayabilityStatus


async def load_universal_exclusion_rules(db: AsyncSession) -> list:
    """Load all IRDAI universal exclusion rules once before the item loop."""
    result = await db.execute(
        select(ExclusionRule).where(ExclusionRule.applies_to_all == True)  # noqa: E712
    )
    return result.scalars().all()


# Categories that are never excluded by IRDAI universal rules — they are payable
# medical services/items regardless of how they appear in a description.
_NEVER_EXCLUDED_CATEGORIES = {"DIAGNOSTIC_TEST", "IMPLANT", "PROCEDURE", "ROOM_RENT", "DRUG"}


def check_universal_exclusions(
    item: BillItemInput,
    rules: list,
    item_category: str | None = None,
) -> AnalyzedLineItem | None:
    """
    Returns an AnalyzedLineItem if item matches an IRDAI universal exclusion.
    Returns None if no match — proceed to next step.

    item_category: pre-assigned category from Step 0 LLM batch classifier.
      - If the category is in _NEVER_EXCLUDED_CATEGORIES, skip all exclusion rules
        immediately (prevents false positives like 'blood tube' hitting CONSUMABLE).
      - If category matches a rule's category → high-confidence match without keyword.
      - If item_category is None or UNCLASSIFIED → fall back to keyword matching.
    """
    # Fast-exit: LLM confirmed this is a test/procedure/implant — never excluded
    if item_category and item_category in _NEVER_EXCLUDED_CATEGORIES:
        return None

    desc_lower = item.description.lower()

    for rule in rules:
        # Primary: category equality match (LLM-assigned category agrees with rule)
        if item_category and item_category == rule.category:
            return AnalyzedLineItem(
                id=_new_id(),
                description=item.description,
                billed_amount=item.billed_amount,
                payable_amount=0.0,
                status=PayabilityStatus.NOT_PAYABLE,
                category=rule.category,
                rule_matched=f"IRDAI:{rule.category}:CATEGORY_MATCH",
                confidence=0.97,  # Slightly higher — LLM + rule agree
                confidence_basis=ConfidenceBasis.IRDAI_RULE,
                rejection_reason=rule.rejection_reason,
                recovery_action=_recovery_action(rule.category),
                llm_used=False,
            )

        # Fallback: keyword substring match (used when item_category is None/UNCLASSIFIED)
        if not item_category or item_category == "UNCLASSIFIED":
            for keyword in rule.keywords:
                if keyword.lower() in desc_lower:
                    return AnalyzedLineItem(
                        id=_new_id(),
                        description=item.description,
                        billed_amount=item.billed_amount,
                        payable_amount=0.0,
                        status=PayabilityStatus.NOT_PAYABLE,
                        category=rule.category,
                        rule_matched=f"IRDAI:{rule.category}:{keyword}",
                        confidence=0.95,
                        confidence_basis=ConfidenceBasis.IRDAI_RULE,
                        rejection_reason=rule.rejection_reason,
                        recovery_action=_recovery_action(rule.category),
                        llm_used=False,
                    )

    return None


def _recovery_action(category: str) -> str:
    actions = {
        "CONSUMABLE": (
            "Ask the hospital billing desk to bundle consumable costs into the "
            "procedure/surgery package charges. Itemized consumables are excluded "
            "under IRDAI Circular IRDAI/HLT/REG/CIR/193/07/2020."
        ),
        "ADMIN": (
            "Administrative charges such as registration, file, and discharge fees "
            "are not claimable. Remove these from the insurance claim submission."
        ),
        "NON_MEDICAL": (
            "Personal comfort items (food, telephone, TV, laundry) are not covered. "
            "Pay these directly and do not include in the insurance claim."
        ),
        "EQUIPMENT_RENTAL": (
            "External equipment rental charges are excluded. If the equipment was "
            "medically essential (e.g., ICU ventilator), request the hospital to "
            "bill it as part of ICU/room charges."
        ),
        "COSMETIC": (
            "Cosmetic procedures are explicitly excluded under all Indian health "
            "insurance policies. This cannot be claimed."
        ),
        "ATTENDANT": (
            "Attendant/bystander charges are not covered. Remove from claim."
        ),
        "EXTERNAL_PHARMACY": (
            "Medicines purchased from outside the hospital pharmacy are not payable "
            "unless accompanied by a valid prescription and emergency justification."
        ),
    }
    return actions.get(
        category,
        "Remove this item from the insurance claim or consult your TPA.",
    )


import uuid as _uuid_module


def _new_id() -> _uuid_module.UUID:
    return _uuid_module.uuid4()
