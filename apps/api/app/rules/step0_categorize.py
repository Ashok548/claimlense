"""
Step 0 — LLM Batch Item Categorizer

Runs BEFORE any rule step. Sends all bill item descriptions in a single GPT-4o
call and returns a category for each one. The category is then threaded through
every rule step so rules match by category equality, not substring keyword guessing.

Crucially: this step only classifies — it never decides payability.
The verdict (PAYABLE / NOT_PAYABLE / etc.) remains solely with the rule engine.

On any failure (GPT unavailable, parse error, timeout) returns an empty dict.
All downstream steps fall back to their existing keyword logic gracefully.
"""

import json
import logging
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import BillItemInput
from app.services.gpt_service import gpt_client, settings as gpt_settings

if TYPE_CHECKING:
    from app.models import ItemCategory as ItemCategoryModel

logger = logging.getLogger(__name__)

# ─── Compile-time fallback taxonomy ──────────────────────────────────────────
# VALID_CATEGORIES is used ONLY when the item_categories DB table is empty
# (e.g. before migration 011 runs).  It is intentionally NOT derived from the
# ItemCategory enum so new DB-only categories (added after initial deploy) flow
# through without requiring an enum change.
# When item_categories rows ARE loaded, the engine builds valid_cats from those
# codes and this constant is never consulted.

VALID_CATEGORIES: frozenset[str] = frozenset({
    "CONSUMABLE", "DIAGNOSTIC_TEST", "DRUG", "IMPLANT", "PROCEDURE",
    "ROOM_RENT", "ADMIN", "NON_MEDICAL", "ATTENDANT", "EQUIPMENT_RENTAL",
    "EXTERNAL_PHARMACY", "COSMETIC", "MODERN_TREATMENT", "CATARACT_PACKAGE",
    "CONSUMABLE_OVERRIDE", "CONSUMABLE_SUBLIMIT", "PHARMACY_COPAY",
    "ROOM_UPGRADE_COPAY", "SURGEON_CONSULTATION", "OPD", "CONSULTATION",
    "MATERNITY", "DELIVERY", "CRITICAL_ILLNESS", "DENTAL", "UNCLASSIFIED",
})

SYSTEM_PROMPT = """You are a medical billing classification expert specializing in Indian hospital bills.

Your ONLY job is to assign a category to each hospital bill line item. 
You must NOT decide whether items are payable or not. Only classify.

Return a JSON object where keys are the exact item descriptions provided and values are categories.

Use EXACTLY one of these categories (no others):
- CONSUMABLE: gloves, syringes, IV cannula, needles used for IV/injection, bandages, gauze, drapes, dressings, OT kits, sterile packs, urine bags, stoma bags, catheters used as disposables
- DIAGNOSTIC_TEST: blood tests (CBC, LFT, RFT, KFT), imaging (CT, MRI, X-ray, ultrasound, PET scan), cardiology tests (ECG, echo, Doppler, angiography), pathology (biopsy, FNAC, culture, Pap smear), urine/stool tests, endoscopy, colonoscopy, pulmonary function tests, nerve conduction, audiometry, any item with "test", "profile", "panel", "study", "scan", "culture", "sensitivity" in the name
- DRUG: medicines, tablets, capsules, syrups, IV fluids (saline, dextrose, Ringer's), antibiotics, injections (named drugs), blood products
- IMPLANT: stent, coronary stent, knee/hip prosthesis, IOL (intraocular lens), pacemaker, orthopedic screws/plates, cochlear implant, breast implant (reconstructive)
- PROCEDURE: surgery charges, OT charges, operation theatre, anaesthesia, surgeon fee, doctor fee, procedure charges, physiotherapy, radiation, chemotherapy, dialysis, ICU monitoring fees
- ROOM_RENT: room charge, room rent, bed charge, ward charge, accommodation, ICU charges, NICU, PICU, HDU
- ADMIN: registration fee, admission fee, discharge fee, file charge, documentation fee, administrative charge, GST on services, processing fee, bed booking fee
- NON_MEDICAL: food, meals, diet, beverages, telephone, TV, cable, laundry, washing, soap, toiletries, personal items, visitor meals
- ATTENDANT: attendant charge, bystander charge, companion fee, private nurse attendant, ayah charges
- EQUIPMENT_RENTAL: nebulizer rental/hire, CPAP/BiPAP rental, monitor hire, equipment rental, wheelchair rental, walker rental, laser machine charges billed separately
- EXTERNAL_PHARMACY: outside pharmacy, retail pharmacy bill, medicine from outside, pharmacy invoice not from hospital
- COSMETIC: cosmetic surgery, botox, liposuction, aesthetic procedure, anti-aging, rhinoplasty for cosmetic reasons, breast augmentation
- UNCLASSIFIED: only if genuinely cannot determine from the description

Critical distinctions:
- "Blood collection tube" or "vacutainer" — this is part of a DIAGNOSTIC_TEST, NOT a CONSUMABLE
- "Culture kit" or "test kit" or "diagnostic kit" — DIAGNOSTIC_TEST, NOT a CONSUMABLE
- "Biopsy needle" or "FNAC needle" — DIAGNOSTIC_TEST (the needle is integral to the procedure), NOT a CONSUMABLE
- "IV cannula" or "injection needle" or "IV needle" — CONSUMABLE (used for drug delivery, not a test)
- "Phaco machine charge" for cataract — PROCEDURE, NOT EQUIPMENT_RENTAL
- "OT kit" or "surgical kit" — CONSUMABLE
- "Suture" — CONSUMABLE
- Named drugs like "Ceftriaxone injection", "Paracetamol", "NS 500ml" — DRUG, NOT CONSUMABLE
- "ECG electrodes" or "electrode pads" — CONSUMABLE (disposable pads, NOT a DIAGNOSTIC_TEST)
- "Oxygen cylinder outside hospital" — EQUIPMENT_RENTAL (outside-use is excluded)
- "Sugar free tablets" — NON_MEDICAL (comfort item, not prescribed medication)
- "Blood grouping of donors" — ADMIN (donor-side process, not patient diagnostic test)
- "Ambulance equipment" — EQUIPMENT_RENTAL (equipment separately billed, not the ambulance ride)
- "Vasofix" or "Abbocath" or cannula brand names — CONSUMABLE (IV access devices)
- "Delivery kit" or "Ortho kit" or "Recovery kit" with no details — CONSUMABLE

Return ONLY the JSON object. No explanation."""


