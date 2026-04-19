"""
Migration 010 — audit fields + deterministic partial constraints.

1) Adds audit metadata columns to bill_line_items so line-level rule basis is
   persisted and queryable.
2) Adds data-quality CHECK constraints to insurer_rules to ensure partial
   payouts are deterministic and bounded.
"""

from alembic import op
import sqlalchemy as sa


revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Persist rule-audit metadata on every analyzed line item.
    op.add_column("bill_line_items", sa.Column("decision_source", sa.String(100), nullable=True))
    op.add_column("bill_line_items", sa.Column("policy_basis_id", sa.String(200), nullable=True))
    op.add_column("bill_line_items", sa.Column("policy_basis_text", sa.Text(), nullable=True))
    op.add_column("bill_line_items", sa.Column("payable_pct_source", sa.String(50), nullable=True))

    # Normalize legacy bad data so new constraints can be applied safely.
    # PARTIALLY_PAYABLE without payable_pct is non-deterministic by definition.
    op.execute(
        """
        UPDATE insurer_rules
        SET verdict = 'VERIFY_WITH_TPA'
        WHERE verdict = 'PARTIALLY_PAYABLE' AND payable_pct IS NULL
        """
    )

    # Deterministic partial payouts require payable_pct to be present.
    op.create_check_constraint(
        "ck_insurer_rules_partial_requires_pct",
        "insurer_rules",
        "verdict <> 'PARTIALLY_PAYABLE' OR payable_pct IS NOT NULL",
    )

    # Any stored payable percentage must be in (0, 100].
    op.create_check_constraint(
        "ck_insurer_rules_payable_pct_bounds",
        "insurer_rules",
        "payable_pct IS NULL OR (payable_pct > 0 AND payable_pct <= 100)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_insurer_rules_payable_pct_bounds", "insurer_rules", type_="check")
    op.drop_constraint("ck_insurer_rules_partial_requires_pct", "insurer_rules", type_="check")

    op.drop_column("bill_line_items", "payable_pct_source")
    op.drop_column("bill_line_items", "policy_basis_text")
    op.drop_column("bill_line_items", "policy_basis_id")
    op.drop_column("bill_line_items", "decision_source")
