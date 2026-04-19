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

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import AnalyzedLineItem, BillItemInput, ConfidenceBasis, PayabilityStatus

# Compile-time fallback keyword lists used when room_rent_config table is empty.
ROOM_RENT_KEYWORDS = [
    "room rent", "room charge", "bed charge", "ward charge",
    "accommodation", "room & board", "room and board",
    "single room", "double room", "general ward", "ac room",
    "icu charges", "iccu", "hdu", "nicu", "picu",
]

# Subset of ROOM_RENT_KEYWORDS that are specifically ICU-type
ICU_KEYWORDS = {"icu", "iccu", "hdu", "nicu", "picu"}


async def load_room_rent_config(
    db: AsyncSession,
    insurer_id=None,
    plan_code: str | None = None,
):
    """Load the most-specific RoomRentConfig row for this insurer/plan.

    Priority order:
      1. Insurer + plan_code match
      2. Insurer match (no plan filter)
      3. Global default (insurer_id=NULL)

    Returns None if the table does not exist (pre-012 migration).
    """
    try:
        from app.models import RoomRentConfig
        stmt = (
            select(RoomRentConfig)
            .options(
                selectinload(RoomRentConfig.detection_keyword_set),
                selectinload(RoomRentConfig.icu_keyword_set),
            )
            .where(
                or_(
                    RoomRentConfig.insurer_id.is_(None),
                    RoomRentConfig.insurer_id == insurer_id,
                )
            )
            .order_by(RoomRentConfig.priority.desc())
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            return None

        # Pick the most-specific match when plan_code is provided
        if plan_code:
            plan_match = next(
                (r for r in rows if r.plan_codes and plan_code in r.plan_codes),
                None,
            )
            if plan_match:
                return plan_match

        # Insurer-level match (no plan filter)
        if insurer_id:
            insurer_match = next(
                (r for r in rows if r.insurer_id == insurer_id and not r.plan_codes),
                None,
            )
            if insurer_match:
                return insurer_match

        # Fall back to global default
        return next((r for r in rows if r.insurer_id is None), None)
    except Exception:
        return None


def is_room_rent_item(description: str, room_rent_cfg=None) -> bool:
    desc_lower = description.lower()
    keywords = (
        room_rent_cfg.detection_keyword_set.keywords
        if room_rent_cfg and room_rent_cfg.detection_keyword_set
        else ROOM_RENT_KEYWORDS
    )
    return any(kw in desc_lower for kw in keywords)


def is_icu_item(description: str, room_rent_cfg=None) -> bool:
    """True if the room rent item is an ICU/ICCU/HDU/NICU/PICU charge."""
    desc_lower = description.lower()
    keywords = (
        room_rent_cfg.icu_keyword_set.keywords
        if room_rent_cfg and room_rent_cfg.icu_keyword_set
        else ICU_KEYWORDS
    )
    return any(kw in desc_lower for kw in keywords)


def check_room_rent(
    item: BillItemInput,
    room_rent_limit: float | None,
    icu_days: int | None = None,
    general_ward_days: int | None = None,
    icu_room_rent_limit: float | None = None,
    room_rent_cfg=None,
) -> tuple["AnalyzedLineItem | None", float, bool]:
    """
    Returns:
        (AnalyzedLineItem, deduction_ratio, is_icu_line) — if this is a room rent item
        (None, 1.0, False) — if not a room rent item

    room_rent_cfg: RoomRentConfig ORM row loaded by the engine.
      When provided, keyword detection uses the DB-stored keyword sets.
      When None, falls back to hardcoded ROOM_RENT_KEYWORDS / ICU_KEYWORDS.
    """
    if not is_room_rent_item(item.description, room_rent_cfg):
        return None, 1.0, False

    icu_item = is_icu_item(item.description, room_rent_cfg)

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