# ─── DB-backed loaders and dynamic prompt builder ────────────────────────────


async def load_item_categories(db: AsyncSession) -> list:
    """Load all item_category rows. Returns list[ItemCategoryModel].

    Returns an empty list if the table does not yet exist (pre-011 migration),
    which is safe — callers fall back to VALID_CATEGORIES and SYSTEM_PROMPT.
    """
    try:
        from app.models import ItemCategory as ItemCategoryModel  # local to avoid circular
        result = await db.execute(select(ItemCategoryModel).order_by(ItemCategoryModel.code))
        return result.scalars().all()
    except Exception:
        return []


# Template variables: {CATEGORY_LIST}, {CATEGORY_EXAMPLES}
_PROMPT_TEMPLATE = """\
You are a medical billing classification expert specializing in Indian hospital bills.

Your ONLY job is to assign a category to each hospital bill line item.
You must NOT decide whether items are payable or not. Only classify.

Return a JSON object where keys are the exact item descriptions provided and values are categories.

Use EXACTLY one of these categories (no others):
{CATEGORY_LIST}

Examples per category:
{CATEGORY_EXAMPLES}

Critical distinctions:
- "Blood collection tube" / "vacutainer" — DIAGNOSTIC_TEST, NOT a CONSUMABLE
- "Culture kit" / "test kit" / "diagnostic kit" — DIAGNOSTIC_TEST, NOT a CONSUMABLE
- "Biopsy needle" / "FNAC needle" — DIAGNOSTIC_TEST (needle is integral to the procedure)
- "IV cannula" / "injection needle" — CONSUMABLE (used for drug delivery, not a test)
- "Phaco machine charge" for cataract — PROCEDURE, NOT EQUIPMENT_RENTAL
- "OT kit" / "surgical kit" — CONSUMABLE
- Named drugs — DRUG, NOT CONSUMABLE
- "ECG electrodes" or "electrode pads" — CONSUMABLE (disposable pads, NOT a DIAGNOSTIC_TEST)
- "Oxygen cylinder outside hospital" — EQUIPMENT_RENTAL (outside-use is excluded)
- "Sugar free tablets" — NON_MEDICAL (comfort item, not prescribed medication)
- "Blood grouping of donors" — ADMIN (donor-side process, not patient diagnostic test)
- "Ambulance equipment" — EQUIPMENT_RENTAL (equipment separately billed, not the ambulance ride)
- "Vasofix" or "Abbocath" or cannula brand names — CONSUMABLE (IV access devices)
- "Delivery kit" or "Ortho kit" or "Recovery kit" with no details — CONSUMABLE

Return ONLY the JSON object. No explanation."""


