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

from app.schemas import BillItemInput, ItemCategory
from app.services.gpt_service import gpt_client, settings as gpt_settings

logger = logging.getLogger(__name__)

# ─── Fixed category taxonomy ──────────────────────────────────────────────────
# These must stay in sync with the SYSTEM_PROMPT below and with the categories
# used by step1_universal.py / insurer_rules / diagnosis_overrides in the DB.

VALID_CATEGORIES = {cat.value for cat in ItemCategory}

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

Return ONLY the JSON object. No explanation."""


async def batch_categorize_items(
    items: list[BillItemInput],
    diagnosis: str | None,
    billing_mode: str,
) -> dict[str, str]:
    """
    Sends all bill item descriptions to GPT-4o in one call.
    Returns a dict: {description -> category_string}.

    On any failure, returns {} so all rule steps fall back to keyword matching.
    """
    if not items:
        return {}

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
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,  # Fully deterministic — this is classification, not generation
            max_tokens=800,
        )

        content = response.choices[0].message.content
        raw: dict = json.loads(content)

        # Sanitize: only keep known descriptions and valid categories
        result: dict[str, str] = {}
        for desc in descriptions:
            category = raw.get(desc)
            if isinstance(category, str) and category.upper() in VALID_CATEGORIES:
                result[desc] = category.upper()
            else:
                # GPT returned unknown category or missed this item — leave out so
                # downstream steps use keyword fallback
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
