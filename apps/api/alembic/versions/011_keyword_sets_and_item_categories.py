"""Migration 011 — keyword_sets and item_categories tables.

Creates two new config tables that replace hardcoded keyword lists and
category constants scattered across rule step files.

  keyword_sets    — named, versioned lists of detection keywords
  item_categories — canonical category registry; replaces _NEVER_EXCLUDED_CATEGORIES,
                    _recovery_action(), VALID_CATEGORIES, and the Step 0 SYSTEM_PROMPT
"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None

# ─── Keyword sets ─────────────────────────────────────────────────────────────

KEYWORD_SETS = [
    {
        "name": "ROOM_RENT_DETECTION",
        "is_system": True,
        "description": "Keywords that identify room/accommodation line items (step4).",
        "keywords": [
            "room rent", "room charge", "bed charge", "ward charge",
            "accommodation", "room & board", "room and board",
            "single room", "double room", "general ward", "ac room",
            "icu charges", "iccu", "hdu", "nicu", "picu",
        ],
    },
    {
        "name": "ICU_DETECTION",
        "is_system": True,
        "description": "Keywords that identify ICU/critical-care line items within room rent (step4).",
        "keywords": ["icu", "iccu", "hdu", "nicu", "picu"],
    },
    {
        "name": "CONSUMABLE_BILLING_MODE",
        "is_system": True,
        "description": "Consumable keywords for billing-mode rescue in package/mixed claims (step3 fallback).",
        "keywords": [
            "gloves", "mask", "syringe", "needle", "gauze", "bandage",
            "suture", "consumable", "disposable", "cotton", "catheter",
            "drape", "cannula", "iv tube", "drain tube", "ot kit", "surgical kit",
            "sterile pack", "dressing pack", "dressing",
        ],
    },
    {
        "name": "MATERNITY_DETECTION",
        "is_system": True,
        "description": "Keywords identifying maternity/obstetric billing items (step5b rider fallback).",
        "keywords": [
            "maternity", "delivery", "c-section", "caesarean", "lscs",
            "obstetric", "obstetrics", "antenatal", "ante natal",
            "postnatal", "post natal", "prenatal", "pre natal",
            "episiotomy", "neonatal", "newborn care", "new born care",
            "vacuum delivery", "forceps delivery",
            "labour charge", "labor charge", "labour room", "labor room",
            "normal delivery", "assisted delivery",
        ],
    },
    {
        "name": "OPD_DETECTION",
        "is_system": True,
        "description": "Keywords identifying OPD/outpatient items (step5b rider fallback).",
        "keywords": ["opd", "outpatient", "consultation"],
    },
    {
        "name": "CONSUMABLE_RIDER_DETECTION",
        "is_system": True,
        "description": "Short-form consumable keywords for rider rescue (step5b).",
        "keywords": ["gloves", "syringe", "mask", "disposable", "consumable"],
    },
]

# ─── Item categories ──────────────────────────────────────────────────────────

ITEM_CATEGORIES = [
    # ── Core, never-excluded (payable medical services/items) ─────────────
    {
        "code": "DIAGNOSTIC_TEST",
        "display_name": "Diagnostic Test",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Laboratory tests, imaging, pathology, and any diagnostic investigations.",
        "llm_examples": ["CBC", "LFT", "MRI Brain", "CT abdomen", "ECG", "biopsy", "urine culture"],
        "recovery_template": None,
    },
    {
        "code": "DRUG",
        "display_name": "Drug / Medicine",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Medicines, IV fluids, injections, blood products dispensed by the hospital pharmacy.",
        "llm_examples": ["Ceftriaxone injection", "Paracetamol", "NS 500ml", "saline drip", "blood transfusion"],
        "recovery_template": None,
    },
    {
        "code": "IMPLANT",
        "display_name": "Implant / Prosthesis",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Surgical implants, prosthetics, and intraocular lenses.",
        "llm_examples": ["coronary stent", "knee prosthesis", "IOL", "pacemaker", "orthopedic plate"],
        "recovery_template": None,
    },
    {
        "code": "PROCEDURE",
        "display_name": "Procedure / Surgery",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Surgery charges, OT fees, anaesthesia, ICU monitoring, physiotherapy, dialysis.",
        "llm_examples": [
            "OT charges", "surgeon fee", "anaesthesia", "ICU monitoring",
            "dialysis", "chemotherapy", "physiotherapy",
        ],
        "recovery_template": None,
    },
    {
        "code": "ROOM_RENT",
        "display_name": "Room Rent / Accommodation",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Room, bed, ward, or accommodation charges including ICU.",
        "llm_examples": ["room rent", "bed charge", "ICU charges", "single room", "general ward"],
        "recovery_template": None,
    },
    # ── Exclusion categories ───────────────────────────────────────────────
    {
        "code": "CONSUMABLE",
        "display_name": "Consumable / Disposable",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Single-use disposable items billed separately from procedures.",
        "llm_examples": ["gloves", "syringes", "IV cannula", "bandage", "gauze", "OT kit", "urine bag"],
        "recovery_template": (
            "Ask the hospital billing desk to bundle consumable costs into the "
            "procedure/surgery package charges. Itemized consumables are excluded "
            "under IRDAI Circular IRDAI/HLT/REG/CIR/193/07/2020."
        ),
    },
    {
        "code": "ADMIN",
        "display_name": "Administrative Fee",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Registration, admission, discharge, file, and paperwork fees.",
        "llm_examples": ["registration fee", "admission charges", "discharge fee", "file charge", "documentation"],
        "recovery_template": (
            "Administrative charges such as registration, file, and discharge fees "
            "are not claimable. Remove these from the insurance claim submission."
        ),
    },
    {
        "code": "NON_MEDICAL",
        "display_name": "Non-Medical / Personal Comfort",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Food, beverages, personal comfort items, telephone, TV, laundry.",
        "llm_examples": ["meal charges", "diet food", "TV rental", "telephone", "laundry", "toiletries"],
        "recovery_template": (
            "Personal comfort items (food, telephone, TV, laundry) are not covered. "
            "Pay these directly and do not include in the insurance claim."
        ),
    },
    {
        "code": "ATTENDANT",
        "display_name": "Attendant / Bystander",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Attendant, bystander, companion, and private nurse charges.",
        "llm_examples": ["attendant charge", "bystander fee", "companion fee", "ayah charges"],
        "recovery_template": "Attendant/bystander charges are not covered. Remove from claim.",
    },
    {
        "code": "EQUIPMENT_RENTAL",
        "display_name": "Equipment Rental",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "External equipment hire billed separately from procedure or room charges.",
        "llm_examples": ["nebulizer rental", "CPAP hire", "monitor rental", "wheelchair rental", "BiPAP"],
        "recovery_template": (
            "External equipment rental charges are excluded. If the equipment was "
            "medically essential (e.g. ICU ventilator), request the hospital to "
            "bill it as part of ICU/room charges."
        ),
    },
    {
        "code": "EXTERNAL_PHARMACY",
        "display_name": "External Pharmacy",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Medicines purchased from outside the hospital pharmacy.",
        "llm_examples": ["outside pharmacy", "retail pharmacy bill", "medicine from outside"],
        "recovery_template": (
            "Medicines purchased from outside the hospital pharmacy are not payable "
            "unless accompanied by a valid prescription and emergency justification."
        ),
    },
    {
        "code": "COSMETIC",
        "display_name": "Cosmetic Procedure",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Cosmetic surgery, aesthetic procedures, anti-aging treatments.",
        "llm_examples": ["botox", "liposuction", "rhinoplasty cosmetic", "breast augmentation"],
        "recovery_template": (
            "Cosmetic procedures are explicitly excluded under all Indian health "
            "insurance policies. This cannot be claimed."
        ),
    },
    {
        "code": "UNCLASSIFIED",
        "display_name": "Unclassified",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Item that could not be assigned to a known category.",
        "llm_examples": [],
        "recovery_template": "Remove this item from the insurance claim or consult your TPA.",
    },
    # ── Insurer-custom categories (used in insurer_rules + step5) ─────────
    # Stored here so the Step 0 LLM prompt can include them and step5
    # category-equality matching works correctly.
    {
        "code": "MODERN_TREATMENT",
        "display_name": "Modern / Technology Treatment",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Robotic, laser, or tech-intensive procedures that some insurers cap.",
        "llm_examples": ["robotic surgery", "laser surgery", "robot assisted"],
        "recovery_template": "Check your policy for sub-limits on modern/technology treatments.",
    },
    {
        "code": "CATARACT_PACKAGE",
        "display_name": "Cataract Surgery Package",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Cataract (phacoemulsification) surgery package including IOL implant.",
        "llm_examples": ["cataract surgery", "phacoemulsification", "IOL implant", "intraocular lens"],
        "recovery_template": None,
    },
    {
        "code": "CONSUMABLE_OVERRIDE",
        "display_name": "Consumable (Insurer Override)",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Consumable covered by insurer-specific plan (overrides IRDAI exclusion).",
        "llm_examples": ["gloves", "syringe", "disposable", "surgical gloves"],
        "recovery_template": None,
    },
    {
        "code": "CONSUMABLE_SUBLIMIT",
        "display_name": "Consumable (Sub-limit Applies)",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Consumable allowed with an aggregate sub-limit cap.",
        "llm_examples": ["consumables", "disposables"],
        "recovery_template": "Consumables are covered up to a sub-limit. Verify remaining cap with TPA.",
    },
    {
        "code": "PHARMACY_COPAY",
        "display_name": "Pharmacy (Co-pay Applicable)",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Pharmacy charges subject to a co-payment under specific plans.",
        "llm_examples": ["pharmacy", "medicines", "drugs", "medication"],
        "recovery_template": "A co-payment applies on pharmacy/medicine charges under this plan.",
    },
    {
        "code": "ROOM_UPGRADE_COPAY",
        "display_name": "Room Upgrade (Co-pay)",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Room category upgrade charge subject to a co-payment.",
        "llm_examples": ["room upgrade", "room category upgrade", "higher room"],
        "recovery_template": "A co-payment applies on room upgrade charges under this plan.",
    },
    {
        "code": "SURGEON_CONSULTATION",
        "display_name": "Surgeon / Specialist Consultation",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Surgeon or specialist consultation fees, sometimes capped by insurers.",
        "llm_examples": ["surgeon consultation", "specialist visit", "consultant charges"],
        "recovery_template": "Surgeon consultation fees may be capped under your plan.",
    },
]


def upgrade() -> None:
    # ── Create keyword_sets ───────────────────────────────────────────────
    op.create_table(
        "keyword_sets",
        sa.Column(
            "id",
            PGUUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("keywords", ARRAY(sa.Text()), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_keyword_sets_name", "keyword_sets", ["name"])

    # ── Create item_categories ────────────────────────────────────────────
    op.create_table(
        "item_categories",
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("never_excluded", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_payable_by_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("llm_examples", ARRAY(sa.Text()), nullable=True),
        sa.Column("recovery_template", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("code"),
    )

    conn = op.get_bind()

    # ── Seed keyword_sets ─────────────────────────────────────────────────
    for ks in KEYWORD_SETS:
        conn.execute(
            sa.text(
                "INSERT INTO keyword_sets (id, name, keywords, description, is_system) "
                "VALUES (gen_random_uuid(), :name, :keywords, :description, :is_system)"
            ),
            {
                "name": ks["name"],
                "keywords": ks["keywords"],
                "description": ks.get("description"),
                "is_system": ks["is_system"],
            },
        )

    # ── Seed item_categories ──────────────────────────────────────────────
    for cat in ITEM_CATEGORIES:
        conn.execute(
            sa.text(
                "INSERT INTO item_categories "
                "(code, display_name, description, never_excluded, is_payable_by_default, "
                "llm_examples, recovery_template) "
                "VALUES (:code, :display_name, :description, :never_excluded, "
                ":is_payable_by_default, :llm_examples, :recovery_template)"
            ),
            {
                "code": cat["code"],
                "display_name": cat["display_name"],
                "description": cat.get("description"),
                "never_excluded": cat["never_excluded"],
                "is_payable_by_default": cat["is_payable_by_default"],
                "llm_examples": cat.get("llm_examples") or [],
                "recovery_template": cat.get("recovery_template"),
            },
        )


def downgrade() -> None:
    op.drop_index("ix_keyword_sets_name", table_name="keyword_sets")
    op.drop_table("item_categories")
    op.drop_table("keyword_sets")
