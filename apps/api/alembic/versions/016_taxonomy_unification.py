"""Migration 016 — taxonomy unification.

Remaps insurer_rules.item_category values that use ad-hoc custom category codes
(not in the Step 0 LLM taxonomy) to canonical categories from item_categories.

Why this matters:
  Step 0 (LLM) classifies items as canonical categories like CONSUMABLE.
  Step 5 (insurer rules) does a category-equality check. If an insurer rule uses
  CONSUMABLE_OVERRIDE but the item was classified as CONSUMABLE, the match fails
  silently and the rule never fires.

Remappings applied:
  CONSUMABLE_OVERRIDE  → CONSUMABLE   (plan_codes already narrows the scope)
  CONSUMABLE_SUBLIMIT  → CONSUMABLE   (plan_codes already narrows the scope)

Non-remapped custom categories (MODERN_TREATMENT, CATARACT_PACKAGE,
PHARMACY_COPAY, ROOM_UPGRADE_COPAY, SURGEON_CONSULTATION) are kept as-is
because they are genuinely distinct from CONSUMABLE and Step 0 may now
classify items into them directly (their codes appear in the LLM prompt
thanks to migration 011).
"""
from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None

REMAPPINGS = [
    ("CONSUMABLE_OVERRIDE", "CONSUMABLE"),
    ("CONSUMABLE_SUBLIMIT", "CONSUMABLE"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for old_cat, new_cat in REMAPPINGS:
        conn.execute(
            sa.text(
                "UPDATE insurer_rules SET item_category = :new_cat "
                "WHERE item_category = :old_cat"
            ),
            {"old_cat": old_cat, "new_cat": new_cat},
        )


def downgrade() -> None:
    # Best-effort reverse: only restores plan-scoped rules (where the remap was
    # originally safe because plan_codes provided the narrowing). Universal rules
    # with old_cat are not recoverable without additional metadata.
    conn = op.get_bind()
    for old_cat, new_cat in REMAPPINGS:
        conn.execute(
            sa.text(
                "UPDATE insurer_rules SET item_category = :old_cat "
                "WHERE item_category = :new_cat "
                "AND plan_codes IS NOT NULL AND cardinality(plan_codes) > 0"
            ),
            {"old_cat": old_cat, "new_cat": new_cat},
        )
