"""
Step 2 — Diagnosis-Aware Overrides
Runs BEFORE exclusion rules are applied on per-item basis.
Prevents false rejections (e.g., knee implants, stents, cataract consumables).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiagnosisOverride
from app.schemas import AnalyzedLineItem, BillItemInput, ConfidenceBasis, PayabilityStatus


async def load_diagnosis_overrides(db: AsyncSession) -> list:
    """Load all diagnosis overrides once before the item loop."""
    result = await db.execute(select(DiagnosisOverride))
    return result.scalars().all()


def check_diagnosis_override(
    item: BillItemInput,
    diagnosis: str | None,
    overrides: list,
    item_category: str | None = None,
) -> AnalyzedLineItem | None:
    """
    If the current diagnosis matches a stored override AND the item matches,
    return the override verdict. Returns None if no override found.

    item_category: pre-assigned category from Step 0. Used to filter overrides by
    item_category first for speed; keyword match is still the final confirmation.
    """
    if not diagnosis:
        return None

    diagnosis_lower = diagnosis.lower()
    desc_lower = item.description.lower()

    for override in overrides:
        # Check if diagnosis matches this override's keyword
        if override.diagnosis_keyword.lower() not in diagnosis_lower:
            continue

        # If we have a pre-assigned category and the override has a category, use it
        # to skip overrides that clearly don't apply (fast path)
        if (
            item_category
            and item_category not in ("UNCLASSIFIED", None)
            and override.item_category
            and override.item_category != item_category
        ):
            continue

        # Check if item description matches any item keyword
        for kw in override.item_keywords:
            if kw.lower() in desc_lower:
                payable = (
                    item.billed_amount
                    if override.override_status == "PAYABLE"
                    else (
                        item.billed_amount * (override.payable_pct / 100)
                        if override.payable_pct
                        else 0.0
                    )
                )
                return AnalyzedLineItem(
                    id=uuid.uuid4(),
                    description=item.description,
                    billed_amount=item.billed_amount,
                    payable_amount=round(payable, 2),
                    status=PayabilityStatus(override.override_status),
                    category="DIAGNOSIS_OVERRIDE",
                    rule_matched=f"DIAGNOSIS:{override.diagnosis_keyword}:{kw}",
                    confidence=0.90,
                    confidence_basis=ConfidenceBasis.DIAGNOSIS_OVERRIDE,
                    rejection_reason=None
                    if override.override_status == "PAYABLE"
                    else override.reason,
                    recovery_action=override.notes,
                    llm_used=False,
                )

    return None
