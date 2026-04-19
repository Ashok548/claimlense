"""
seeds/insurers/hdfc_ergo.py — HDFC ERGO General Insurance

Source data: migrations 003 (insurer), 004 (insurer_rules), 006 (plans + riders),
             009 (sublimit_rules), 015 (rider_coverage_clauses).

IMPORTANT — item_category values in INSURER_RULES must use canonical taxonomy codes
(see item_categories table or step0_categorize.py VALID_CATEGORIES).

Canonical codes:
    CONSUMABLE | DIAGNOSTIC_TEST | DRUG | IMPLANT | PROCEDURE | ROOM_RENT |
    ADMIN | NON_MEDICAL | ATTENDANT | EQUIPMENT_RENTAL | EXTERNAL_PHARMACY |
    COSMETIC | UNCLASSIFIED

Custom codes accepted by step5 (defined in item_categories via migration 011):
    MODERN_TREATMENT | CATARACT_PACKAGE | PHARMACY_COPAY |
    ROOM_UPGRADE_COPAY | SURGEON_CONSULTATION

Rider clause target_categories use canonical codes only (migration 017 extended the taxonomy
to include OPD, CONSULTATION, MATERNITY, DELIVERY, CRITICAL_ILLNESS, DENTAL).
"""

INSURER = {
    "code": "HDFC_ERGO",
    "name": "HDFC ERGO General Insurance",
    "logo_url": None,
    "room_rent_default": 4000,
}

PLANS = [
    {
        "code": "OPTIMA_SECURE",
        "name": "Optima Secure",
        "description": "Premium plan — full consumables coverage, no room rent limit.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": None,          # no room rent restriction
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": True,           # plan-level flag — step5b respects this
        "consumables_sublimit": None,
    },
    {
        "code": "OPTIMA_RESTORE",
        "name": "Optima Restore",
        "description": "Restore benefit — room rent capped at 1% of sum insured/day.",
        "room_rent_limit_pct": 1.0,
        "room_rent_limit_abs": None,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": None,
    },
    {
        "code": "MY_HEALTH",
        "name": "My:Health Suraksha",
        "description": "Standard plan — room rent capped at ₹4,000/day.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 4000.0,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": False,
        "consumables_sublimit": None,
    },
]

# Rider clauses use keyword_set names that must exist in the keyword_sets table
# (seeded by migration 011). Clause categories include legacy aliases for
# backward-compat with step5b boolean fallback path.
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

# OPTIMA_SECURE already covers consumables natively via consumables_covered=True,
# so CONSUMABLE_COVER rider is not linked to it (avoids redundant rescue attempt).
PLAN_RIDERS = [
    ("OPTIMA_SECURE",  "OPD_RIDER"),
    ("OPTIMA_SECURE",  "MATERNITY_RIDER"),
    ("OPTIMA_SECURE",  "CRITICAL_ILLNESS"),
    ("OPTIMA_SECURE",  "PA_COVER"),
    ("OPTIMA_RESTORE", "CONSUMABLE_COVER"),
    ("OPTIMA_RESTORE", "OPD_RIDER"),
    ("OPTIMA_RESTORE", "MATERNITY_RIDER"),
    ("OPTIMA_RESTORE", "CRITICAL_ILLNESS"),
    ("OPTIMA_RESTORE", "PA_COVER"),
    ("MY_HEALTH",      "CONSUMABLE_COVER"),
    ("MY_HEALTH",      "OPD_RIDER"),
    ("MY_HEALTH",      "MATERNITY_RIDER"),
    ("MY_HEALTH",      "CRITICAL_ILLNESS"),
    ("MY_HEALTH",      "PA_COVER"),
]

# item_category = "CONSUMABLE" (remapped from CONSUMABLE_OVERRIDE by migration 016)
# plan_codes restricts this rule to OPTIMA_SECURE only.
INSURER_RULES = [
    {
        "item_category": "CONSUMABLE",
        "keywords": [
            "gloves", "surgical gloves", "mask", "syringe", "needle",
            "gauze", "bandage", "suture", "consumable", "disposable", "cannula",
        ],
        "verdict": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Under Optima Secure plan, consumables and disposables are fully covered — "
            "this overrides the standard IRDAI exclusion."
        ),
        "plan_codes": ["OPTIMA_SECURE"],
    },
]

# No aggregate sublimit caps for HDFC ERGO plans
SUBLIMIT_RULES = []
