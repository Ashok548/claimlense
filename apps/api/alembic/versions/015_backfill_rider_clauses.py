"""Migration 015 — backfill rider_coverage_clauses from boolean columns.

For every existing rider row that has at least one coverage boolean set to true,
creates the corresponding rider_coverage_clauses rows so that the new
config-driven step5b_riders.py path picks them up without Python code changes.

Boolean columns on riders remain (deprecated) and are used as fallback by
step5b when the rider_coverage_clauses table is empty (backward-compat guard).
"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Resolve keyword set IDs created in migration 011
    kw_ids = {
        row.name: str(row.id)
        for row in conn.execute(
            sa.text("SELECT id, name FROM keyword_sets")
        ).fetchall()
    }

    riders = conn.execute(
        sa.text(
            "SELECT id, name, covers_consumables, covers_opd, covers_maternity, "
            "covers_dental, covers_critical_illness FROM riders"
        )
    ).fetchall()

    for rider in riders:
        if rider.covers_consumables:
            conn.execute(
                sa.text(
                    "INSERT INTO rider_coverage_clauses "
                    "(id, rider_id, target_categories, fallback_kw_set_id, verdict, "
                    "payable_pct, only_rescues_status, priority, reason_template) "
                    "VALUES (gen_random_uuid(), :rider_id, :cats, :kw_set, 'PAYABLE', "
                    "NULL, ARRAY['NOT_PAYABLE','VERIFY_WITH_TPA']::text[], 10, :reason)"
                ),
                {
                    "rider_id": str(rider.id),
                    "cats": ["CONSUMABLE", "CONSUMABLE_OVERRIDE", "CONSUMABLE_SUBLIMIT"],
                    "kw_set": kw_ids.get("CONSUMABLE_RIDER_DETECTION"),
                    "reason": f"Rider '{rider.name}' covers consumables",
                },
            )

        if rider.covers_opd:
            conn.execute(
                sa.text(
                    "INSERT INTO rider_coverage_clauses "
                    "(id, rider_id, target_categories, fallback_kw_set_id, verdict, "
                    "payable_pct, only_rescues_status, priority, reason_template) "
                    "VALUES (gen_random_uuid(), :rider_id, :cats, :kw_set, 'PAYABLE', "
                    "NULL, ARRAY['NOT_PAYABLE','VERIFY_WITH_TPA']::text[], 10, :reason)"
                ),
                {
                    "rider_id": str(rider.id),
                    "cats": ["OPD", "CONSULTATION"],
                    "kw_set": kw_ids.get("OPD_DETECTION"),
                    "reason": f"Rider '{rider.name}' covers OPD / outpatient",
                },
            )

        if rider.covers_maternity:
            conn.execute(
                sa.text(
                    "INSERT INTO rider_coverage_clauses "
                    "(id, rider_id, target_categories, fallback_kw_set_id, verdict, "
                    "payable_pct, only_rescues_status, priority, reason_template) "
                    "VALUES (gen_random_uuid(), :rider_id, :cats, :kw_set, 'PAYABLE', "
                    "NULL, ARRAY['NOT_PAYABLE','VERIFY_WITH_TPA']::text[], 10, :reason)"
                ),
                {
                    "rider_id": str(rider.id),
                    "cats": ["MATERNITY", "DELIVERY"],
                    "kw_set": kw_ids.get("MATERNITY_DETECTION"),
                    "reason": f"Rider '{rider.name}' covers maternity",
                },
            )

        if rider.covers_dental:
            conn.execute(
                sa.text(
                    "INSERT INTO rider_coverage_clauses "
                    "(id, rider_id, target_categories, fallback_kw_set_id, verdict, "
                    "payable_pct, only_rescues_status, priority, reason_template) "
                    "VALUES (gen_random_uuid(), :rider_id, :cats, NULL, 'PAYABLE', "
                    "NULL, ARRAY['NOT_PAYABLE','VERIFY_WITH_TPA']::text[], 10, :reason)"
                ),
                {
                    "rider_id": str(rider.id),
                    "cats": ["DENTAL"],
                    "reason": f"Rider '{rider.name}' covers dental",
                },
            )

        if rider.covers_critical_illness:
            conn.execute(
                sa.text(
                    "INSERT INTO rider_coverage_clauses "
                    "(id, rider_id, target_categories, fallback_kw_set_id, verdict, "
                    "payable_pct, only_rescues_status, priority, reason_template) "
                    "VALUES (gen_random_uuid(), :rider_id, :cats, NULL, 'PAYABLE', "
                    "NULL, ARRAY['NOT_PAYABLE','VERIFY_WITH_TPA']::text[], 10, :reason)"
                ),
                {
                    "rider_id": str(rider.id),
                    "cats": ["CRITICAL_ILLNESS"],
                    "reason": f"Rider '{rider.name}' covers critical illness",
                },
            )


def downgrade() -> None:
    # Removes all backfilled rows; manually-added rows are also deleted
    op.execute("DELETE FROM rider_coverage_clauses")
