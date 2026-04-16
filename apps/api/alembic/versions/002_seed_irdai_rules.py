"""
Migration 002 — Seed IRDAI Universal Exclusion Rules.
Source: IRDAI Circular IRDAI/HLT/REG/CIR/193/07/2020
These apply to ALL insurers regardless of policy.
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

EXCLUSION_RULES = [
    {
        "category": "CONSUMABLE",
        "keywords": [
            "gloves", "surgical gloves", "mask", "face mask", "syringe", "needle",
            "gauze", "bandage", "suture", "sutures", "cotton", "catheter",
            "drape", "surgical drape", "cannula", "iv cannula", "tube", "iv tube",
            "consumable", "consumables", "disposable", "disposables",
            "dressing", "wound dressing", "kit", "ot kit", "pre-op kit",
            "prep kit", "phaco consumable", "ot pack", "sterile pack",
            "urine bag", "colostomy bag", "stoma bag",
        ],
        "rejection_reason": (
            "Standard consumables and disposable items are excluded under IRDAI Circular "
            "IRDAI/HLT/REG/CIR/193/07/2020. These items when billed separately as "
            "line items are not payable by any insurer in India."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "ADMIN",
        "keywords": [
            "registration charge", "registration fee", "admission fee",
            "file charge", "file opening", "case file", "discharge fee",
            "discharge summary charge", "administrative charge", "admin charge",
            "gst charge", "gst on services", "service tax", "processing fee",
            "documentation fee", "medical record fee", "id card charge",
        ],
        "rejection_reason": (
            "Administrative, documentation, and non-medical overhead charges are "
            "not payable by insurance under IRDAI guidelines."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "NON_MEDICAL",
        "keywords": [
            "food charge", "food charges", "meal charge", "diet charge",
            "beverage", "tea charge", "coffee", "tiffin",
            "telephone", "phone charge", "mobile charge",
            "tv charges", "television", "cable tv",
            "laundry", "laundry charge", "washing charge",
            "soap", "toiletries", "personal items",
            "attendant food", "visitor meals",
        ],
        "rejection_reason": (
            "Personal comfort items including food, beverages, telephone, TV, "
            "laundry, and toiletries are not covered under health insurance."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "ATTENDANT",
        "keywords": [
            "attendant charge", "attendant charges", "attendant fee",
            "bystander charge", "companion charge", "escort charge",
            "nursing attendant", "private attendant",
            "ayah charge", "ward attendant fee",
        ],
        "rejection_reason": (
            "Attendant, bystander, and companion charges are excluded from "
            "health insurance coverage."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "EQUIPMENT_RENTAL",
        "keywords": [
            "nebulizer rental", "nebulizer hire", "nebulizer charge",
            "cpap rental", "cpap hire", "bipap rental", "bipap hire",
            "monitor hire", "monitor rental", "equipment hire",
            "equipment rental", "machine hire", "machine rental",
            "wheelchair rental", "walker rental",
            "laser machine charge", "laser machine usage",
            "laser machine hire", "laser equipment charge",
        ],
        "rejection_reason": (
            "External equipment rental and machine usage charges billed as separate "
            "line items are not payable. Equipment use should be embedded in the "
            "procedure package or ICU charges."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "COSMETIC",
        "keywords": [
            "cosmetic", "cosmetic surgery", "botox", "botulinum",
            "liposuction", "liposuction charge", "aesthetic",
            "anti-aging", "anti aging", "filler", "dermal filler",
            "hair transplant", "rhinoplasty cosmetic",
            "breast augmentation", "breast implant cosmetic",
        ],
        "rejection_reason": (
            "Cosmetic and aesthetic procedures are explicitly excluded under all "
            "Indian health insurance policies irrespective of insurer."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "EXTERNAL_PHARMACY",
        "keywords": [
            "outside pharmacy", "external pharmacy", "pharmacy bill",
            "pharmacy invoice", "medicine from outside",
            "drugs from retail", "retail pharmacy",
        ],
        "rejection_reason": (
            "Medicines purchased from outside the hospital pharmacy are not payable "
            "unless emergency justification is provided with a valid prescription."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    for rule in EXCLUSION_RULES:
        conn.execute(
            sa.text(
                """
                INSERT INTO exclusion_rules (id, category, keywords, rejection_reason, source_circular, applies_to_all)
                VALUES (:id, :category, :keywords, :rejection_reason, :source_circular, true)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "category": rule["category"],
                "keywords": rule["keywords"],
                "rejection_reason": rule["rejection_reason"],
                "source_circular": rule.get("source_circular"),
            },
        )


def downgrade() -> None:
    op.execute("DELETE FROM exclusion_rules WHERE applies_to_all = true")
