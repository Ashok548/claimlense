"""
Migration 007 — Fix over-broad IRDAI CONSUMABLE exclusion keywords.

Remove the bare keyword "tube" from the CONSUMABLE exclusion rule.
"tube" is too broad: it matches "blood collection tube" and "culture tube",
which are DIAGNOSTIC_TEST items and should NOT be excluded.
"iv tube" (already present) is retained as the specific compound form.

This fix only matters for the Step 1 keyword fallback path, which runs when
Step 0 LLM categorisation fails and item_category is UNCLASSIFIED. Under normal
operation Step 0 catches these distinctions; the migration removes the safety risk
when GPT is unavailable or returns an unexpected result.
"""

from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove bare "tube" and bare "kit" from the CONSUMABLE exclusion rule keywords.
    # Both are over-broad: "tube" matches "blood collection tube" (DIAGNOSTIC_TEST)
    # and "kit" matches "culture kit" / "diagnostic kit" (also DIAGNOSTIC_TEST).
    # Specific compound forms ("iv tube", "ot kit") are seeded separately and retained.
    # array_remove() is a native PostgreSQL function that removes all occurrences
    # of an element from an array without requiring a full row replacement.
    op.execute(
        """
        UPDATE exclusion_rules
        SET keywords = array_remove(array_remove(keywords, 'tube'), 'kit')
        WHERE category = 'CONSUMABLE'
        """
    )


def downgrade() -> None:
    # Re-add both bare keywords on rollback (only if not already present).
    op.execute(
        """
        UPDATE exclusion_rules
        SET keywords = array_append(keywords, 'tube')
        WHERE category = 'CONSUMABLE'
          AND NOT ('tube' = ANY(keywords))
        """
    )
    op.execute(
        """
        UPDATE exclusion_rules
        SET keywords = array_append(keywords, 'kit')
        WHERE category = 'CONSUMABLE'
          AND NOT ('kit' = ANY(keywords))
        """
    )
