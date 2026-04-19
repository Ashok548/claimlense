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
from app.rules._shared import contains_phrase, is_unclassified, keyword_matches_item, normalize_text


async def load_diagnosis_synonyms(db: AsyncSession) -> dict[str, set[str]]:
    """Load diagnosis synonym groups from DB.

    Returns a dict matching the shape of DIAGNOSIS_SYNONYMS below.
    Falls back to an empty dict when the table does not exist (pre-018 migration),
    in which case _diagnosis_matches() uses the compile-time constant instead.
    """
    try:
        from app.models import DiagnosisSynonymGroup
        result = await db.execute(select(DiagnosisSynonymGroup))
        rows = result.scalars().all()
        return {row.base_term: set(row.synonyms) for row in rows}
    except Exception:
        return {}


# Lightweight synonym expansion as an immediate improvement over pure substring.
# This can later be replaced by DB-driven concept mapping (ICD/SNOMED).
DIAGNOSIS_SYNONYMS: dict[str, set[str]] = {
    "myocardial infarction": {"mi", "heart attack", "acute coronary syndrome", "acs"},
    "coronary artery disease": {"cad", "ischemic heart disease", "ihd"},
    "knee replacement": {"tkr", "total knee replacement", "total knee arthroplasty", "tka"},
    "hip replacement": {"thr", "total hip replacement", "total hip arthroplasty", "tha"},
    "cataract": {"phaco", "phacoemulsification", "lens opacity"},
    "dialysis": {"hemodialysis", "haemodialysis", "hd"},
    "chemotherapy": {"chemo", "oncology infusion"},
    "accident": {"rta", "road traffic accident", "trauma"},
}


def _diagnosis_matches(
    diagnosis_norm: str,
    diagnosis_keyword: str,
    synonym_map: dict[str, set[str]] | None = None,
) -> bool:
    keyword_norm = normalize_text(diagnosis_keyword)
    if contains_phrase(diagnosis_norm, keyword_norm):
        return True

    # DB-loaded synonyms take precedence; fall back to compile-time constant.
    active_map = synonym_map if synonym_map is not None else DIAGNOSIS_SYNONYMS
    expanded = active_map.get(keyword_norm, set())
    for syn in expanded:
        syn_norm = normalize_text(syn)
        if contains_phrase(diagnosis_norm, syn_norm):
            return True
    return False


async def load_diagnosis_overrides(db: AsyncSession) -> list:
    """Load all diagnosis overrides once before the item loop."""
    result = await db.execute(select(DiagnosisOverride))
    return result.scalars().all()


def check_diagnosis_override(
    item: BillItemInput,
    diagnosis: str | None,
    overrides: list,
    item_category: str | None = None,
    synonym_map: dict[str, set[str]] | None = None,
) -> AnalyzedLineItem | None:
    """
    If the current diagnosis matches a stored override AND the item matches,
    return the override verdict. Returns None if no override found.

    item_category: pre-assigned category from Step 0. Used to filter overrides by
    item_category first for speed; keyword match is still the final confirmation.
    synonym_map: DB-loaded synonym groups from load_diagnosis_synonyms().
                 When None, falls back to the compile-time DIAGNOSIS_SYNONYMS constant.
    """
    if not diagnosis:
        return None

    diagnosis_norm = normalize_text(diagnosis)
    desc_norm = normalize_text(item.description)

    for override in overrides:
        # Check diagnosis against normalized keyword + synonym expansion.
        if not _diagnosis_matches(diagnosis_norm, override.diagnosis_keyword, synonym_map):
            continue

        # If we have a pre-assigned category and the override has a category, use it
        # to skip overrides that clearly don't apply (fast path)
        if (
            not is_unclassified(item_category)
            and override.item_category
            and override.item_category != item_category
        ):
            continue

        # Check item keyword match with token-safe normalization.
        item_matched, matched_kw = keyword_matches_item(desc_norm, override.item_keywords)
        if not item_matched:
            continue

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
            category=item_category or override.item_category,
            rule_matched=f"DIAGNOSIS:{override.diagnosis_keyword}:{matched_kw}",
            confidence=0.90,
            confidence_basis=ConfidenceBasis.DIAGNOSIS_OVERRIDE,
            decision_source="DIAGNOSIS_OVERRIDE",
            policy_basis_id=f"DIAGNOSIS:{override.id}",
            policy_basis_text=override.reason,
            payable_pct_source="deterministic" if override.override_status == "PARTIALLY_PAYABLE" else None,
            rejection_reason=None
            if override.override_status == "PAYABLE"
            else override.reason,
            recovery_action=override.notes,
            llm_used=False,
        )

    return None
