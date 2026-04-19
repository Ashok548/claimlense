"""
Migration 009 — sublimit_rules table.

Creates a new `sublimit_rules` table for per-claim aggregate category caps.
Also backfills rows from the existing `plans.consumables_sublimit` column so
that the new step7_sublimit.py engine pass can enforce those limits.

This is additive and backward-compatible: the old consumables_sublimit column
is NOT dropped (it remains as the plan-level default for new plans seeded later).
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sublimit_rules",
        sa.Column(
            "id",
            PGUUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("insurer_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("item_category", sa.String(100), nullable=False),
        sa.Column("plan_codes", sa.ARRAY(sa.Text()), nullable=True),
        sa.Column("max_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["insurer_id"], ["insurers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_sublimit_rules_insurer_category",
        "sublimit_rules",
        ["insurer_id", "item_category"],
    )

    # Backfill sublimit_rules from existing plans.consumables_sublimit values.
    # Every plan with consumables_sublimit set becomes a sublimit rule restricted
    # to that specific plan code.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT p.id, p.insurer_id, p.code, p.consumables_sublimit
            FROM plans p
            WHERE p.consumables_sublimit IS NOT NULL
              AND p.consumables_sublimit > 0
            """
        )
    )
    for row in rows:
        conn.execute(
            sa.text(
                """
                INSERT INTO sublimit_rules (id, insurer_id, item_category, plan_codes, max_amount, note)
                VALUES (:id, :insurer_id, :category, :plan_codes, :max_amount, :note)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "insurer_id": str(row.insurer_id),
                "category": "CONSUMABLE",
                "plan_codes": [row.code],
                "max_amount": float(row.consumables_sublimit),
                "note": f"Backfilled from plans.consumables_sublimit for plan {row.code}",
            },
        )


def downgrade() -> None:
    op.drop_index("ix_sublimit_rules_insurer_category", table_name="sublimit_rules")
    op.drop_table("sublimit_rules")
