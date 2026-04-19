"""
Step 3 — Billing Mode Context
Package-billed items bypass consumable exclusion rules.
The same item (e.g., surgical gloves) can be PAYABLE in a package
and NOT_PAYABLE when billed as a separate line item (itemized).
"""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import AnalyzedLineItem, BillItemInput, BillingMode, ConfidenceBasis, PayabilityStatus
from app.rules._shared import contains_phrase, normalize_text

# Compile-time fallback keyword list used when billing_mode_rules table is empty.
# Mirrors the CONSUMABLE_BILLING_MODE keyword_set seeded in migration 011.
CONSUMABLE_KEYWORDS = [
    "gloves", "mask", "syringe", "needle", "gauze", "bandage",
    "suture", "consumable", "disposable", "cotton", "catheter",
    "drape", "cannula", "iv tube", "drain tube", "ot kit", "surgical kit",
    "sterile pack", "dressing pack", "dressing",
]

# These categories flow straight through step3 regardless of billing mode.
_NON_CONSUMABLE_CATEGORIES = {"DIAGNOSTIC_TEST", "IMPLANT", "PROCEDURE", "ROOM_RENT", "DRUG"}


async def load_billing_mode_rules(
    db: AsyncSession,
    insurer_id=None,
    plan_code: str | None = None,
) -> list:
    """Load BillingModeRule rows relevant to this insurer/plan combination.

    Returns global rules (insurer_id=NULL) PLUS insurer-specific rules ordered
    by priority descending.  Returns [] if the table does not exist yet.
    """
    try:
        from app.models import BillingModeRule
        stmt = (
            select(BillingModeRule)
            .options(selectinload(BillingModeRule.fallback_kw_set))
            .where(
                or_(
                    BillingModeRule.insurer_id.is_(None),
                    BillingModeRule.insurer_id == insurer_id,
                )
            )
            .order_by(BillingModeRule.priority.desc())
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()
        # Filter by plan_code when the rule has plan_codes set
        if plan_code:
            rows = [
                r for r in rows
                if not r.plan_codes or plan_code in r.plan_codes
            ]
        return rows
    except Exception:
        return []


def check_billing_mode(
    item: BillItemInput,
    billing_mode: BillingMode,
    billing_mode_rules: list | None = None,
    item_category: str | None = None,
) -> AnalyzedLineItem | None:
    """
    Returns an AnalyzedLineItem when the billing mode affects payability.
    Returns None if not applicable (itemized) or no rule matched.

    billing_mode_rules: list of BillingModeRule ORM rows loaded by the engine.
      When None/empty the original hardcoded logic is used as fallback.
    item_category: pre-assigned category from Step 0.
    """
    # Itemized billing: step 3 is not applicable (IRDAI exclusion handled by step 1)
    if billing_mode == BillingMode.ITEMIZED:
        return None

    if billing_mode_rules:
        # Compute effective bypass set from DB: highest-priority row with
        # bypass_categories set non-null wins (insurer-specific row overrides global).
        effective_bypass: set[str] = _NON_CONSUMABLE_CATEGORIES
        for rule in billing_mode_rules:  # already ordered by priority desc
            bp = getattr(rule, "bypass_categories", None)
            if bp:
                effective_bypass = set(bp)
                break
        if item_category and item_category in effective_bypass:
            return None
        return _check_with_rules(item, billing_mode, billing_mode_rules, item_category)

    # ── Legacy hardcoded fallback (no rules loaded) ──────────────────────────
    if item_category and item_category in _NON_CONSUMABLE_CATEGORIES:
        return None

    if billing_mode == BillingMode.MIXED:
        return _check_mixed_mode(item, item_category)

    # PACKAGE mode
    if item_category == "CONSUMABLE":
        return _build_result(
            item, "CONSUMABLE",
            PayabilityStatus.PAYABLE, item.billed_amount,
            "BILLING_MODE:PACKAGE:CATEGORY_MATCH", 0.90,
            reason=None,
            recovery=(
                "Item is part of a package — consumable costs are absorbed "
                "into the package billing and are payable."
            ),
        )

    desc_norm = normalize_text(item.description)
    matched_kw = next((kw for kw in CONSUMABLE_KEYWORDS if contains_phrase(desc_norm, normalize_text(kw))), None)
    if matched_kw:
        return _build_result(
            item, "CONSUMABLE_IN_PACKAGE",
            PayabilityStatus.PAYABLE, item.billed_amount,
            f"BILLING_MODE:PACKAGE:{matched_kw}", 0.88,
            reason=None,
            recovery=(
                "Item is part of a package — consumable costs are absorbed "
                "into the package billing and are payable."
            ),
        )
    return None


def _check_with_rules(
    item: BillItemInput,
    billing_mode: BillingMode,
    billing_mode_rules: list,
    item_category: str | None,
) -> AnalyzedLineItem | None:
    """Generic rule-table path: iterate rules in priority order."""
    desc_norm = normalize_text(item.description)
    mode_value = billing_mode.value

    for rule in billing_mode_rules:
        if rule.billing_mode != mode_value:
            continue

        matched_key: str | None = None

        # Category match (fast path — LLM assigned the same category as the rule)
        if item_category and item_category not in ("UNCLASSIFIED", None):
            if item_category == rule.item_category:
                matched_key = f"BILLING:{rule.item_category}:CATEGORY"

        # Keyword fallback for UNCLASSIFIED items
        if matched_key is None and rule.fallback_kw_set:
            if not item_category or item_category == "UNCLASSIFIED":
                hit = next(
                    (kw for kw in rule.fallback_kw_set.keywords if contains_phrase(desc_norm, normalize_text(kw))),
                    None,
                )
                if hit:
                    matched_key = f"BILLING:{rule.item_category}:{hit}"

        if matched_key is None:
            continue

        payable = (
            float(rule.payable_pct) / 100 * item.billed_amount
            if rule.payable_pct is not None
            else item.billed_amount
        )
        verdict_enum = PayabilityStatus(rule.verdict)
        confidence = 0.90 if item_category and item_category != "UNCLASSIFIED" else 0.88

        return _build_result(
            item, rule.item_category, verdict_enum, payable,
            matched_key, confidence,
            reason=rule.reason if verdict_enum != PayabilityStatus.PAYABLE else None,
            recovery=rule.recovery,
        )

    return None


def _build_result(
    item: BillItemInput,
    category: str,
    status: PayabilityStatus,
    payable_amount: float,
    rule_matched: str,
    confidence: float,
    reason: str | None,
    recovery: str | None,
) -> AnalyzedLineItem:
    return AnalyzedLineItem(
        id=uuid.uuid4(),
        description=item.description,
        billed_amount=item.billed_amount,
        payable_amount=payable_amount,
        status=status,
        category=category,
        rule_matched=rule_matched,
        confidence=confidence,
        confidence_basis=ConfidenceBasis.BILLING_MODE,
        rejection_reason=reason,
        recovery_action=recovery,
        llm_used=False,
    )


def _check_mixed_mode(
    item: BillItemInput,
    item_category: str | None,
) -> AnalyzedLineItem | None:
    """
    Legacy fallback for MIXED billing mode.
    For MIXED billing, consumable items cannot be auto-rescued like in PACKAGE mode.
    """
    is_consumable = item_category == "CONSUMABLE"
    if not is_consumable:
        desc_norm = normalize_text(item.description)
        is_consumable = any(contains_phrase(desc_norm, normalize_text(kw)) for kw in CONSUMABLE_KEYWORDS)

    if not is_consumable:
        return None

    return _build_result(
        item, "CONSUMABLE",
        PayabilityStatus.VERIFY_WITH_TPA, item.billed_amount,
        "BILLING_MODE:MIXED:CONSUMABLE_UNRESOLVED", 0.65,
        reason=(
            "Bill uses mixed (package + itemized) mode. It cannot be confirmed "
            "whether this consumable is bundled into the package component or "
            "billed separately. IRDAI excludes separately itemized consumables."
        ),
        recovery=(
            "Ask the hospital billing desk whether this item is included in the "
            "package portion of the bill. If yes, request it be removed from the "
            "itemized section before submitting the insurance claim."
        ),
    )
