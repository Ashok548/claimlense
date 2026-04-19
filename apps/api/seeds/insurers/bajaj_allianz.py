"""
seeds/insurers/bajaj_allianz.py — Bajaj Allianz General Insurance

Source data: migrations 003, 004, 006.
Health Guard plan applies 30% co-payment on pharmacy/medicine bills.
"""

INSURER = {
    "code": "BAJAJ_ALLIANZ",
    "name": "Bajaj Allianz General Insurance",
    "logo_url": None,
    "room_rent_default": 3000,
}

PLANS = [
    {
        "code": "HEALTH_GUARD",
        "name": "Health Guard",
        "description": "Standard plan — 30% pharmacy co-pay, room rent capped at ₹3,000/day.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 3000.0,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,          # Global co-pay is 0; pharmacy co-pay is handled via insurer_rules
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": None,
    },
    {
        "code": "GLOBAL_HEALTH",
        "name": "Global Health Care",
        "description": "International coverage plan — no room rent restriction.",
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
    ("HEALTH_GUARD",   "CONSUMABLE_COVER"),
    ("HEALTH_GUARD",   "OPD_RIDER"),
    ("HEALTH_GUARD",   "MATERNITY_RIDER"),
    ("HEALTH_GUARD",   "CRITICAL_ILLNESS"),
    ("HEALTH_GUARD",   "PA_COVER"),
    ("GLOBAL_HEALTH",  "CONSUMABLE_COVER"),
    ("GLOBAL_HEALTH",  "OPD_RIDER"),
    ("GLOBAL_HEALTH",  "MATERNITY_RIDER"),
    ("GLOBAL_HEALTH",  "CRITICAL_ILLNESS"),
    ("GLOBAL_HEALTH",  "PA_COVER"),
]

# PHARMACY_COPAY is a custom category (step5 accepts non-canonical codes for
# insurer-specific logic). payable_pct=70 reflects 30% co-pay (100 - 30 = 70).
INSURER_RULES = [
    {
        "item_category": "PHARMACY_COPAY",
        "keywords": ["pharmacy", "medicines", "drugs", "medication"],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 70.0,
        "reason": "Bajaj Allianz Health Guard applies 30% co-payment on pharmacy/medicine bills.",
        "plan_codes": ["HEALTH_GUARD"],
    },
]

SUBLIMIT_RULES = []
