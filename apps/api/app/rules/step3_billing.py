"""
Step 3 — Billing Mode Context
Package-billed items bypass consumable exclusion rules.
The same item (e.g., surgical gloves) can be PAYABLE in a package
and NOT_PAYABLE when billed as a separate line item (itemized).
"""

import uuid

from app.schemas import AnalyzedLineItem, BillItemInput, BillingMode, ConfidenceBasis, PayabilityStatus

# Keywords that are consumables when itemized, but payable when in a package.
# Intentionally specific compound keywords — bare "tube" and "kit" are excluded
# because they also appear in diagnostic item names ("blood collection tube",
# "culture kit") and create false-positive matches when Step 0 category is missing.
CONSUMABLE_KEYWORDS = [
    "gloves", "mask", "syringe", "needle", "gauze", "bandage",
    "suture", "consumable", "disposable", "cotton", "catheter",
    "drape", "cannula", "iv tube", "drain tube", "ot kit", "surgical kit",
    "sterile pack", "dressing pack", "dressing",
]


def check_billing_mode(
    item: BillItemInput,
    billing_mode: BillingMode,
    item_category: str | None = None,
) -> AnalyzedLineItem | None:
    """
    If billing_mode is 'package', consumable items are absorbed into the
    package price and should be marked PAYABLE.
    If billing_mode is 'mixed', consumable items are ambiguous — it is unclear
    whether they fall in the package component or the itemized component, so
    they are flagged VERIFY_WITH_TPA instead of being auto-rescued.
    Returns None if not applicable (itemized or not a consumable).

    item_category: pre-assigned category from Step 0.
      - If DIAGNOSTIC_TEST / IMPLANT / PROCEDURE / DRUG → return None immediately;
        these are never "consumable in a package" — they flow to the verdict steps.
      - If CONSUMABLE → match without keyword loop when in package/mixed mode.
      - If None/UNCLASSIFIED → fall back to keyword loop.
    """
    if billing_mode == BillingMode.MIXED:
        return _check_mixed_mode(item, item_category)

    if billing_mode != BillingMode.PACKAGE:
        return None

    # Items that are never consumables — skip step 3 entirely
    _non_consumable = {"DIAGNOSTIC_TEST", "IMPLANT", "PROCEDURE", "ROOM_RENT", "DRUG"}
    if item_category and item_category in _non_consumable:
        return None

    # Category confirmed as CONSUMABLE by Step 0
    if item_category == "CONSUMABLE":
        return AnalyzedLineItem(
            id=uuid.uuid4(),
            description=item.description,
            billed_amount=item.billed_amount,
            payable_amount=item.billed_amount,
            status=PayabilityStatus.PAYABLE,
            category="CONSUMABLE_IN_PACKAGE",
            rule_matched="BILLING_MODE:PACKAGE:CATEGORY_MATCH",
            confidence=0.90,
            confidence_basis=ConfidenceBasis.BILLING_MODE,
            rejection_reason=None,
            recovery_action=(
                "Item is part of a package — consumable costs are absorbed "
                "into the package billing and are payable."
            ),
            llm_used=False,
        )

    # Fallback: keyword match for UNCLASSIFIED or missing category
    desc_lower = item.description.lower()
    matched_kw = next(
        (kw for kw in CONSUMABLE_KEYWORDS if kw in desc_lower), None
    )

    if matched_kw:
        return AnalyzedLineItem(
            id=uuid.uuid4(),
            description=item.description,
            billed_amount=item.billed_amount,
            payable_amount=item.billed_amount,
            status=PayabilityStatus.PAYABLE,
            category="CONSUMABLE_IN_PACKAGE",
            rule_matched=f"BILLING_MODE:PACKAGE:{matched_kw}",
            confidence=0.88,
            confidence_basis=ConfidenceBasis.BILLING_MODE,
            rejection_reason=None,
            recovery_action=(
                "Item is part of a package — consumable costs are absorbed "
                "into the package billing and are payable."
            ),
            llm_used=False,
        )

    return None


def _check_mixed_mode(
    item: BillItemInput,
    item_category: str | None,
) -> AnalyzedLineItem | None:
    """
    For MIXED billing, consumable items cannot be auto-rescued like in PACKAGE mode
    because there is no line-level metadata indicating whether a specific item is part
    of the package component or the itemized component.
    Return VERIFY_WITH_TPA so the TPA adjudicates on a per-item basis.
    Non-consumables (DIAGNOSTIC_TEST, IMPLANT, PROCEDURE, DRUG) are passed through
    to the downstream verdict steps unchanged.
    """
    _non_consumable = {"DIAGNOSTIC_TEST", "IMPLANT", "PROCEDURE", "ROOM_RENT", "DRUG"}
    if item_category and item_category in _non_consumable:
        return None

    is_consumable = item_category == "CONSUMABLE"
    if not is_consumable:
        desc_lower = item.description.lower()
        is_consumable = any(kw in desc_lower for kw in CONSUMABLE_KEYWORDS)

    if not is_consumable:
        return None

    return AnalyzedLineItem(
        id=uuid.uuid4(),
        description=item.description,
        billed_amount=item.billed_amount,
        payable_amount=item.billed_amount,
        status=PayabilityStatus.VERIFY_WITH_TPA,
        category="CONSUMABLE",
        rule_matched="BILLING_MODE:MIXED:CONSUMABLE_UNRESOLVED",
        confidence=0.65,
        confidence_basis=ConfidenceBasis.BILLING_MODE,
        rejection_reason=(
            "Bill uses mixed (package + itemized) mode. It cannot be confirmed "
            "whether this consumable is bundled into the package component or "
            "billed separately. IRDAI excludes separately itemized consumables."
        ),
        recovery_action=(
            "Ask the hospital billing desk whether this item is included in the "
            "package portion of the bill. If yes, request it be removed from the "
            "itemized section before submitting the insurance claim."
        ),
        llm_used=False,
    )
