"""Reference seed payload for reusable keyword sets."""

DOMAIN = "keyword_sets"

KEYWORD_SETS = [
    {
        "name": "ROOM_RENT_DETECTION",
        "is_system": True,
        "description": "Keywords that identify room/accommodation line items (step4).",
        "keywords": [
            "room rent", "room charge", "bed charge", "ward charge",
            "accommodation", "room & board", "room and board",
            "single room", "double room", "general ward", "ac room",
            "icu charges", "iccu", "hdu", "nicu", "picu",
        ],
    },
    {
        "name": "ICU_DETECTION",
        "is_system": True,
        "description": "Keywords that identify ICU/critical-care line items within room rent (step4).",
        "keywords": ["icu", "iccu", "hdu", "nicu", "picu"],
    },
    {
        "name": "CONSUMABLE_BILLING_MODE",
        "is_system": True,
        "description": "Consumable keywords for billing-mode rescue in package/mixed claims (step3 fallback).",
        "keywords": [
            "gloves", "mask", "syringe", "needle", "gauze", "bandage",
            "suture", "consumable", "disposable", "cotton", "catheter",
            "drape", "cannula", "iv tube", "drain tube", "ot kit", "surgical kit",
            "sterile pack", "dressing pack", "dressing",
        ],
    },
    {
        "name": "MATERNITY_DETECTION",
        "is_system": True,
        "description": "Keywords identifying maternity/obstetric billing items (step5b rider fallback).",
        "keywords": [
            "maternity", "delivery", "c-section", "caesarean", "lscs",
            "obstetric", "obstetrics", "antenatal", "ante natal",
            "postnatal", "post natal", "prenatal", "pre natal",
            "episiotomy", "neonatal", "newborn care", "new born care",
            "vacuum delivery", "forceps delivery",
            "labour charge", "labor charge", "labour room", "labor room",
            "normal delivery", "assisted delivery",
        ],
    },
    {
        "name": "OPD_DETECTION",
        "is_system": True,
        "description": "Keywords identifying OPD/outpatient items (step5b rider fallback).",
        "keywords": ["opd", "outpatient", "consultation"],
    },
    {
        "name": "CONSUMABLE_RIDER_DETECTION",
        "is_system": True,
        "description": "Short-form consumable keywords for rider rescue (step5b).",
        "keywords": ["gloves", "syringe", "mask", "disposable", "consumable"],
    },
]
