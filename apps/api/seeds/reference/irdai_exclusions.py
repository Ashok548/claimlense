"""Reference seed payload for IRDAI universal exclusion rules."""

DOMAIN = "irdai_exclusions"

# Mirrors migration 002 and folds in the keyword narrowing from migration 007.
EXCLUSION_RULES = [
    {
        "category": "CONSUMABLE",
        "keywords": [
            "gloves", "surgical gloves", "mask", "face mask", "syringe", "needle",
            "gauze", "bandage", "suture", "sutures", "cotton", "catheter",
            "drape", "surgical drape", "cannula", "iv cannula", "iv tube",
            "dressing", "wound dressing", "ot kit", "pre-op kit",
            "prep kit", "phaco consumable", "ot pack", "sterile pack",
            "urine bag", "colostomy bag", "stoma bag",
            "consumable", "consumables", "disposable", "disposables",
            "ecg electrode", "splint", "kidney tray", "trolley cover",
            "delivery kit", "ortho kit", "recovery kit", "vasofix",
            "cold pack", "hot pack", "sanitary pad", "ambulance collar",
            "pan can", "urometer", "urine jug",
        ],
        "rejection_reason": (
            "Standard consumables and disposable items are excluded under IRDAI Circular "
            "IRDAI/HLT/REG/CIR/193/07/2020. These items when billed separately as "
            "line items are not payable by any insurer in India."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "ADMIN",
        "keywords": [
            "registration charge", "registration fee", "admission fee",
            "file charge", "file opening", "case file", "discharge fee",
            "discharge summary charge", "administrative charge", "admin charge",
            "gst charge", "gst on services", "service tax", "processing fee",
            "documentation fee", "medical record fee", "id card charge",
            "birth certificate", "certificate charge", "courier charge",
            "conveyance charge", "photocopy charge", "mortuary charge",
            "blood grouping donor", "surcharge", "medical certificate",
        ],
        "rejection_reason": (
            "Administrative, documentation, and non-medical overhead charges are "
            "not payable by insurance under IRDAI guidelines."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "NON_MEDICAL",
        "keywords": [
            "food charge", "food charges", "meal charge", "diet charge",
            "beverage", "tea charge", "coffee", "tiffin",
            "telephone", "phone charge", "mobile charge",
            "tv charges", "television", "cable tv",
            "soap", "toiletries", "personal items",
            "attendant food", "visitor meals",
            "laundry", "laundry charge", "washing charge",
            "baby food", "mineral water", "internet charge", "email charge",
            "sugar free", "diaper", "carry bag", "beauty service",
            "thermometer", "diabetic footwear", "ounce glass", "leggings",
            "buds", "guest service",
        ],
        "rejection_reason": (
            "Personal comfort items including food, beverages, telephone, TV, "
            "laundry, and toiletries are not covered under health insurance."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "ATTENDANT",
        "keywords": [
            "attendant charge", "attendant charges", "attendant fee",
            "bystander charge", "companion charge", "escort charge",
            "nursing attendant", "private attendant",
            "ayah charge", "ward attendant fee",
            "private nurse", "special nursing",
        ],
        "rejection_reason": (
            "Attendant, bystander, and companion charges are excluded from "
            "health insurance coverage."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "EQUIPMENT_RENTAL",
        "keywords": [
            "nebulizer rental", "nebulizer hire", "nebulizer charge",
            "cpap rental", "cpap hire", "bipap rental", "bipap hire",
            "monitor hire", "monitor rental", "equipment hire",
            "equipment rental", "machine hire", "machine rental",
            "wheelchair rental", "walker rental",
            "laser machine charge", "laser machine usage",
            "laser machine hire", "laser equipment charge",
            "oxygen cylinder outside", "ambulance equipment", "spacer",
            "spirometer", "steam inhaler", "arm sling", "armsling",
            "cervical collar", "knee brace", "knee immobilizer",
            "shoulder immobilizer", "lumbo sacral belt", "abdominal binder",
            "nimbus bed", "pelvic traction belt", "eyelet collar",
            "water bed", "air bed", "belts", "braces",
        ],
        "rejection_reason": (
            "External equipment rental and machine usage charges billed as separate "
            "line items are not payable. Equipment use should be embedded in the "
            "procedure package or ICU charges."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "COSMETIC",
        "keywords": [
            "cosmetic", "cosmetic surgery", "botox", "botulinum",
            "liposuction", "liposuction charge", "aesthetic",
            "anti-aging", "anti aging", "filler", "dermal filler",
            "hair transplant", "rhinoplasty cosmetic",
            "breast augmentation", "breast implant cosmetic",
        ],
        "rejection_reason": (
            "Cosmetic and aesthetic procedures are explicitly excluded under all "
            "Indian health insurance policies irrespective of insurer."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
    {
        "category": "EXTERNAL_PHARMACY",
        "keywords": [
            "outside pharmacy", "external pharmacy", "pharmacy bill",
            "pharmacy invoice", "medicine from outside",
            "drugs from retail", "retail pharmacy",
        ],
        "rejection_reason": (
            "Medicines purchased from outside the hospital pharmacy are not payable "
            "unless emergency justification is provided with a valid prescription."
        ),
        "source_circular": "IRDAI/HLT/REG/CIR/193/07/2020",
    },
]
