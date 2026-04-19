"""Migration 012 — room_rent_config table.

Moves ROOM_RENT_KEYWORDS and ICU_KEYWORDS (hardcoded in step4_room_rent.py)
and the deduction_method assumption into a database table.

Seeds a single global default row (insurer_id=NULL) that mirrors the existing
hardcoded behaviour so that runtime is immediately config-driven after migration.
"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "room_rent_config",
        sa.Column(
            "id",
            PGUUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("insurer_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("plan_codes", ARRAY(sa.Text()), nullable=True),
        sa.Column("detection_kw_set_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("icu_kw_set_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column(
            "deduction_method", sa.String(30), server_default="proportional", nullable=False
        ),
        sa.Column(
            "icu_deduction_separate", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["insurer_id"], ["insurers.id"]),
        sa.ForeignKeyConstraint(["detection_kw_set_id"], ["keyword_sets.id"]),
        sa.ForeignKeyConstraint(["icu_kw_set_id"], ["keyword_sets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_room_rent_config_insurer_priority",
        "room_rent_config",
        ["insurer_id", "priority"],
    )

    conn = op.get_bind()

    # Resolve keyword set IDs seeded in migration 011
    detection_id = conn.execute(
        sa.text("SELECT id FROM keyword_sets WHERE name = 'ROOM_RENT_DETECTION'")
    ).scalar_one()
    icu_id = conn.execute(
        sa.text("SELECT id FROM keyword_sets WHERE name = 'ICU_DETECTION'")
    ).scalar_one()

    # Global default row: insurer_id=NULL means it applies to all insurers
    conn.execute(
        sa.text(
            "INSERT INTO room_rent_config "
            "(id, insurer_id, plan_codes, detection_kw_set_id, icu_kw_set_id, "
            "deduction_method, icu_deduction_separate, priority) "
            "VALUES (gen_random_uuid(), NULL, NULL, :det_id, :icu_id, "
            "'proportional', true, 0)"
        ),
        {"det_id": str(detection_id), "icu_id": str(icu_id)},
    )


def downgrade() -> None:
    op.drop_index("ix_room_rent_config_insurer_priority", table_name="room_rent_config")
    op.drop_table("room_rent_config")
