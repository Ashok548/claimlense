"""
Migration 008 — ICU per-day room rent limit + summary pending-verification column.

Two additive, backward-compatible column additions:

1. plans.icu_room_rent_limit_abs  (Numeric 10,2, nullable)
   Separate per-day cap for ICU/ICCU/HDU/NICU/PICU charges.
   When set, step4_room_rent uses this limit specifically for ICU line items
   instead of the generic room_rent_limit_abs, allowing separate deduction
   ratios for ICU vs general ward stays.
   NULL = fall back to room_rent_limit_abs (existing behaviour, fully safe).

2. claim_analyses.total_pending_verification  (Numeric 12,2, nullable, default 0)
   Sum of payable_amount for VERIFY_WITH_TPA items.
   Previously these were folded into total_payable, causing the confirmed-payable
   figure to look optimistic. Separating them lets the UI show an honest
   "Confirmed Payable" vs "Pending Verification" split.
   NULL on legacy rows = treat as 0 in the frontend (no backfill needed).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import NUMERIC

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. ICU per-day cap on plans table
    op.add_column(
        "plans",
        sa.Column(
            "icu_room_rent_limit_abs",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
    )

    # 2. Pending-verification total on claim_analyses table
    op.add_column(
        "claim_analyses",
        sa.Column(
            "total_pending_verification",
            sa.Numeric(precision=12, scale=2),
            server_default="0",
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("claim_analyses", "total_pending_verification")
    op.drop_column("plans", "icu_room_rent_limit_abs")
