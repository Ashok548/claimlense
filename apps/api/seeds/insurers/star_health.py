"""
seeds/insurers/star_health.py — Star Health & Allied Insurance

Source data: migrations 003, 004, 006.
No sublimit rules for Star Health plans.
"""

INSURER = {
    "code": "STAR_HEALTH",
    "name": "Star Health & Allied Insurance",
    "logo_url": None,
    "room_rent_default": 3000,
}

PLANS = [
    {
        "code": "COMPREHENSIVE",
        "name": "Comprehensive",
        "description": "Standard plan — room rent capped at 1% of sum insured/day.",
        "room_rent_limit_pct": 1.0,
        "room_rent_limit_abs": None,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": None,
    },
    {
        "code": "YOUNG_STAR",
        "name": "Young Star",
        "description": "Youth plan — room rent capped at ₹3,000/day.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 3000.0,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": None,
    },
    {
        "code": "SENIOR_RED",
        "name": "Senior Citizen Red Carpet",
        "description": "Senior plan — 30% co-payment, room rent capped at ₹3,000/day.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 3000.0,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 30.0,
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

# All riders available for all Star Health plans
PLAN_RIDERS = [
    ("COMPREHENSIVE", "CONSUMABLE_COVER"),
    ("COMPREHENSIVE", "OPD_RIDER"),
    ("COMPREHENSIVE", "MATERNITY_RIDER"),
    ("COMPREHENSIVE", "CRITICAL_ILLNESS"),
    ("COMPREHENSIVE", "PA_COVER"),
    ("YOUNG_STAR",    "CONSUMABLE_COVER"),
    ("YOUNG_STAR",    "OPD_RIDER"),
    ("YOUNG_STAR",    "MATERNITY_RIDER"),
    ("YOUNG_STAR",    "CRITICAL_ILLNESS"),
    ("YOUNG_STAR",    "PA_COVER"),
    ("SENIOR_RED",    "CONSUMABLE_COVER"),
    ("SENIOR_RED",    "OPD_RIDER"),
    ("SENIOR_RED",    "MATERNITY_RIDER"),
    ("SENIOR_RED",    "CRITICAL_ILLNESS"),
    ("SENIOR_RED",    "PA_COVER"),
]

INSURER_RULES = [
    {
        "item_category": "MODERN_TREATMENT",
        "keywords": [
            "robotic surgery", "robotic", "robot assisted",
            "laser surgery", "laser treatment",
        ],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 50.0,
        "reason": (
            "Star Health caps modern treatments (robotic/laser surgery) at 50% of actual cost "
            "under standard plans unless specifically covered."
        ),
        "plan_codes": None,   # applies to all Star Health plans
    },
    {
        "item_category": "CATARACT_PACKAGE",
        "keywords": [
            "cataract surgery", "phacoemulsification", "iol implant", "intraocular lens",
        ],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Cataract surgery is covered as a package under Star Health. "
            "Request hospital to bill as package."
        ),
        "plan_codes": None,
    },
]

SUBLIMIT_RULES = []
