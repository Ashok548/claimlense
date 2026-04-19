"""
seeds/insurers/niva_bupa.py — Niva Bupa Health Insurance (formerly Max Bupa)

Source data: migrations 003, 004, 006.
ReAssure 2.0 plan covers consumables natively (consumables_covered=True).
Health Companion plan has a 20% room upgrade co-payment rule.
"""

INSURER = {
    "code": "NIVA_BUPA",
    "name": "Niva Bupa Health Insurance (Max Bupa)",
    "logo_url": None,
    "room_rent_default": 5000,
}

PLANS = [
    {
        "code": "REASSURE",
        "name": "ReAssure 2.0",
        "description": "Premium plan — consumables 100% covered, unlimited restore, no room rent limit.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": None,          # no room rent restriction
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,
        "icu_limit_pct": None,
        "consumables_covered": True,           # native consumables coverage
        "consumables_sublimit": None,
    },
    {
        "code": "HC",
        "name": "Health Companion",
        "description": "Standard plan — 20% co-pay on room upgrade, room rent capped at ₹5,000/day.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 5000.0,
        "icu_room_rent_limit_abs": None,
        "co_pay_pct": 0,           # Global co-pay is 0; room upgrade co-pay handled via insurer_rules
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

# REASSURE covers consumables natively — skip CONSUMABLE_COVER rider link for it.
PLAN_RIDERS = [
    ("REASSURE", "OPD_RIDER"),
    ("REASSURE", "MATERNITY_RIDER"),
    ("REASSURE", "CRITICAL_ILLNESS"),
    ("REASSURE", "PA_COVER"),
    ("HC",       "CONSUMABLE_COVER"),
    ("HC",       "OPD_RIDER"),
    ("HC",       "MATERNITY_RIDER"),
    ("HC",       "CRITICAL_ILLNESS"),
    ("HC",       "PA_COVER"),
]

INSURER_RULES = [
    # REASSURE — consumables fully override IRDAI exclusion
    # item_category = "CONSUMABLE" (remapped from CONSUMABLE_OVERRIDE by migration 016)
    {
        "item_category": "CONSUMABLE",
        "keywords": [
            "gloves", "surgical gloves", "mask", "syringe", "needle",
            "gauze", "bandage", "suture", "consumable", "consumables", "disposable",
        ],
        "verdict": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Niva Bupa ReAssure 2.0 plan fully covers consumables — "
            "overrides standard IRDAI exclusion."
        ),
        "plan_codes": ["REASSURE"],
    },
    # HC — 20% co-pay on room upgrades (ROOM_UPGRADE_COPAY is a custom category)
    {
        "item_category": "ROOM_UPGRADE_COPAY",
        "keywords": ["room upgrade", "room category upgrade", "higher room"],
        "verdict": "PARTIALLY_PAYABLE",
        "payable_pct": 80.0,
        "reason": "Niva Bupa Health Companion applies 20% co-payment on room upgrade.",
        "plan_codes": ["HC"],
    },
]

SUBLIMIT_RULES = []
