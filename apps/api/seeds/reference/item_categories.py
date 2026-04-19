"""Reference seed payload for canonical item categories."""

DOMAIN = "item_categories"

ITEM_CATEGORIES = [
    {
        "code": "DIAGNOSTIC_TEST",
        "display_name": "Diagnostic Test",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Laboratory tests, imaging, pathology, and any diagnostic investigations.",
        "llm_examples": ["CBC", "LFT", "MRI Brain", "CT abdomen", "biopsy", "urine culture", "blood grouping patient"],
        "recovery_template": None,
    },
    {
        "code": "DRUG",
        "display_name": "Drug / Medicine",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Medicines, IV fluids, injections, blood products dispensed by the hospital pharmacy.",
        "llm_examples": ["Ceftriaxone injection", "Paracetamol", "NS 500ml", "saline drip", "blood transfusion"],
        "recovery_template": None,
    },
    {
        "code": "IMPLANT",
        "display_name": "Implant / Prosthesis",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Surgical implants, prosthetics, and intraocular lenses.",
        "llm_examples": ["coronary stent", "knee prosthesis", "IOL", "pacemaker", "orthopedic plate"],
        "recovery_template": None,
    },
    {
        "code": "PROCEDURE",
        "display_name": "Procedure / Surgery",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Surgery charges, OT fees, anaesthesia, ICU monitoring, physiotherapy, dialysis.",
        "llm_examples": [
            "OT charges", "surgeon fee", "anaesthesia", "ICU monitoring",
            "dialysis", "chemotherapy", "physiotherapy",
        ],
        "recovery_template": None,
    },
    {
        "code": "ROOM_RENT",
        "display_name": "Room Rent / Accommodation",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Room, bed, ward, or accommodation charges including ICU.",
        "llm_examples": ["room rent", "bed charge", "ICU charges", "single room", "general ward"],
        "recovery_template": None,
    },
    {
        "code": "CONSUMABLE",
        "display_name": "Consumable / Disposable",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Single-use disposable items billed separately from procedures.",
        "llm_examples": ["gloves", "syringes", "IV cannula", "bandage", "gauze", "OT kit", "urine bag", "ECG electrodes", "trolley cover", "kidney tray", "splint", "cold pack", "sanitary pad", "delivery kit"],
        "recovery_template": (
            "Ask the hospital billing desk to bundle consumable costs into the "
            "procedure/surgery package charges. Itemized consumables are excluded "
            "under IRDAI Circular IRDAI/HLT/REG/CIR/193/07/2020."
        ),
    },
    {
        "code": "ADMIN",
        "display_name": "Administrative Fee",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Registration, admission, discharge, file, and paperwork fees.",
        "llm_examples": ["registration fee", "admission charges", "discharge fee", "file charge", "documentation", "birth certificate", "courier charges", "mortuary charges", "photocopies charges", "conveyance charges"],
        "recovery_template": (
            "Administrative charges such as registration, file, and discharge fees "
            "are not claimable. Remove these from the insurance claim submission."
        ),
    },
    {
        "code": "NON_MEDICAL",
        "display_name": "Non-Medical / Personal Comfort",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Food, beverages, personal comfort items, telephone, TV, laundry.",
        "llm_examples": ["meal charges", "diet food", "TV rental", "telephone", "laundry", "toiletries", "baby food", "mineral water", "internet charges", "diaper", "sugar free tablets", "beauty services"],
        "recovery_template": (
            "Personal comfort items (food, telephone, TV, laundry) are not covered. "
            "Pay these directly and do not include in the insurance claim."
        ),
    },
    {
        "code": "ATTENDANT",
        "display_name": "Attendant / Bystander",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Attendant, bystander, companion, and private nurse charges.",
        "llm_examples": ["attendant charge", "bystander fee", "companion fee", "ayah charges"],
        "recovery_template": "Attendant/bystander charges are not covered. Remove from claim.",
    },
    {
        "code": "EQUIPMENT_RENTAL",
        "display_name": "Equipment Rental",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "External equipment hire billed separately from procedure or room charges.",
        "llm_examples": ["nebulizer rental", "CPAP hire", "monitor rental", "wheelchair rental", "BiPAP", "cervical collar", "knee immobilizer", "lumbo sacral belt", "spacer", "spirometer", "steam inhaler", "arm sling"],
        "recovery_template": (
            "External equipment rental charges are excluded. If the equipment was "
            "medically essential (e.g., ICU ventilator), request the hospital to "
            "bill it as part of ICU/room charges."
        ),
    },
    {
        "code": "EXTERNAL_PHARMACY",
        "display_name": "External Pharmacy",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Medicines purchased from outside the hospital pharmacy.",
        "llm_examples": ["outside pharmacy", "retail pharmacy bill", "medicine from outside"],
        "recovery_template": (
            "Medicines purchased from outside the hospital pharmacy are not payable "
            "unless accompanied by a valid prescription and emergency justification."
        ),
    },
    {
        "code": "COSMETIC",
        "display_name": "Cosmetic Procedure",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Cosmetic surgery, aesthetic procedures, anti-aging treatments.",
        "llm_examples": ["botox", "liposuction", "rhinoplasty cosmetic", "breast augmentation"],
        "recovery_template": (
            "Cosmetic procedures are explicitly excluded under all Indian health "
            "insurance policies. This cannot be claimed."
        ),
    },
    {
        "code": "UNCLASSIFIED",
        "display_name": "Unclassified",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Item that could not be assigned to a known category.",
        "llm_examples": [],
        "recovery_template": "Remove this item from the insurance claim or consult your TPA.",
    },
    {
        "code": "MODERN_TREATMENT",
        "display_name": "Modern / Technology Treatment",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Robotic, laser, or tech-intensive procedures that some insurers cap.",
        "llm_examples": ["robotic surgery", "laser surgery", "robot assisted"],
        "recovery_template": "Check your policy for sub-limits on modern/technology treatments.",
    },
    {
        "code": "CATARACT_PACKAGE",
        "display_name": "Cataract Surgery Package",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Cataract (phacoemulsification) surgery package including IOL implant.",
        "llm_examples": ["cataract surgery", "phacoemulsification", "IOL implant", "intraocular lens"],
        "recovery_template": None,
    },
    {
        "code": "CONSUMABLE_OVERRIDE",
        "display_name": "Consumable (Insurer Override)",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Consumable covered by insurer-specific plan (overrides IRDAI exclusion).",
        "llm_examples": ["gloves", "syringe", "disposable", "surgical gloves"],
        "recovery_template": None,
    },
    {
        "code": "CONSUMABLE_SUBLIMIT",
        "display_name": "Consumable (Sub-limit Applies)",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Consumable allowed with an aggregate sub-limit cap.",
        "llm_examples": ["consumables", "disposables"],
        "recovery_template": "Consumables are covered up to a sub-limit. Verify remaining cap with TPA.",
    },
    {
        "code": "PHARMACY_COPAY",
        "display_name": "Pharmacy (Co-pay Applicable)",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Pharmacy charges subject to a co-payment under specific plans.",
        "llm_examples": ["pharmacy", "medicines", "drugs", "medication"],
        "recovery_template": "A co-payment applies on pharmacy/medicine charges under this plan.",
    },
    {
        "code": "ROOM_UPGRADE_COPAY",
        "display_name": "Room Upgrade (Co-pay)",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": "Room category upgrade charge subject to a co-payment.",
        "llm_examples": ["room upgrade", "room category upgrade", "higher room"],
        "recovery_template": "A co-payment applies on room upgrade charges under this plan.",
    },
    {
        "code": "SURGEON_CONSULTATION",
        "display_name": "Surgeon / Specialist Consultation",
        "never_excluded": True,
        "is_payable_by_default": True,
        "description": "Surgeon or specialist consultation fees, sometimes capped by insurers.",
        "llm_examples": ["surgeon consultation", "specialist visit", "consultant charges"],
        "recovery_template": "Surgeon consultation fees may be capped under your plan.",
    },
    {
        "code": "OPD",
        "display_name": "OPD Consultation",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Outpatient department charges billed during hospitalisation or as "
            "standalone OPD visits covered by a plan or rider."
        ),
        "llm_examples": [
            "OPD consultation", "outpatient visit", "clinic visit charge",
            "doctor visit fee", "follow-up consultation",
        ],
        "recovery_template": (
            "OPD charges are not covered under standard inpatient hospitalisation "
            "policies. Check whether your plan includes an OPD benefit rider."
        ),
    },
    {
        "code": "CONSULTATION",
        "display_name": "Doctor Consultation Fee",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Specialist or GP consultation fees billed as a separate line item "
            "outside of a surgical procedure or OT charge."
        ),
        "llm_examples": [
            "consultation fee", "doctor fee", "specialist fee", "visiting charge",
            "surgeon consultation", "physician fee",
        ],
        "recovery_template": (
            "Standalone consultation fees are not payable unless your policy "
            "includes a consultation benefit or OPD rider."
        ),
    },
    {
        "code": "MATERNITY",
        "display_name": "Maternity / Obstetric",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Maternity, obstetric, antenatal, or postnatal charges billed during "
            "the hospitalisation episode."
        ),
        "llm_examples": [
            "maternity charges", "antenatal care", "postnatal care",
            "obstetric fee", "prenatal visit", "ante natal",
        ],
        "recovery_template": (
            "Maternity charges are covered only under plans or riders with an "
            "explicit maternity benefit. Check your policy schedule."
        ),
    },
    {
        "code": "DELIVERY",
        "display_name": "Delivery / Labour Room",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Delivery charges, labour room fees, C-section or normal delivery "
            "procedure costs."
        ),
        "llm_examples": [
            "delivery charges", "labour room", "normal delivery", "C-section",
            "caesarean", "LSCS charges", "labour charge",
        ],
        "recovery_template": (
            "Delivery and labour room charges require a maternity benefit rider "
            "or a maternity-inclusive plan. Verify with your insurer."
        ),
    },
    {
        "code": "CRITICAL_ILLNESS",
        "display_name": "Critical Illness",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Charges or benefit triggers associated with critical illness conditions "
            "such as cancer, stroke, or heart attack."
        ),
        "llm_examples": [
            "critical illness", "cancer treatment", "stroke rehabilitation",
            "organ failure", "cardiac arrest management",
        ],
        "recovery_template": (
            "Critical illness benefits are lump-sum payouts triggered by diagnosis "
            "of a listed condition. Verify your CI rider or plan schedule."
        ),
    },
    {
        "code": "DENTAL",
        "display_name": "Dental Treatment",
        "never_excluded": False,
        "is_payable_by_default": False,
        "description": (
            "Dental procedure charges billed during hospitalisation or as standalone "
            "dental treatment under a dental rider."
        ),
        "llm_examples": [
            "dental extraction", "tooth removal", "scaling", "root canal",
            "dental surgery", "wisdom tooth", "dental charges",
        ],
        "recovery_template": (
            "Dental charges are excluded from standard hospitalisation cover. "
            "Check whether your plan includes a dental benefit rider."
        ),
    },
]
