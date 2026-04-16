"""
Migration 004 — Seed insurer-specific rules.
These OVERRIDE IRDAI universal exclusions for specific insurers/plans.
"""

import uuid
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None

# Rules: (insurer_code, item_category, keywords, verdict, payable_pct, reason, plan_codes)
INSURER_RULES = [
    # ── STAR HEALTH ─────────────────────────────────────────────────────────
    {
        "insurer_code": "STAR_HEALTH",
        "item_category": "MODERN_TREATMENT",
        "keywords": ["robotic surgery", "robotic", "robot assisted", "laser surgery", "laser treatment"],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 50.0,
        "reason": (
            "Star Health caps modern treatments (robotic/laser surgery) at 50% of actual cost "
            "under standard plans unless specifically covered."
        ),
        "plan_codes": None,  # applies to all Star plans
    },
    {
        "insurer_code": "STAR_HEALTH",
        "item_category": "CATARACT_PACKAGE",
        "keywords": ["cataract surgery", "phacoemulsification", "iol implant", "intraocular lens"],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 100.0,
        "reason": "Cataract surgery is covered as a package under Star Health. Request hospital to bill as package.",
        "plan_codes": None,
    },

    # ── HDFC ERGO ───────────────────────────────────────────────────────────
    {
        "insurer_code": "HDFC_ERGO",
        "item_category": "CONSUMABLE_OVERRIDE",
        "keywords": [
            "gloves", "surgical gloves", "mask", "syringe", "needle", "gauze",
            "bandage", "suture", "consumable", "disposable", "cannula",
        ],
        "verdict": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Under Optima Secure plan, consumables and disposables are fully covered — "
            "this overrides the standard IRDAI exclusion."
        ),
        "plan_codes": ["OPTIMA_SECURE"],
    },

    # ── ICICI LOMBARD ────────────────────────────────────────────────────────
    {
        "insurer_code": "ICICI_LOMBARD",
        "item_category": "CONSUMABLE_SUBLIMIT",
        "keywords": ["consumable", "consumables", "disposable", "disposables"],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": None,  # Subject to ₹5000 sub-limit — handled by special logic
        "reason": "ICICI Lombard iHealth plan allows consumables up to ₹5,000 per hospitalization.",
        "plan_codes": ["IHEALTH"],
    },

    # ── BAJAJ ALLIANZ ────────────────────────────────────────────────────────
    {
        "insurer_code": "BAJAJ_ALLIANZ",
        "item_category": "PHARMACY_COPAY",
        "keywords": ["pharmacy", "medicines", "drugs", "medication"],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 70.0,
        "reason": "Bajaj Allianz Health Guard applies 30% co-payment on pharmacy/medicine bills.",
        "plan_codes": ["HEALTH_GUARD"],
    },

    # ── NIVA BUPA ────────────────────────────────────────────────────────────
    {
        "insurer_code": "NIVA_BUPA",
        "item_category": "CONSUMABLE_OVERRIDE",
        "keywords": [
            "gloves", "surgical gloves", "mask", "syringe", "needle", "gauze",
            "bandage", "suture", "consumable", "consumables", "disposable",
        ],
        "verdict": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Niva Bupa ReAssure 2.0 plan fully covers consumables — "
            "overrides standard IRDAI exclusion."
        ),
        "plan_codes": ["REASSURE"],
    },
    {
        "insurer_code": "NIVA_BUPA",
        "item_category": "ROOM_UPGRADE_COPAY",
        "keywords": ["room upgrade", "room category upgrade", "higher room"],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 80.0,
        "reason": "Niva Bupa Health Companion applies 20% co-payment on room upgrade.",
        "plan_codes": ["HC"],
    },

    # ── NEW INDIA ASSURANCE ──────────────────────────────────────────────────
    {
        "insurer_code": "NEW_INDIA",
        "item_category": "SURGEON_CONSULTATION",
        "keywords": ["surgeon consultation", "surgical consultation", "specialist visit", "consultant charges"],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 80.0,
        "reason": "New India Assurance caps surgeon/specialist consultation fees at 80% per day.",
        "plan_codes": None,
    },

    # ── CARE HEALTH ──────────────────────────────────────────────────────────
    {
        "insurer_code": "CARE_HEALTH",
        "item_category": "EXTERNAL_PHARMACY",
        "keywords": ["outside pharmacy", "external pharmacy", "pharmacy bill", "retail pharmacy"],
        "verdict": "NOT_PAYABLE",
        "payable_pct": None,
        "reason": "Care Health does not cover medicines purchased from outside the hospital pharmacy.",
        "plan_codes": None,
    },
]


def upgrade() -> None:
    conn = op.get_bind()

    # Get insurer ID map
    result = conn.execute(sa.text("SELECT id, code FROM insurers"))
    insurer_map = {row.code: str(row.id) for row in result}

    for rule in INSURER_RULES:
        insurer_id = insurer_map.get(rule["insurer_code"])
        if not insurer_id:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO insurer_rules (id, insurer_id, item_category, keywords, verdict, payable_pct, reason, plan_codes)
                VALUES (:id, :insurer_id, :item_category, :keywords, :verdict, :payable_pct, :reason, :plan_codes)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "insurer_id": insurer_id,
                "item_category": rule["item_category"],
                "keywords": rule["keywords"],
                "verdict": rule["verdict"],
                "payable_pct": rule.get("payable_pct"),
                "reason": rule["reason"],
                "plan_codes": rule.get("plan_codes"),
            },
        )


def downgrade() -> None:
    op.execute("DELETE FROM insurer_rules")
