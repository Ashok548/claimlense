"""
seeds/insurers/care_health.py — Care Health Insurance

Source data: migrations 003, 004, 006.
External pharmacy items (from outside the hospital pharmacy) are NOT_PAYABLE
across all Care Health plans.
"""

INSURER = {
    "code": "CARE_HEALTH",
    "name": "Care Health Insurance",
    "logo_url": None,
    "room_rent_default": 4000,
}

PLANS = [
    {
        "code": "CARE",
        "name": "Care",
        "description": "Standard plan — external pharmacy excluded, room rent capped at ₹4,000/day.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 4000.0,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": None,
    },
    {
        "code": "CARE_PLUS",
        "name": "Care Plus",
        "description": "Enhanced plan with additional benefits — no room rent restriction.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": None,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": None,
    },
]

RIDERS = [
    {
        "code": "CONSUMABLE_COVER",
        "name": "Consumables Cover",
        "description": "Covers all consumable hospital items billed separately.",
        "covers_consumables": True,
        "covers_opd": False,
        "covers_maternity": False,
        "covers_dental": False,
        "covers_critical_illness": False,
        "clauses": [
            {
                "target_categories": ["CONSUMABLE"],
                "fallback_kw_set_name": "CONSUMABLE_RIDER_DETECTION",
                "verdict": "PAYABLE",
                "payable_pct": None,
                "only_rescues_status": ["NOT_PAYABLE", "VERIFY_WITH_TPA"],
                "priority": 10,
                "reason_template": "Rider 'Consumables Cover' covers consumables",
            }
        ],
    },
    {
        "code": "OPD_RIDER",
        "name": "OPD Care",
        "description": "Outpatient consultation coverage.",
        "covers_consumables": False,
        "covers_opd": True,
        "covers_maternity": False,
        "covers_dental": False,
        "covers_critical_illness": False,
        "clauses": [
            {
                "target_categories": ["OPD", "CONSULTATION"],
                "fallback_kw_set_name": "OPD_DETECTION",
                "verdict": "PAYABLE",
                "payable_pct": None,
                "only_rescues_status": ["NOT_PAYABLE", "VERIFY_WITH_TPA"],
                "priority": 10,
                "reason_template": "Rider 'OPD Care' covers OPD / outpatient",
            }
        ],
    },
    {
        "code": "MATERNITY_RIDER",
        "name": "Maternity Extension",
        "description": "Maternity and delivery expense coverage.",
        "covers_consumables": False,
        "covers_opd": False,
        "covers_maternity": True,
        "covers_dental": False,
        "covers_critical_illness": False,
        "clauses": [
            {
                "target_categories": ["MATERNITY", "DELIVERY"],
                "fallback_kw_set_name": "MATERNITY_DETECTION",
                "verdict": "PAYABLE",
                "payable_pct": None,
                "only_rescues_status": ["NOT_PAYABLE", "VERIFY_WITH_TPA"],
                "priority": 10,
                "reason_template": "Rider 'Maternity Extension' covers maternity",
            }
        ],
    },
    {
        "code": "CRITICAL_ILLNESS",
        "name": "Critical Illness Shield",
        "description": "Lump sum on diagnosis of listed critical illnesses.",
        "covers_consumables": False,
        "covers_opd": False,
        "covers_maternity": False,
        "covers_dental": False,
        "covers_critical_illness": True,
        "clauses": [
            {
                "target_categories": ["CRITICAL_ILLNESS"],
                "fallback_kw_set_name": None,
                "verdict": "PAYABLE",
                "payable_pct": None,
                "only_rescues_status": ["NOT_PAYABLE", "VERIFY_WITH_TPA"],
                "priority": 10,
                "reason_template": "Rider 'Critical Illness Shield' covers critical illness",
            }
        ],
    },
    {
        "code": "PA_COVER",
        "name": "Personal Accident Cover",
        "description": "Personal accident benefit.",
        "covers_consumables": False,
        "covers_opd": False,
        "covers_maternity": False,
        "covers_dental": False,
        "covers_critical_illness": False,
        "clauses": [],
    },
]

PLAN_RIDERS = [
    ("CARE",      "CONSUMABLE_COVER"),
    ("CARE",      "OPD_RIDER"),
    ("CARE",      "MATERNITY_RIDER"),
    ("CARE",      "CRITICAL_ILLNESS"),
    ("CARE",      "PA_COVER"),
    ("CARE_PLUS", "CONSUMABLE_COVER"),
    ("CARE_PLUS", "OPD_RIDER"),
    ("CARE_PLUS", "MATERNITY_RIDER"),
    ("CARE_PLUS", "CRITICAL_ILLNESS"),
    ("CARE_PLUS", "PA_COVER"),
]

# plan_codes=None → applies to all Care Health plans
INSURER_RULES = [
    {
        "item_category": "EXTERNAL_PHARMACY",
        "keywords": [
            "outside pharmacy", "external pharmacy",
            "pharmacy bill", "retail pharmacy",
        ],
        "verdict": "NOT_PAYABLE",
        "payable_pct": None,
        "reason": (
            "Care Health does not cover medicines purchased from outside "
            "the hospital pharmacy."
        ),
        "plan_codes": None,
    },
]

SUBLIMIT_RULES = []
