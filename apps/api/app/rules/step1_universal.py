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


# Compile-time fallback for when item_categories table is empty (pre-011 migration).
_NEVER_EXCLUDED_CATEGORIES = {"DIAGNOSTIC_TEST", "IMPLANT", "PROCEDURE", "ROOM_RENT", "DRUG"}


def _is_never_excluded(category: str, item_categories: dict) -> bool:
    """Return True if this category should never be rejected by IRDAI rules.

    Uses the DB-loaded item_categories dict when available; falls back to the
    hardcoded _NEVER_EXCLUDED_CATEGORIES set for backward compatibility.
    """
    if item_categories:
        cat_row = item_categories.get(category)
        return bool(cat_row and cat_row.never_excluded)
    return category in _NEVER_EXCLUDED_CATEGORIES


def check_universal_exclusions(
    item: BillItemInput,
    rules: list,
    item_category: str | None = None,
    item_categories: dict | None = None,
) -> AnalyzedLineItem | None:
    """
    Returns an AnalyzedLineItem if item matches an IRDAI universal exclusion.
    Returns None if no match — proceed to next step.

    item_category:   pre-assigned category from Step 0 LLM batch classifier.
    item_categories: dict {code -> ItemCategoryModel} loaded by the engine.
                     When provided, never_excluded flags and recovery_template text
                     come from the DB instead of hardcoded constants.
    """
    item_categories = item_categories or {}
    # Fast-exit: LLM confirmed this is a test/procedure/implant — never excluded
    if item_category and _is_never_excluded(item_category, item_categories):
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
                recovery_action=_recovery_action(rule.category, item_categories),
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
                        recovery_action=_recovery_action(rule.category, item_categories),
                        llm_used=False,
                    )

    return None


def _recovery_action(category: str, item_categories: dict | None = None) -> str:
    """Return recovery action text for a rejected category.

    Uses DB row's recovery_template when available; falls back to hardcoded text.
    """
    if item_categories:
        cat_row = item_categories.get(category)
        if cat_row and cat_row.recovery_template:
            return cat_row.recovery_template

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
