"""Reference seed payload for room-rent configuration."""

DOMAIN = "room_rent"

ROOM_RENT_CONFIGS = [
    {
        "insurer_code": None,
        "plan_codes": None,
        "detection_kw_set_name": "ROOM_RENT_DETECTION",
        "icu_kw_set_name": "ICU_DETECTION",
        "deduction_method": "proportional",
        "icu_deduction_separate": True,
        "priority": 0,
    },
]
