"""Reference seed payload for diagnosis overrides and synonym groups."""

DOMAIN = "diagnosis"

DIAGNOSIS_OVERRIDES = [
    {
        "diagnosis_keyword": "cataract",
        "item_category": "PROCEDURE",
        "item_keywords": ["phaco", "phacoemulsification", "phaco machine", "iol", "intraocular lens", "lens implant"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Phacoemulsification (phaco machine) charges for cataract surgery are payable "
            "as part of the procedure cost per IRDAI circular on day-care procedures."
        ),
        "notes": "Ensure billing is done as cataract package for full payability.",
    },
    {
        "diagnosis_keyword": "knee replacement",
        "item_category": "IMPLANT",
        "item_keywords": ["implant", "knee implant", "prosthesis", "knee prosthesis", "tibial component", "femoral component"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Orthopedic implants (knee prosthesis) for knee replacement surgery are payable "
            "as medical devices integral to the procedure. Pre-authorization required."
        ),
        "notes": "Pre-authorization mandatory. Ensure original invoice from implant manufacturer is attached.",
    },
    {
        "diagnosis_keyword": "hip replacement",
        "item_category": "IMPLANT",
        "item_keywords": ["implant", "hip implant", "prosthesis", "hip prosthesis", "acetabular cup", "femoral stem"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": "Hip replacement implants are payable per IRDAI implant coverage guidelines.",
        "notes": "Pre-authorization required. Original implant invoice mandatory.",
    },
    {
        "diagnosis_keyword": "cardiac",
        "item_category": "IMPLANT",
        "item_keywords": ["stent", "coronary stent", "drug eluting stent", "bare metal stent", "cardiac stent"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Coronary stents are payable as part of cardiac procedures. "
            "However, pre-authorization is mandatory for planned cardiac procedures."
        ),
        "notes": "Pre-authorization required. NPPA capped stent prices apply.",
    },
    {
        "diagnosis_keyword": "bypass",
        "item_category": "IMPLANT",
        "item_keywords": ["stent", "coronary stent", "graft", "bypass graft"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": "Bypass graft and stent are payable under cardiac surgery coverage.",
        "notes": "Pre-auth mandatory. Document procedure type clearly.",
    },
    {
        "diagnosis_keyword": "accident",
        "item_category": "CONSUMABLE",
        "item_keywords": ["suture", "sutures", "wound care", "wound dressing", "emergency dressing"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "In accident/emergency context, sutures and wound care consumables are payable "
            "as they are medically essential for the emergency treatment."
        ),
        "notes": "Document accident nature in discharge summary for smooth reimbursement.",
    },
    {
        "diagnosis_keyword": "trauma",
        "item_category": "CONSUMABLE",
        "item_keywords": ["suture", "sutures", "wound care", "wound dressing", "emergency consumable"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": "Trauma emergency consumables are payable due to emergency medical necessity.",
        "notes": "Attach emergency certificate from treating doctor.",
    },
    {
        "diagnosis_keyword": "dialysis",
        "item_category": "CONSUMABLE",
        "item_keywords": ["dialysis consumable", "dialyzer", "tubing", "bicarbonate", "heparin"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Consumables used during dialysis sessions are payable as medically necessary "
            "items under the day-care procedure exception."
        ),
        "notes": "Dialysis is covered as a day-care procedure. Consumables included.",
    },
    {
        "diagnosis_keyword": "chemotherapy",
        "item_category": "CONSUMABLE",
        "item_keywords": ["chemotherapy consumable", "chemo consumable", "iv set", "infusion set", "chemo kit"],
        "override_status": "PAYABLE",
        "payable_pct": 100.0,
        "reason": (
            "Consumables used during chemotherapy administration are payable as they "
            "are integral to the cancer treatment procedure."
        ),
        "notes": "Covered under day-care procedure. Oncology report required.",
    },
]

DIAGNOSIS_SYNONYM_GROUPS = [
    {
        "base_term": "myocardial infarction",
        "synonyms": ["mi", "heart attack", "acute coronary syndrome", "acs"],
    },
    {
        "base_term": "coronary artery disease",
        "synonyms": ["cad", "ischemic heart disease", "ihd"],
    },
    {
        "base_term": "knee replacement",
        "synonyms": ["tkr", "total knee replacement", "total knee arthroplasty", "tka"],
    },
    {
        "base_term": "hip replacement",
        "synonyms": ["thr", "total hip replacement", "total hip arthroplasty", "tha"],
    },
    {
        "base_term": "cataract",
        "synonyms": ["phaco", "phacoemulsification", "lens opacity"],
    },
    {
        "base_term": "dialysis",
        "synonyms": ["hemodialysis", "haemodialysis", "hd"],
    },
    {
        "base_term": "chemotherapy",
        "synonyms": ["chemo", "oncology infusion"],
    },
    {
        "base_term": "accident",
        "synonyms": ["rta", "road traffic accident", "trauma"],
    },
]
