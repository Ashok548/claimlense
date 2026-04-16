"""
Migration 001 — Create all FastAPI intelligence tables.
Run: alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON, ENUM
import uuid

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums
    payability_status = ENUM(
        "PAYABLE", "NOT_PAYABLE", "PARTIALLY_PAYABLE", "VERIFY_WITH_TPA",
        name="payability_status",
        create_type=False,
    )
    billing_mode = ENUM("itemized", "package", "mixed", name="billing_mode", create_type=False)
    policy_type = ENUM("individual", "floater", "group", name="policy_type", create_type=False)
    hospital_type = ENUM("empanelled", "non_empanelled", name="hospital_type", create_type=False)

    payability_status.create(op.get_bind(), checkfirst=True)
    billing_mode.create(op.get_bind(), checkfirst=True)
    policy_type.create(op.get_bind(), checkfirst=True)
    hospital_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "insurers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("plans", JSON),
        sa.Column("room_rent_default", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), default=True),
    )

    op.create_table(
        "exclusion_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("keywords", ARRAY(sa.Text()), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=False),
        sa.Column("source_circular", sa.String(200)),
        sa.Column("applies_to_all", sa.Boolean(), default=True),
    )

    op.create_table(
        "insurer_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("insurer_id", UUID(as_uuid=True), sa.ForeignKey("insurers.id"), nullable=False),
        sa.Column("item_category", sa.String(100), nullable=False),
        sa.Column("keywords", ARRAY(sa.Text()), nullable=False),
        sa.Column("verdict", payability_status, nullable=False),
        sa.Column("payable_pct", sa.Numeric(5, 2)),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("plan_codes", ARRAY(sa.Text())),
    )

    op.create_table(
        "diagnosis_overrides",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("diagnosis_keyword", sa.String(200), nullable=False),
        sa.Column("item_category", sa.String(100), nullable=False),
        sa.Column("item_keywords", ARRAY(sa.Text()), nullable=False),
        sa.Column("override_status", payability_status, nullable=False),
        sa.Column("payable_pct", sa.Numeric(5, 2)),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
    )

    op.create_table(
        "claim_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("insurer_id", UUID(as_uuid=True), sa.ForeignKey("insurers.id"), nullable=False),
        sa.Column("user_ref", UUID(as_uuid=True)),
        sa.Column("billing_mode", billing_mode, default="itemized"),
        sa.Column("policy_type", policy_type, default="individual"),
        sa.Column("hospital_type", hospital_type, default="empanelled"),
        sa.Column("diagnosis", sa.String(300)),
        sa.Column("sum_insured", sa.Numeric(12, 2), nullable=False),
        sa.Column("room_rent_limit", sa.Numeric(10, 2)),
        sa.Column("total_billed", sa.Numeric(12, 2), default=0),
        sa.Column("total_payable", sa.Numeric(12, 2), default=0),
        sa.Column("total_at_risk", sa.Numeric(12, 2), default=0),
        sa.Column("rejection_rate_pct", sa.Numeric(5, 2), default=0),
        sa.Column("action_items", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "bill_line_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("analysis_id", UUID(as_uuid=True), sa.ForeignKey("claim_analyses.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("billed_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payable_amount", sa.Numeric(10, 2), default=0),
        sa.Column("status", payability_status, nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("rule_matched", sa.String(200)),
        sa.Column("confidence", sa.Numeric(4, 3), default=0.55),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("recovery_action", sa.Text()),
        sa.Column("llm_used", sa.Boolean(), default=False),
    )


def downgrade() -> None:
    op.drop_table("bill_line_items")
    op.drop_table("claim_analyses")
    op.drop_table("diagnosis_overrides")
    op.drop_table("insurer_rules")
    op.drop_table("exclusion_rules")
    op.drop_table("insurers")

    for enum_name in ["payability_status", "billing_mode", "policy_type", "hospital_type"]:
        sa.Enum(name=enum_name).drop(op.get_bind())
