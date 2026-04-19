"""Migration 017 — extend item_categories with rider/benefit taxonomy.

Step 5b (rider coverage) uses rider_coverage_clauses.target_categories.
Step 0 (LLM) classifies items using the item_categories table for its prompt.
Without these categories in item_categories, Step 0 never emits them,
so rider clause target_categories that reference OPD, MATERNITY, etc. can
never fire via a category-equality match.

New categories added:
  OPD              — outpatient consultation charges (is_payable_by_default=False)
  CONSULTATION     — standalone doctor consultation fees
  MATERNITY        — maternity / obstetric charges
  DELIVERY         — delivery room / labour room charges
  CRITICAL_ILLNESS — critical illness lump-sum or benefit claims
  DENTAL           — dental treatment charges

All six have never_excluded=False and is_payable_by_default=False because
they are benefit-specific — only payable when the plan or rider explicitly
covers them.
"""

from alembic import op
import sqlalchemy as sa

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None

NEW_CATEGORIES = [
    {
        "code": "OPD",
        "display_name": "OPD Consultation",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Outpatient department charges billed during hospitalisation or as "
            "standalone OPD visits covered by a plan or rider."
        ),
        "llm_examples": [
            "OPD consultation", "outpatient visit", "clinic visit charge",
            "doctor visit fee", "follow-up consultation",
        ],
        "recovery_template": (
            "OPD charges are not covered under standard inpatient hospitalisation "
            "policies. Check whether your plan includes an OPD benefit rider."
        ),
    },
    {
        "code": "CONSULTATION",
        "display_name": "Doctor Consultation Fee",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Specialist or GP consultation fees billed as a separate line item "
            "outside of a surgical procedure or OT charge."
        ),
        "llm_examples": [
            "consultation fee", "doctor fee", "specialist fee", "visiting charge",
            "surgeon consultation", "physician fee",
        ],
        "recovery_template": (
            "Standalone consultation fees are not payable unless your policy "
            "includes a consultation benefit or OPD rider."
        ),
    },
    {
        "code": "MATERNITY",
        "display_name": "Maternity / Obstetric",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Maternity, obstetric, antenatal, or postnatal charges billed during "
            "the hospitalisation episode."
        ),
        "llm_examples": [
            "maternity charges", "antenatal care", "postnatal care",
            "obstetric fee", "prenatal visit", "ante natal",
        ],
        "recovery_template": (
            "Maternity charges are covered only under plans or riders with an "
            "explicit maternity benefit. Check your policy schedule."
        ),
    },
    {
        "code": "DELIVERY",
        "display_name": "Delivery / Labour Room",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Delivery charges, labour room fees, C-section or normal delivery "
            "procedure costs."
        ),
        "llm_examples": [
            "delivery charges", "labour room", "normal delivery", "C-section",
            "caesarean", "LSCS charges", "labour charge",
        ],
        "recovery_template": (
            "Delivery and labour room charges require a maternity benefit rider "
            "or a maternity-inclusive plan. Verify with your insurer."
        ),
    },
    {
        "code": "CRITICAL_ILLNESS",
        "display_name": "Critical Illness",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Charges or benefit triggers associated with critical illness conditions "
            "such as cancer, stroke, or heart attack."
        ),
        "llm_examples": [
            "critical illness", "cancer treatment", "stroke rehabilitation",
            "organ failure", "cardiac arrest management",
        ],
        "recovery_template": (
            "Critical illness benefits are lump-sum payouts triggered by diagnosis "
            "of a listed condition. Verify your CI rider or plan schedule."
        ),
    },
    {
        "code": "DENTAL",
        "display_name": "Dental Treatment",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Dental procedure charges billed during hospitalisation or as standalone "
            "dental treatment under a dental rider."
        ),
        "llm_examples": [
            "dental extraction", "tooth removal", "scaling", "root canal",
            "dental surgery", "wisdom tooth", "dental charges",
        ],
        "recovery_template": (
            "Dental charges are excluded from standard hospitalisation cover. "
            "Check whether your plan includes a dental benefit rider."
        ),
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    for cat in NEW_CATEGORIES:
        # Idempotent: skip if already present (e.g. manual insert or re-run)
        existing = conn.execute(
            sa.text("SELECT 1 FROM item_categories WHERE code = :code"),
            {"code": cat["code"]},
        ).fetchone()
        if existing:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO item_categories "
                "(code, display_name, description, never_excluded, "
                " is_payable_by_default, llm_examples, recovery_template) "
                "VALUES "
                "(:code, :display_name, :description, :never_excluded, "
                " :is_payable_by_default, :llm_examples, :recovery_template)"
            ),
            {
                "code": cat["code"],
                "display_name": cat["display_name"],
                "description": cat["description"],
                "never_excluded": cat["never_excluded"],
                "is_payable_by_default": cat["is_payable_by_default"],
                "llm_examples": cat["llm_examples"],
                "recovery_template": cat["recovery_template"],
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    codes = [c["code"] for c in NEW_CATEGORIES]
    for code in codes:
        conn.execute(
            sa.text("DELETE FROM item_categories WHERE code = :code"),
            {"code": code},
        )
