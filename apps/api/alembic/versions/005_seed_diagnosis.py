"""
Migration 005 — Seed diagnosis-aware overrides.
These run BEFORE universal exclusion rules to prevent
false rejections of medically necessary items.
"""

import uuid
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

DIAGNOSIS_OVERRIDES = [
    # ── Cataract ─────────────────────────────────────────────────────────────
    {
        "diagnosis_keyword": "cataract",
        "item_category": "CATARACT_PROCEDURE",
        "item_keywords": ["phaco", "phacoemulsification", "phaco machine", "iol", "intraocular lens", "lens implant"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Phacoemulsification (phaco machine) charges for cataract surgery are payable "
            "as part of the procedure cost per IRDAI circular on day-care procedures."
        ),
        "notes": "Ensure billing is done as cataract package for full payability.",
    },

    # ── Knee / Hip Replacement ────────────────────────────────────────────────
    {
        "diagnosis_keyword": "knee replacement",
        "item_category": "ORTHOPEDIC_IMPLANT",
        "item_keywords": ["implant", "knee implant", "prosthesis", "knee prosthesis", "tibial component", "femoral component"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Orthopedic implants (knee prosthesis) for knee replacement surgery are payable "
            "as medical devices integral to the procedure. Pre-authorization required."
        ),
        "notes": "Pre-authorization mandatory. Ensure original invoice from implant manufacturer is attached.",
    },
    {
        "diagnosis_keyword": "hip replacement",
        "item_category": "ORTHOPEDIC_IMPLANT",
        "item_keywords": ["implant", "hip implant", "prosthesis", "hip prosthesis", "acetabular cup", "femoral stem"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": "Hip replacement implants are payable per IRDAI implant coverage guidelines.",
        "notes": "Pre-authorization required. Original implant invoice mandatory.",
    },

    # ── Cardiac ───────────────────────────────────────────────────────────────
    {
        "diagnosis_keyword": "cardiac",
        "item_category": "CARDIAC_IMPLANT",
        "item_keywords": ["stent", "coronary stent", "drug eluting stent", "bare metal stent", "cardiac stent"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Coronary stents are payable as part of cardiac procedures. "
            "However, pre-authorization is mandatory for planned cardiac procedures."
        ),
        "notes": "Pre-authorization required. NPPA capped stent prices apply.",
    },
    {
        "diagnosis_keyword": "bypass",
        "item_category": "CARDIAC_IMPLANT",
        "item_keywords": ["stent", "coronary stent", "graft", "bypass graft"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": "Bypass graft and stent are payable under cardiac surgery coverage.",
        "notes": "Pre-auth mandatory. Document procedure type clearly.",
    },

    # ── Accident / Emergency ─────────────────────────────────────────────────
    {
        "diagnosis_keyword": "accident",
        "item_category": "EMERGENCY_CONSUMABLE",
        "item_keywords": ["suture", "sutures", "wound care", "wound dressing", "emergency dressing"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "In accident/emergency context, sutures and wound care consumables are payable "
            "as they are medically essential for the emergency treatment."
        ),
        "notes": "Document accident nature in discharge summary for smooth reimbursement.",
    },
    {
        "diagnosis_keyword": "trauma",
        "item_category": "EMERGENCY_CONSUMABLE",
        "item_keywords": ["suture", "sutures", "wound care", "wound dressing", "emergency consumable"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": "Trauma emergency consumables are payable due to emergency medical necessity.",
        "notes": "Attach emergency certificate from treating doctor.",
    },

    # ── Dialysis ──────────────────────────────────────────────────────────────
    {
        "diagnosis_keyword": "dialysis",
        "item_category": "DIALYSIS_CONSUMABLE",
        "item_keywords": ["dialysis consumable", "dialyzer", "tubing", "bicarbonate", "heparin"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Consumables used during dialysis sessions are payable as medically necessary "
            "items under the day-care procedure exception."
        ),
        "notes": "Dialysis is covered as a day-care procedure. Consumables included.",
    },

    # ── Chemotherapy ─────────────────────────────────────────────────────────
    {
        "diagnosis_keyword": "chemotherapy",
        "item_category": "CHEMO_CONSUMABLE",
        "item_keywords": ["chemotherapy consumable", "chemo consumable", "iv set", "infusion set", "chemo kit"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Consumables used during chemotherapy administration are payable as they "
            "are integral to the cancer treatment procedure."
        ),
        "notes": "Covered under day-care procedure. Oncology report required.",
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    for override in DIAGNOSIS_OVERRIDES:
        conn.execute(
            sa.text(
                """
                INSERT INTO diagnosis_overrides
                    (id, diagnosis_keyword, item_category, item_keywords, override_status, payable_pct, reason, notes)
                VALUES
                    (:id, :diagnosis_keyword, :item_category, :item_keywords, :override_status, :payable_pct, :reason, :notes)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "diagnosis_keyword": override["diagnosis_keyword"],
                "item_category": override["item_category"],
                "item_keywords": override["item_keywords"],
                "override_status": override["override_status"],
                "payable_pct": override.get("payable_pct"),
                "reason": override["reason"],
                "notes": override.get("notes"),
            },
        )


def downgrade() -> None:
    op.execute("DELETE FROM diagnosis_overrides")
