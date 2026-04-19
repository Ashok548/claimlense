"""
Step 4 — Room Rent Cap + Proportional Deduction

Critical industry rule that most apps implement incorrectly:
When room rent billed exceeds the policy cap, TWO things happen:
  1. The room rent line item is capped to the policy limit (PARTIALLY_PAYABLE)
  2. ALL other payable line items are ALSO proportionally reduced by the ratio:
       deduction_ratio = room_rent_limit / billed_room_rent

This step:
  - Identifies room rent line items
  - Returns the capped room result
  - Stores the deduction_ratio so engine.py can apply it globally
"""

import uuid

from app.schemas import AnalyzedLineItem, BillItemInput, ConfidenceBasis, PayabilityStatus

ROOM_RENT_KEYWORDS = [
    "room rent", "room charge", "bed charge", "ward charge",
    "accommodation", "room & board", "room and board",
    "single room", "double room", "general ward", "ac room",
    "icu charges", "iccu", "hdu", "nicu", "picu",
]

# Subset of ROOM_RENT_KEYWORDS that are specifically ICU-type
ICU_KEYWORDS = {"icu", "iccu", "hdu", "nicu", "picu"}


def is_room_rent_item(description: str) -> bool:
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in ROOM_RENT_KEYWORDS)


def is_icu_item(description: str) -> bool:
    """True if the room rent item is an ICU/ICCU/HDU/NICU/PICU charge."""
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in ICU_KEYWORDS)


def check_room_rent(
    item: BillItemInput,
    room_rent_limit: float | None,
    icu_days: int | None = None,
    general_ward_days: int | None = None,
    icu_room_rent_limit: float | None = None,
) -> tuple[AnalyzedLineItem | None, float, bool]:
    """
    Returns:
        (AnalyzedLineItem, deduction_ratio, is_icu_line) — if this is a room rent item
        (None, 1.0, False) — if not a room rent item

    deduction_ratio: used by engine.py to proportionally reduce other items.
    is_icu_line: True when this item is an ICU charge, so engine.py can track
                 separate ICU vs ward deduction ratios.

    ICU items: use icu_room_rent_limit when set, else fall back to room_rent_limit.
    Ward items: always use room_rent_limit.
    """
    if not is_room_rent_item(item.description):
        return None, 1.0, False

    icu_item = is_icu_item(item.description)

    # Resolve the effective per-day cap for this line item type
    effective_limit: float | None
    if icu_item and icu_room_rent_limit:
        effective_limit = icu_room_rent_limit
    else:
        effective_limit = room_rent_limit

    # If no limit applies, it's fully payable
    if not effective_limit:
        return AnalyzedLineItem(
            id=uuid.uuid4(),
            description=item.description,
            billed_amount=item.billed_amount,
            payable_amount=item.billed_amount,
            status=PayabilityStatus.PAYABLE,
            category="ROOM_RENT",
            rule_matched="ROOM_RENT:NO_LIMIT",
            confidence=0.99,
            confidence_basis=ConfidenceBasis.CALCULATION,
            rejection_reason=None,
            recovery_action=None,
            llm_used=False,
        ), 1.0, icu_item

    days_for_item: int | None = icu_days if icu_item else general_ward_days
    item_type_label = "ICU/ICCU" if icu_item else "ward"

    if not days_for_item or days_for_item <= 0:
        hint = (
            f"Enter the number of days you stayed in the {item_type_label} so we can "
            f"verify whether your per-day room rent exceeds the policy sub-limit."
        )
        return AnalyzedLineItem(
            id=uuid.uuid4(),
            description=item.description,
            billed_amount=item.billed_amount,
            payable_amount=item.billed_amount,
            status=PayabilityStatus.VERIFY_WITH_TPA,
            category="ROOM_RENT",
            rule_matched="ROOM_RENT:DAYS_UNKNOWN",
            confidence=0.60,
            confidence_basis=ConfidenceBasis.CALCULATION,
            rejection_reason=(
                f"{item_type_label.capitalize()} room charge of ₹{item.billed_amount:,.0f} cannot be verified "
                f"against the per-day limit of ₹{effective_limit:,.0f}/day because the number of "
                f"{item_type_label} days was not provided."
            ),
            recovery_action=hint,
            llm_used=False,
        ), 1.0, icu_item

    per_day_billed = item.billed_amount / days_for_item

    if per_day_billed <= effective_limit:
        return AnalyzedLineItem(
            id=uuid.uuid4(),
            description=item.description,
            billed_amount=item.billed_amount,
            payable_amount=item.billed_amount,
            status=PayabilityStatus.PAYABLE,
            category="ROOM_RENT",
            rule_matched="ROOM_RENT:WITHIN_LIMIT",
            confidence=0.99,
            confidence_basis=ConfidenceBasis.CALCULATION,
            rejection_reason=None,
            recovery_action=None,
            llm_used=False,
        ), 1.0, icu_item

    # Per-day rate EXCEEDS cap
    total_payable = effective_limit * days_for_item
    deduction_ratio = effective_limit / per_day_billed
    days_info = f" for {days_for_item} {item_type_label} days"

    return AnalyzedLineItem(
        id=uuid.uuid4(),
        description=item.description,
        billed_amount=item.billed_amount,
        payable_amount=round(total_payable, 2),
        status=PayabilityStatus.PARTIALLY_PAYABLE,
        category="ROOM_RENT_EXCESS",
        rule_matched=f"ROOM_RENT:EXCEEDS_LIMIT:{effective_limit}",
        confidence=0.99,
        confidence_basis=ConfidenceBasis.CALCULATION,
        rejection_reason=(
            f"Room rent of ₹{per_day_billed:,.0f}/day (₹{item.billed_amount:,.0f}{days_info}) "
            f"exceeds your policy sub-limit of ₹{effective_limit:,.0f}/day. "
            f"Additionally, all other claim items will be proportionally reduced "
            f"by {round((1 - deduction_ratio) * 100, 1)}% as per insurer policy."
        ),
        recovery_action=(
            f"Before discharge, request the hospital to downgrade your room to "
            f"the category within ₹{effective_limit:,.0f}/day. "
            f"This will also prevent proportional deduction on your entire bill."
        ),
        llm_used=False,
    ), deduction_ratio, icu_item



def apply_proportional_deduction(
    item: AnalyzedLineItem,
    deduction_ratio: float,
) -> AnalyzedLineItem:
    """
    Apply proportional deduction to a payable/partially-payable item.
    Called by engine.py after all items are processed if room rent exceeded cap.
    """
    if deduction_ratio >= 1.0:
        return item
    if item.status in (PayabilityStatus.NOT_PAYABLE, PayabilityStatus.VERIFY_WITH_TPA):
        return item  # NOT_PAYABLE is already zero; VERIFY items show full billed amount to TPA

    reduced_payable = round(item.payable_amount * deduction_ratio, 2)
    reduction_pct = round((1 - deduction_ratio) * 100, 1)

    return item.model_copy(
        update={
            "payable_amount": reduced_payable,
            "status": PayabilityStatus.PARTIALLY_PAYABLE,
            "rejection_reason": (
                (item.rejection_reason or "")
                + f" [Room rent proportional deduction: -{reduction_pct}%]"
            ).strip(),
            "rule_matched": (item.rule_matched or "") + "|PROPORTIONAL_DEDUCTION",
        }
    )
