"""
seeds/insurers/icici_lombard.py — ICICI Lombard General Insurance

Source data: migrations 003, 004, 006, 009.
iHealth plan has a ₹5,000/claim consumable sublimit (backfilled by migration 009).
"""

INSURER = {
    "code": "ICICI_LOMBARD",
    "name": "ICICI Lombard General Insurance",
    "logo_url": None,
    "room_rent_default": 3500,
}

PLANS = [
    {
        "code": "IHEALTH",
        "name": "iHealth",
        "description": "Day-care list plan — consumables allowed up to ₹5,000 per hospitalisation.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 3500.0,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": 5000.0,   # enforced by step7 via sublimit_rules
    },
    {
        "code": "CHI",
        "name": "Complete Health Insurance",
        "description": "Comprehensive plan — no room rent sublimit.",
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
    ("IHEALTH", "CONSUMABLE_COVER"),
    ("IHEALTH", "OPD_RIDER"),
    ("IHEALTH", "MATERNITY_RIDER"),
    ("IHEALTH", "CRITICAL_ILLNESS"),
    ("IHEALTH", "PA_COVER"),
    ("CHI",     "CONSUMABLE_COVER"),
    ("CHI",     "OPD_RIDER"),
    ("CHI",     "MATERNITY_RIDER"),
    ("CHI",     "CRITICAL_ILLNESS"),
    ("CHI",     "PA_COVER"),
]

# item_category = "CONSUMABLE" (remapped from CONSUMABLE_SUBLIMIT by migration 016).
# verdict PAYABLE so step5 marks the item payable; step7 then applies the
# SUBLIMIT_RULES aggregate cap of ₹5,000.  Using PARTIALLY_PAYABLE without a
# payable_pct caused _effective_status() to downgrade to VERIFY_WITH_TPA, which
# step7_sublimit skips — meaning the cap never fired.
INSURER_RULES = [
    {
        "item_category": "CONSUMABLE",
        "keywords": ["consumable", "consumables", "disposable", "disposables"],
        "verdict": "PAYABLE",
        "payable_pct": None,
        "reason": (
            "ICICI Lombard iHealth plan allows consumables up to ₹5,000 per hospitalisation. "
            "Amount subject to aggregate sublimit cap."
        ),
        "plan_codes": ["IHEALTH"],
    },
]

# Backfilled from plans.consumables_sublimit=5000 for iHealth (migration 009)
SUBLIMIT_RULES = [
    {
        "item_category": "CONSUMABLE",
        "max_amount": 5000.0,
        "plan_codes": ["IHEALTH"],
        "note": "ICICI Lombard iHealth — consumable sublimit ₹5,000 per hospitalisation",
    },
]
