"""Migration 014 — rider_coverage_clauses table.

Adds the rider_coverage_clauses table that replaces the five hardcoded
boolean capability checks in step5b_riders.py:
  covers_consumables, covers_opd, covers_maternity, covers_dental, covers_critical_illness

The boolean columns on riders are NOT dropped here (see migration 015 for backfill).
A future cleanup migration can drop those columns once all riders are migrated.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rider_coverage_clauses",
        sa.Column(
            "id",
            PGUUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("rider_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("target_categories", ARRAY(sa.Text()), nullable=False),
        sa.Column("fallback_kw_set_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("verdict", sa.String(30), server_default="PAYABLE", nullable=False),
        sa.Column("payable_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "only_rescues_status",
            ARRAY(sa.Text()),
            server_default=sa.text("ARRAY['NOT_PAYABLE','VERIFY_WITH_TPA']::text[]"),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reason_template", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["rider_id"], ["riders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fallback_kw_set_id"], ["keyword_sets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rider_coverage_clauses_rider_id", "rider_coverage_clauses", ["rider_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_rider_coverage_clauses_rider_id", table_name="rider_coverage_clauses"
    )
    op.drop_table("rider_coverage_clauses")
