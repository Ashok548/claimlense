"""Migration 013 — billing_mode_rules table.

Moves the hardcoded billing-mode branch logic and CONSUMABLE_KEYWORDS from
step3_billing.py into a database table.

Seeds two universal rows covering the meaningful billing-mode scenarios:
  CONSUMABLE × PACKAGE → PAYABLE
  CONSUMABLE × MIXED   → VERIFY_WITH_TPA

Both rows carry a reference to the CONSUMABLE_BILLING_MODE keyword_set as a
fallback for UNCLASSIFIED items so the old keyword-matching path is data-driven.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None

UNIVERSAL_BILLING_RULES = [
    {
        "item_category": "CONSUMABLE",
        "billing_mode": "package",
        "verdict": "PAYABLE",
        "payable_pct": None,
        "priority": 10,
        "reason": (
            "Item is part of a package — consumable costs are absorbed "
            "into the package billing and are payable."
        ),
        "recovery": (
            "Item is part of a package — consumable costs are absorbed "
            "into the package billing and are payable."
        ),
        "fallback_kw_set": "CONSUMABLE_BILLING_MODE",
    },
    {
        "item_category": "CONSUMABLE",
        "billing_mode": "mixed",
        "verdict": "VERIFY_WITH_TPA",
        "payable_pct": None,
        "priority": 10,
        "reason": (
            "Bill uses mixed (package + itemized) mode. It cannot be confirmed "
            "whether this consumable is bundled into the package component or "
            "billed separately. IRDAI excludes separately itemized consumables."
        ),
        "recovery": (
            "Ask the hospital billing desk whether this item is included in the "
            "package portion of the bill. If yes, request it be removed from the "
            "itemized section before submitting the insurance claim."
        ),
        "fallback_kw_set": "CONSUMABLE_BILLING_MODE",
    },
]


def upgrade() -> None:
    op.create_table(
        "billing_mode_rules",
        sa.Column(
            "id",
            PGUUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("insurer_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("plan_codes", ARRAY(sa.Text()), nullable=True),
        sa.Column("item_category", sa.String(50), nullable=False),
        sa.Column("billing_mode", sa.String(20), nullable=False),
        sa.Column("verdict", sa.String(30), nullable=False),
        sa.Column("payable_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("recovery", sa.Text(), nullable=True),
        sa.Column("fallback_kw_set_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["insurer_id"], ["insurers.id"]),
        sa.ForeignKeyConstraint(["fallback_kw_set_id"], ["keyword_sets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_billing_mode_rules_insurer_mode",
        "billing_mode_rules",
        ["insurer_id", "billing_mode", "item_category"],
    )

    conn = op.get_bind()

    kw_ids = {
        row.name: str(row.id)
        for row in conn.execute(
            sa.text("SELECT id, name FROM keyword_sets")
        ).fetchall()
    }

    for rule in UNIVERSAL_BILLING_RULES:
        conn.execute(
            sa.text(
                "INSERT INTO billing_mode_rules "
                "(id, insurer_id, plan_codes, item_category, billing_mode, verdict, "
                "payable_pct, reason, recovery, fallback_kw_set_id, priority) "
                "VALUES (gen_random_uuid(), NULL, NULL, :item_category, :billing_mode, "
                ":verdict, :payable_pct, :reason, :recovery, :fallback_kw_set_id, :priority)"
            ),
            {
                "item_category": rule["item_category"],
                "billing_mode": rule["billing_mode"],
                "verdict": rule["verdict"],
                "payable_pct": rule.get("payable_pct"),
                "reason": rule["reason"],
                "recovery": rule.get("recovery"),
                "fallback_kw_set_id": kw_ids.get(rule["fallback_kw_set"]),
                "priority": rule["priority"],
            },
        )


def downgrade() -> None:
    op.drop_index("ix_billing_mode_rules_insurer_mode", table_name="billing_mode_rules")
    op.drop_table("billing_mode_rules")
