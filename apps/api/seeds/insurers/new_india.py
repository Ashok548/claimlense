"""
seeds/insurers/new_india.py — New India Assurance

Source data: migrations 003, 004, 006.
All plans cap surgeon/specialist consultation at 80%.
SURGEON_CONSULTATION is a custom category recognised by step5.
"""

INSURER = {
    "code": "NEW_INDIA",
    "name": "New India Assurance",
    "logo_url": None,
    "room_rent_default": 2500,
}

PLANS = [
    {
        "code": "MEDICLAIM",
        "name": "Mediclaim Policy",
        "description": "Public-sector standard plan — surgeon consultation capped at 80%.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 2500.0,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": None,
    },
    {
        "code": "FLOATER",
        "name": "Floater Mediclaim",
        "description": "Family floater plan — sub-limits apply.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 2500.0,
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
    ("MEDICLAIM", "CONSUMABLE_COVER"),
    ("MEDICLAIM", "OPD_RIDER"),
    ("MEDICLAIM", "MATERNITY_RIDER"),
    ("MEDICLAIM", "CRITICAL_ILLNESS"),
    ("MEDICLAIM", "PA_COVER"),
    ("FLOATER",   "CONSUMABLE_COVER"),
    ("FLOATER",   "OPD_RIDER"),
    ("FLOATER",   "MATERNITY_RIDER"),
    ("FLOATER",   "CRITICAL_ILLNESS"),
    ("FLOATER",   "PA_COVER"),
]

# plan_codes=None → applies to all New India plans
INSURER_RULES = [
    {
        "item_category": "SURGEON_CONSULTATION",
        "keywords": [
            "surgeon consultation", "surgical consultation",
            "specialist visit", "consultant charges",
        ],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 80.0,
        "reason": "New India Assurance caps surgeon/specialist consultation fees at 80% per day.",
        "plan_codes": None,
    },
]

SUBLIMIT_RULES = []
