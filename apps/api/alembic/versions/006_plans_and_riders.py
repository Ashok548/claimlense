"""
Migration 006 — Plans, Riders, and their junctions.
"""

import uuid
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create tables
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('insurer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('room_rent_limit_pct', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('room_rent_limit_abs', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('co_pay_pct', sa.Numeric(precision=4, scale=2), server_default='0', nullable=True),
        sa.Column('icu_limit_pct', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('consumables_covered', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('consumables_sublimit', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['insurer_id'], ['insurers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('insurer_id', 'code')
    )

    op.create_table(
        'riders',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('insurer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('covers_consumables', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('covers_opd', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('covers_maternity', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('covers_dental', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('covers_critical_illness', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('additional_sum_insured', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['insurer_id'], ['insurers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('insurer_id', 'code')
    )

    op.create_table(
        'plan_riders',
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rider_id'], ['riders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('plan_id', 'rider_id')
    )

    # 2. Seed data
    conn = op.get_bind()
    
    # Get insurer mappings
    result = conn.execute(sa.text("SELECT id, code FROM insurers"))
    insurer_map = {row.code: str(row.id) for row in result}

    # Data defined from implementation plan
    # Plans
    plans_data = [
        {"insurer_code": "STAR_HEALTH", "code": "COMPREHENSIVE", "name": "Comprehensive", "room_rent_limit_pct": 1.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "STAR_HEALTH", "code": "YOUNG_STAR", "name": "Young Star", "room_rent_limit_abs": 3000.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "STAR_HEALTH", "code": "SENIOR_RED", "name": "Senior Citizen Red Carpet", "room_rent_limit_abs": 3000.0, "co_pay_pct": 30.0, "consumables_covered": False},
        {"insurer_code": "HDFC_ERGO", "code": "OPTIMA_SECURE", "name": "Optima Secure", "room_rent_limit_abs": None, "co_pay_pct": 0, "consumables_covered": True},
        {"insurer_code": "HDFC_ERGO", "code": "OPTIMA_RESTORE", "name": "Optima Restore", "room_rent_limit_pct": 1.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "HDFC_ERGO", "code": "MY_HEALTH", "name": "My:Health Suraksha", "room_rent_limit_abs": 4000.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "ICICI_LOMBARD", "code": "IHEALTH", "name": "iHealth", "room_rent_limit_abs": 3500.0, "co_pay_pct": 0, "consumables_covered": False, "consumables_sublimit": 5000.0},
        {"insurer_code": "ICICI_LOMBARD", "code": "CHI", "name": "Complete Health Insurance", "room_rent_limit_abs": None, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "BAJAJ_ALLIANZ", "code": "HEALTH_GUARD", "name": "Health Guard", "room_rent_limit_abs": 3000.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "BAJAJ_ALLIANZ", "code": "GLOBAL_HEALTH", "name": "Global Health Care", "room_rent_limit_abs": None, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "NIVA_BUPA", "code": "REASSURE", "name": "ReAssure 2.0", "room_rent_limit_abs": None, "co_pay_pct": 0, "consumables_covered": True},
        {"insurer_code": "NIVA_BUPA", "code": "HC", "name": "Health Companion", "room_rent_limit_abs": 5000.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "NEW_INDIA", "code": "MEDICLAIM", "name": "Mediclaim Policy", "room_rent_limit_abs": 2500.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "NEW_INDIA", "code": "FLOATER", "name": "Floater Mediclaim", "room_rent_limit_abs": 2500.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "CARE_HEALTH", "code": "CARE", "name": "Care", "room_rent_limit_abs": 4000.0, "co_pay_pct": 0, "consumables_covered": False},
        {"insurer_code": "CARE_HEALTH", "code": "CARE_PLUS", "name": "Care Plus", "room_rent_limit_abs": None, "co_pay_pct": 0, "consumables_covered": False},
    ]

    plan_ids = {}
    for p in plans_data:
        i_id = insurer_map.get(p["insurer_code"])
        if not i_id:
            continue
        p_id = str(uuid.uuid4())
        plan_ids[(p["insurer_code"], p["code"])] = p_id
        conn.execute(
            sa.text(
                """
                INSERT INTO plans (id, insurer_id, code, name, room_rent_limit_pct, room_rent_limit_abs, co_pay_pct, consumables_covered, consumables_sublimit)
                VALUES (:id, :insurer_id, :code, :name, :room_rent_limit_pct, :room_rent_limit_abs, :co_pay_pct, :consumables_covered, :consumables_sublimit)
                """
            ),
            {
                "id": p_id,
                "insurer_id": i_id,
                "code": p["code"],
                "name": p["name"],
                "room_rent_limit_pct": p.get("room_rent_limit_pct"),
                "room_rent_limit_abs": p.get("room_rent_limit_abs"),
                "co_pay_pct": p.get("co_pay_pct", 0),
                "consumables_covered": p.get("consumables_covered", False),
                "consumables_sublimit": p.get("consumables_sublimit"),
            }
        )

    # Riders
    rider_templates = [
        {"code": "CONSUMABLE_COVER", "name": "Consumables Cover", "covers_consumables": True, "covers_opd": False, "covers_maternity": False},
        {"code": "OPD_RIDER", "name": "OPD Care", "covers_consumables": False, "covers_opd": True, "covers_maternity": False},
        {"code": "MATERNITY_RIDER", "name": "Maternity Extension", "covers_consumables": False, "covers_opd": False, "covers_maternity": True},
        {"code": "CRITICAL_ILLNESS", "name": "Critical Illness Shield", "covers_consumables": False, "covers_opd": False, "covers_maternity": False},
        {"code": "PA_COVER", "name": "Personal Accident Cover", "covers_consumables": False, "covers_opd": False, "covers_maternity": False},
    ]

    rider_ids = {}
    for code, i_id in insurer_map.items():
        for r in rider_templates:
            r_id = str(uuid.uuid4())
            rider_ids[(code, r["code"])] = r_id
            conn.execute(
                sa.text(
                    """
                    INSERT INTO riders (id, insurer_id, code, name, covers_consumables, covers_opd, covers_maternity)
                    VALUES (:id, :insurer_id, :code, :name, :covers_consumables, :covers_opd, :covers_maternity)
                    """
                ),
                {
                    "id": r_id,
                    "insurer_id": i_id,
                    "code": r["code"],
                    "name": r["name"],
                    "covers_consumables": r["covers_consumables"],
                    "covers_opd": r["covers_opd"],
                    "covers_maternity": r["covers_maternity"]
                }
            )

    # Plan-Riders (Assign riders to plans)
    plan_rider_links = []
    
    for (i_code, p_code), p_id in plan_ids.items():
        for r in rider_templates:
            r_code = r["code"]
            
            # Skip consumable rider if the plan inherently covers them
            if r_code == "CONSUMABLE_COVER" and p_code in ("OPTIMA_SECURE", "REASSURE"):
                continue
            
            r_id = rider_ids.get((i_code, r_code))
            if r_id:
                plan_rider_links.append({"plan_id": p_id, "rider_id": r_id})
                
    for link in plan_rider_links:
        conn.execute(
            sa.text("INSERT INTO plan_riders (plan_id, rider_id) VALUES (:plan_id, :rider_id)"),
            link
        )
        

def downgrade() -> None:
    op.drop_table('plan_riders')
    op.drop_table('riders')
    op.drop_table('plans')
