"""Migration 018 — DB-driven diagnosis synonyms.

Replaces the compile-time DIAGNOSIS_SYNONYMS dict in step2_diagnosis.py with a
persistent database table.  The engine loader reads this table before the item
loop; step2 uses it in _diagnosis_matches() instead of the hardcoded constant.

A new synonym group can be added via SQL or a seed script with zero code change:

    INSERT INTO diagnosis_synonym_groups (base_term, synonyms)
    VALUES ('appendicitis', ARRAY['appendectomy', 'appendix removal']);

The 8 existing hardcoded entries are seeded here so existing behaviour is
preserved after the engine is wired to use the DB table.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None

INITIAL_SYNONYMS = [
    ("myocardial infarction", ["mi", "heart attack", "acute coronary syndrome", "acs"]),
    ("coronary artery disease", ["cad", "ischemic heart disease", "ihd"]),
    ("knee replacement", ["tkr", "total knee replacement", "total knee arthroplasty", "tka"]),
    ("hip replacement", ["thr", "total hip replacement", "total hip arthroplasty", "tha"]),
    ("cataract", ["phaco", "phacoemulsification", "lens opacity"]),
    ("dialysis", ["hemodialysis", "haemodialysis", "hd"]),
    ("chemotherapy", ["chemo", "oncology infusion"]),
    ("accident", ["rta", "road traffic accident", "trauma"]),
]


def upgrade() -> None:
    op.create_table(
        "diagnosis_synonym_groups",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("base_term", sa.Text(), nullable=False),
        sa.Column(
            "synonyms",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("base_term", name="uq_diagnosis_synonym_base_term"),
    )

    conn = op.get_bind()
    for base_term, synonyms in INITIAL_SYNONYMS:
        conn.execute(
            sa.text(
                "INSERT INTO diagnosis_synonym_groups (base_term, synonyms) "
                "VALUES (:base_term, :synonyms) "
                "ON CONFLICT (base_term) DO NOTHING"
            ),
            {"base_term": base_term, "synonyms": synonyms},
        )


def downgrade() -> None:
    op.drop_table("diagnosis_synonym_groups")
