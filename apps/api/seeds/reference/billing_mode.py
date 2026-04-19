"""Reference seed payload for billing-mode rules."""

DOMAIN = "billing_mode"

_DEFAULT_BYPASS = ["DIAGNOSTIC_TEST", "IMPLANT", "PROCEDURE", "ROOM_RENT", "DRUG"]

BILLING_MODE_RULES = [
    {
        "insurer_code": None,
        "plan_codes": None,
        "item_category": "CONSUMABLE",
        "billing_mode": "package",
        "verdict": "PAYABLE",
        "payable_pct": None,
        "priority": 10,
        "reason": (
            "Item is part of a package — consumable costs are absorbed "
            "into the package billing and are payable."
        ),
        "recovery": (
            "Item is part of a package — consumable costs are absorbed "
            "into the package billing and are payable."
        ),
        "fallback_kw_set_name": "CONSUMABLE_BILLING_MODE",
        "bypass_categories": _DEFAULT_BYPASS,
    },
    {
        "insurer_code": None,
        "plan_codes": None,
        "item_category": "CONSUMABLE",
        "billing_mode": "mixed",
        "verdict": "VERIFY_WITH_TPA",
        "payable_pct": None,
        "priority": 10,
        "reason": (
            "Bill uses mixed (package + itemized) mode. It cannot be confirmed "
            "whether this consumable is bundled into the package component or "
            "billed separately. IRDAI excludes separately itemized consumables."
        ),
        "recovery": (
            "Ask the hospital billing desk whether this item is included in the "
            "package portion of the bill. If yes, request it be removed from the "
            "itemized section before submitting the insurance claim."
        ),
        "fallback_kw_set_name": "CONSUMABLE_BILLING_MODE",
        "bypass_categories": _DEFAULT_BYPASS,
    },
]