def build_step0_prompt(categories: list) -> str:
    """Build the Step 0 system prompt dynamically from ItemCategory DB rows.

    If categories is empty, returns the hardcoded SYSTEM_PROMPT fallback.
    """
    if not categories:
        return SYSTEM_PROMPT

    codes_lines = []
    example_lines = []
    for cat in categories:
        if cat.code in {
            "UNCLASSIFIED",
            "CONSUMABLE_OVERRIDE",
            "CONSUMABLE_SUBLIMIT",
            "PHARMACY_COPAY",
            "ROOM_UPGRADE_COPAY"
        }:
            continue
        # Allow expanding more examples
        examples = ", ".join((cat.llm_examples or [])[:12]) or "—"
        codes_lines.append(f"- {cat.code}: {cat.description or cat.display_name}")
        example_lines.append(f"- {cat.code}: {examples}")

    # UNCLASSIFIED always last
    codes_lines.append("- UNCLASSIFIED: only if genuinely cannot determine from the description")
    example_lines.append("- UNCLASSIFIED: incomprehensible or truly ambiguous items")

    return _PROMPT_TEMPLATE.format(
        CATEGORY_LIST="\n".join(codes_lines),
        CATEGORY_EXAMPLES="\n".join(example_lines),
    )


async def batch_categorize_items(
    items: list[BillItemInput],
    diagnosis: str | None,
    billing_mode: str,
    categories: list | None = None,
) -> dict[str, str]:
    """
    Sends all bill item descriptions to GPT-4o in one call.
    Returns a dict: {description -> category_string}.

    categories — list of ItemCategory ORM rows loaded by the engine before the
                 item loop.  When provided the prompt is built dynamically from
                 the DB so new categories are picked up without code changes.
                 When None/empty the hardcoded SYSTEM_PROMPT fallback is used.

    On any failure, returns {} so all rule steps fall back to keyword matching.
    """
    if not items:
        return {}

    # Determine which category codes are valid for sanitization
    valid_cats: set[str] = (
        {cat.code for cat in categories} if categories else VALID_CATEGORIES
    )

    prompt = build_step0_prompt(categories) if categories else SYSTEM_PROMPT

    descriptions = [item.description for item in items]

    user_message = json.dumps(
        {
            "items": descriptions,
            "diagnosis_context": diagnosis or "Not specified",
            "billing_mode": billing_mode,
        },
        ensure_ascii=False,
    )

    try:
        response = await gpt_client.chat.completions.create(
            model=gpt_settings.openai_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,  # Fully deterministic — this is classification, not generation
            max_tokens=800,
        )

        content = response.choices[0].message.content
        raw: dict = json.loads(content)

        # Map common LLM hallucinations/near-misses back to valid categories
        CATEGORY_ALIASES = {
            "PHARMACY": "EXTERNAL_PHARMACY",
            "DRUGS": "DRUG",
            "MEDICINES": "DRUG",
            "MEDICINE": "DRUG",
            "CONSUMABLES": "CONSUMABLE",
            "DIAGNOSTIC": "DIAGNOSTIC_TEST",
            "DIAGNOSTICS": "DIAGNOSTIC_TEST",
            "TEST": "DIAGNOSTIC_TEST",
            "ROOM": "ROOM_RENT",
            "IMPLANTS": "IMPLANT",
            "PROCEDURES": "PROCEDURE",
            "SURGERY": "PROCEDURE",
            "ADMINISTRATIVE": "ADMIN",
            "EQUIPMENT": "EQUIPMENT_RENTAL",
        }

        # Sanitize: only keep known descriptions and valid categories
        result: dict[str, str] = {}
        for desc in descriptions:
            category = raw.get(desc)
            if isinstance(category, str):
                cat_upper = category.upper()
                # Apply alias map if it exists
                cat_upper = CATEGORY_ALIASES.get(cat_upper, cat_upper)

                if cat_upper in valid_cats:
                    result[desc] = cat_upper
                    continue

            # GPT returned unknown category or missed this item
            if category:
                logger.warning(
                    "step0: GPT returned unknown category %r for item %r — ignoring",
                    category, desc,
                )

        logger.info(
            "step0: categorized %d/%d items via LLM",
            len(result), len(descriptions),
        )
        return result

    except Exception as exc:
        logger.warning("step0: batch categorization failed (%s) — falling back to keywords", exc)
        return {}
