"""Migration 019 — bypass_categories column on billing_mode_rules.

Adds a TEXT[] column `bypass_categories` to `billing_mode_rules`.
When a rule row has this set, step3_billing.py uses it as the effective bypass
set instead of the hardcoded `_NON_CONSUMABLE_CATEGORIES` constant.

The highest-priority loaded row with a non-null `bypass_categories` wins:
  - Global default rows (insurer_id=NULL) receive the current hardcoded set so
    existing behaviour is preserved unchanged after the migration.
  - An insurer-specific row at higher priority can narrow or widen the set for
    that insurer without any Python code change.

This makes it possible, for example, to configure an insurer whose plans
include IMPLANT in package billing as PAYABLE — previously impossible without
editing the Python constant.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None

# Current hardcoded set from step3_billing._NON_CONSUMABLE_CATEGORIES
_DEFAULT_BYPASS = ["DIAGNOSTIC_TEST", "IMPLANT", "PROCEDURE", "ROOM_RENT", "DRUG"]


def upgrade() -> None:
    op.add_column(
        "billing_mode_rules",
        sa.Column("bypass_categories", ARRAY(sa.Text()), nullable=True),
    )

    # Seed the global default rows (insurer_id IS NULL) with the current hardcoded set
    # so the DB-driven path reproduces today's behaviour out of the box.
    op.get_bind().execute(
        sa.text(
            "UPDATE billing_mode_rules "
            "SET bypass_categories = :bypass "
            "WHERE insurer_id IS NULL"
        ),
        {"bypass": _DEFAULT_BYPASS},
    )


def downgrade() -> None:
    op.drop_column("billing_mode_rules", "bypass_categories")
