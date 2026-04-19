"""Migration 020 — assert rider_coverage_clauses completeness.

Every Rider row with at least one boolean coverage flag set to true must have
at least one matching rider_coverage_clauses row.  This migration raises an
error during upgrade if any are missing, making misconfigured insurers visible
at deploy time rather than silently at request time.

After this migration succeeds, _legacy_boolean_check in step5b_riders.py is
provably unreachable and can be deleted in a future cleanup commit.

This migration is NON-DESTRUCTIVE — it only reads data, never writes.
It is safe to re-run (downgrade is a no-op).
"""

from alembic import op
import sqlalchemy as sa

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Find riders with at least one boolean flag set but no clause rows
    missing = conn.execute(
        sa.text("""
            SELECT r.code, r.insurer_id,
                   r.covers_consumables, r.covers_opd, r.covers_maternity,
                   r.covers_dental, r.covers_critical_illness
            FROM riders r
            WHERE (
                r.covers_consumables = true
                OR r.covers_opd = true
                OR r.covers_maternity = true
                OR r.covers_dental = true
                OR r.covers_critical_illness = true
            )
            AND NOT EXISTS (
                SELECT 1 FROM rider_coverage_clauses c WHERE c.rider_id = r.id
            )
        """)
    ).fetchall()

    if missing:
        codes = [row.code for row in missing]
        raise RuntimeError(
            f"Migration 020 aborted: the following riders have boolean coverage flags "
            f"but no rider_coverage_clauses rows: {codes}. "
            f"Re-seed these insurers first: "
            f"  python seeds/runner.py --insurer <CODE>"
        )


def downgrade() -> None:
    # Non-destructive check — nothing to undo
    pass
