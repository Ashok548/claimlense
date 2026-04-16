"""
Migration 003 — Seed 7 Insurers.
"""

import uuid
import json
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

INSURERS = [
    {
        "code": "STAR_HEALTH",
        "name": "Star Health & Allied Insurance",
        "logo_url": None,
        "room_rent_default": 3000,
        "plans": [
            {"name": "Comprehensive", "code": "COMPREHENSIVE", "features": ["consumables excluded", "room rent 1% SI"]},
            {"name": "Young Star", "code": "YOUNG_STAR", "features": ["consumables excluded", "room rent capped"]},
            {"name": "Senior Citizen Red Carpet", "code": "SENIOR_RED", "features": ["co-payment 30%"]},
        ],
    },
    {
        "code": "HDFC_ERGO",
        "name": "HDFC ERGO General Insurance",
        "logo_url": None,
        "room_rent_default": 4000,
        "plans": [
            {"name": "Optima Secure", "code": "OPTIMA_SECURE", "features": ["consumables 100% covered", "no room rent limit"]},
            {"name": "Optima Restore", "code": "OPTIMA_RESTORE", "features": ["restore benefit", "room rent 1% SI"]},
            {"name": "My:Health Suraksha", "code": "MY_HEALTH", "features": ["standard plan"]},
        ],
    },
    {
        "code": "ICICI_LOMBARD",
        "name": "ICICI Lombard General Insurance",
        "logo_url": None,
        "room_rent_default": 3500,
        "plans": [
            {"name": "iHealth", "code": "IHEALTH", "features": ["day-care list", "consumable sub-limit ₹5000"]},
            {"name": "Complete Health Insurance", "code": "CHI", "features": ["comprehensive coverage"]},
        ],
    },
    {
        "code": "BAJAJ_ALLIANZ",
        "name": "Bajaj Allianz General Insurance",
        "logo_url": None,
        "room_rent_default": 3000,
        "plans": [
            {"name": "Health Guard", "code": "HEALTH_GUARD", "features": ["pharmacy 30% co-pay", "day-care list strict"]},
            {"name": "Global Health Care", "code": "GLOBAL_HEALTH", "features": ["international coverage"]},
        ],
    },
    {
        "code": "NIVA_BUPA",
        "name": "Niva Bupa Health Insurance (Max Bupa)",
        "logo_url": None,
        "room_rent_default": 5000,
        "plans": [
            {"name": "ReAssure 2.0", "code": "REASSURE", "features": ["consumables 100% covered", "unlimited restore"]},
            {"name": "Health Companion", "code": "HC", "features": ["room upgrade co-pay 20%"]},
        ],
    },
    {
        "code": "NEW_INDIA",
        "name": "New India Assurance",
        "logo_url": None,
        "room_rent_default": 2500,
        "plans": [
            {"name": "Mediclaim Policy", "code": "MEDICLAIM", "features": ["surgeon consultation capped 80%", "PSU scheme"]},
            {"name": "Floater Mediclaim", "code": "FLOATER", "features": ["family floater", "sub-limits apply"]},
        ],
    },
    {
        "code": "CARE_HEALTH",
        "name": "Care Health Insurance",
        "logo_url": None,
        "room_rent_default": 4000,
        "plans": [
            {"name": "Care", "code": "CARE", "features": ["external pharmacy excluded", "standard plan"]},
            {"name": "Care Plus", "code": "CARE_PLUS", "features": ["additional benefits"]},
        ],
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    for insurer in INSURERS:
        conn.execute(
            sa.text(
                """
                INSERT INTO insurers (id, code, name, logo_url, plans, room_rent_default, is_active)
                VALUES (:id, :code, :name, :logo_url, CAST(:plans AS jsonb), :room_rent_default, true)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": insurer["code"],
                "name": insurer["name"],
                "logo_url": insurer.get("logo_url"),
                "plans": json.dumps(insurer["plans"]),
                "room_rent_default": insurer["room_rent_default"],
            },
        )


def downgrade() -> None:
    op.execute("DELETE FROM insurers")
