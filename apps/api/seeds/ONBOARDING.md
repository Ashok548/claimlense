# Seed System

The backend now has two seed layers:

- `seeds/reference/` for global reference data such as IRDA exclusions, keyword sets,
  item categories, room-rent defaults, billing-mode rules, and diagnosis config.
- `seeds/insurers/` for insurer-specific plans, riders, insurer rules, and sublimits.

Run global/reference seeds first, then insurer seeds.

## Common Commands

From `apps/api/`:

```bash
python seeds/runner.py --list
python seeds/runner.py --global-only --dry-run
python seeds/runner.py --global-only
python seeds/runner.py --domain irdai_exclusions
python seeds/runner.py --insurer HDFC_ERGO
python seeds/runner.py
```

`python seeds/runner.py` now seeds reference domains first, then all insurer modules.

# Onboarding a New Insurer

No Python code changes are required. Adding an insurer is entirely a data task.
Follow these steps in order.

---

## What You Need Before Starting

Collect this information from the insurer's policy wordings:

- Insurer full legal name and any short code (e.g. `BAJAJ_ALLIANZ`)
- List of plans offered (names, room rent limits, co-pay %, consumables coverage)
- List of rider add-ons per plan
- Insurer-specific exceptions to IRDAI rules (e.g. consumables covered, modern treatment caps)
- Any per-claim aggregate sub-limits (e.g. "max ₹50,000 for consumables per claim")

---

## Step 1 — Create the seed file

Create `apps/api/seeds/insurers/<insurer_code_lowercase>.py`.

The file is auto-discovered — no registration anywhere else is needed.

Use `hdfc_ergo.py` as the reference. Below is the exact structure with every field
explained.

---

### Section 1 · INSURER

```python
INSURER = {
    "code": "MY_INSURER",          # SCREAMING_SNAKE_CASE, unique across all insurers.
                                   # This is the identifier used in API requests.
    "name": "My Insurer Co. Ltd.", # Full legal name shown to users.
    "logo_url": None,              # Optional. URL to logo image. None is fine.
    "room_rent_default": 3000,     # Fallback room rent cap (₹/day) when plan has no explicit limit.
                                   # Set None if insurer never applies a default.
}
```

---

### Section 2 · PLANS

One dict per plan. A minimum of one plan is required.

```python
PLANS = [
    {
        "code": "PLAN_A",                # SCREAMING_SNAKE_CASE, unique within this insurer.
        "name": "Plan A Gold",           # Human-readable name shown to users.
        "description": "...",            # One-line description. Can be None.

        # ── Room rent limits ───────────────────────────────────────────────────
        # Use EITHER pct OR abs, not both. Set the unused one to None.
        #
        # room_rent_limit_pct:  % of sum insured per day.  e.g. 1.0 means 1%/day.
        # room_rent_limit_abs:  Fixed ₹/day cap.
        # icu_room_rent_limit_abs: Fixed ₹/day cap for ICU/ICCU/HDU/NICU/PICU.
        #   Set None to use the same cap as general ward.
        #
        "room_rent_limit_pct": 1.0,      # e.g. 1% of sum insured per day
        "room_rent_limit_abs": None,
        "icu_room_rent_limit_abs": None,

        # ── Co-payment ────────────────────────────────────────────────────────
        # Global co-pay percentage applied to ALL payable items.
        # 0 means no co-pay. 20.0 means patient pays 20%, insurer pays 80%.
        "co_pay_pct": 0,

        # ── ICU percentage cap (legacy field) ─────────────────────────────────
        # Some older plans cap ICU charges as % of sum insured.
        # Set None unless the policy explicitly states this.
        "icu_limit_pct": None,

        # ── Consumables ───────────────────────────────────────────────────────
        # True  = this plan natively covers ALL consumables (overrides IRDAI exclusion).
        # False = consumables are excluded unless a rider is added.
        "consumables_covered": False,

        # Aggregate cap on consumables payable per claim (₹).
        # None = no cap (all consumables payable up to sum insured).
        "consumables_sublimit": None,
    },
]
```

**Room rent tip:** When room rent exceeds the cap, the engine automatically applies
a proportional deduction to ALL other payable items — this is standard IRDAI practice.
The `deduction_method` can be changed to `"room_only"` or `"none"` in the
`room_rent_config` table via a SQL update if this insurer is an exception.

---

### Section 3 · RIDERS

One dict per rider. If the insurer has no riders, set `RIDERS = []`.

Every rider with a `covers_*` flag set to `True` **must** have a corresponding entry
in its `clauses` list — the system will refuse to deploy otherwise (migration 020).

```python
RIDERS = [
    {
        "code": "CONSUMABLE_COVER",      # SCREAMING_SNAKE_CASE, unique within this insurer.
        "name": "Consumables Cover",     # Human-readable name.
        "description": "...",            # One-line description. Can be None.

        # ── Boolean flags (legacy metadata — still required) ──────────────────
        # These must match what the clauses list actually covers.
        "covers_consumables":     True,
        "covers_opd":             False,
        "covers_maternity":       False,
        "covers_dental":          False,
        "covers_critical_illness": False,

        # ── Clause rows (config-driven path — required for every True flag) ───
        # Each clause = one coverage rule for this rider.
        # Multiple clauses allowed (different categories, different verdicts).
        "clauses": [
            {
                # List of item category codes this clause rescues.
                # Use canonical codes from the table below.
                "target_categories": ["CONSUMABLE"],

                # Name of an existing keyword_set row used as fallback when
                # the LLM returns UNCLASSIFIED for an item.
                # Available sets (seeded in migration 011):
                #   "CONSUMABLE_RIDER_DETECTION"
                #   "OPD_DETECTION"
                #   "MATERNITY_DETECTION"
                # Set None if category-match is always sufficient.
                "fallback_kw_set_name": "CONSUMABLE_RIDER_DETECTION",


                # "PAYABLE" is the only normal value here.
                "verdict": "PAYABLE",

                # Percentage of billed amount to pay. None = 100%.
                "payable_pct": None,

                # Item statuses this clause is allowed to override.
                # "NOT_PAYABLE" = rescue items rejected by IRDAI/insurer rules.
                # "VERIFY_WITH_TPA" = rescue items that needed manual check.
                "only_rescues_status": ["NOT_PAYABLE", "VERIFY_WITH_TPA"],

                # Higher number = evaluated first when multiple riders match.
                "priority": 10,

                # Text shown to the user in the results.
                "reason_template": "Rider 'Consumables Cover' covers consumables",
            }
        ],
    },

    # Rider with NO boolean flags — clauses must be empty list
    {
        "code": "PA_COVER",
        "name": "Personal Accident Cover",
        "description": "Lump sum personal accident benefit.",
        "covers_consumables":     False,
        "covers_opd":             False,
        "covers_maternity":       False,
        "covers_dental":          False,
        "covers_critical_illness": False,
        "clauses": [],             # No clauses needed — no flags are True
    },
]
```

**Canonical target_categories reference:**

| Code | What it covers |
|---|---|
| `CONSUMABLE` | Gloves, syringes, bandages, OT kit, drapes, etc. |
| `OPD` | Outpatient / day-care visits |
| `CONSULTATION` | Doctor consultations |
| `MATERNITY` | Ante/post-natal care |
| `DELIVERY` | Delivery charges, C-section |
| `DENTAL` | Dental procedures |
| `CRITICAL_ILLNESS` | Lump sum on CI diagnosis |
| `DIAGNOSTIC_TEST` | Blood tests, scans, imaging |
| `DRUG` | Medicines, IV fluids |
| `IMPLANT` | Stents, prostheses, IOL |
| `PROCEDURE` | Surgery, OT, anaesthesia fees |
| `ROOM_RENT` | Room/ward/ICU charges |
| `ADMIN` | Registration, discharge fees |
| `NON_MEDICAL` | Food, laundry, telephone |
| `EQUIPMENT_RENTAL` | Nebuliser, CPAP/BiPAP hire |
| `EXTERNAL_PHARMACY` | Outside pharmacy bills |

---

### Section 4 · PLAN_RIDERS

Maps which riders are purchasable for which plans.
Every `(plan_code, rider_code)` pair must reference codes defined above.

```python
PLAN_RIDERS = [
    ("PLAN_A", "CONSUMABLE_COVER"),
    ("PLAN_A", "PA_COVER"),
    ("PLAN_B", "PA_COVER"),
    # Plans that natively cover consumables (consumables_covered=True) should NOT
    # link CONSUMABLE_COVER — it would be a redundant, harmless no-op but is confusing.
]
```

---

### Section 5 · INSURER_RULES

Insurer-specific overrides on top of IRDAI universal exclusions.
Only include rules where this insurer's policy **differs** from the IRDAI default.

Common use cases:
- Insurer covers consumables on a specific plan → `verdict: "PAYABLE"`
- Insurer applies a co-pay on a specific category → `verdict: "PARTIALLY_PAYABLE"` + `payable_pct`
- Insurer extends modern treatments coverage → custom category + `verdict: "PAYABLE"`

```python
INSURER_RULES = [
    {
        # MUST be a canonical category code from the table above.
        # NEVER use pre-016 names like "CONSUMABLE_OVERRIDE" — use "CONSUMABLE".
        "item_category": "CONSUMABLE",

        # Keywords used as fallback when item is UNCLASSIFIED by Step 0.
        # Keep this list tight — overly broad keywords cause false matches.
        "keywords": [
            "gloves", "surgical gloves", "mask", "syringe",
            "gauze", "bandage", "suture", "consumable", "disposable",
        ],

        # "PAYABLE" | "NOT_PAYABLE" | "PARTIALLY_PAYABLE" | "VERIFY_WITH_TPA"
        "verdict": "PAYABLE",

        # Required when verdict is "PARTIALLY_PAYABLE". Percent of billed amount paid.
        # Set None for PAYABLE / NOT_PAYABLE verdicts.
        "payable_pct": 100.0,

        # Reason shown to the user. Be specific — cite the plan name.
        "reason": "Plan A Gold covers consumables — overrides IRDAI exclusion.",

        # Restrict rule to specific plan codes. None = applies to ALL plans.
        "plan_codes": ["PLAN_A"],
    },
]
```

If the insurer has no exceptions to IRDAI defaults:

```python
INSURER_RULES = []
```

---

### Section 6 · SUBLIMIT_RULES (optional)

Per-claim aggregate caps. The engine sums all payable amounts for a category and
cuts the total if it exceeds this cap — even if individual item verdicts say PAYABLE.

```python
SUBLIMIT_RULES = [
    {
        "item_category": "CONSUMABLE",   # Category code to cap
        "max_amount": 50000.0,           # Maximum total payable (₹) per claim
        "note": "IRDAI circular caps consumables at ₹50,000 under this plan",
        "plan_codes": ["PLAN_B"],        # None = applies to all plans
    },
]
```

If no sub-limits apply:

```python
SUBLIMIT_RULES = []
```

---

## Step 2 — Validate the file

From `apps/api/`:

```bash
python seeds/runner.py --dry-run --insurer MY_INSURER
```

This validates structure without touching the database. Fix any errors reported.

---

## Step 3 — Seed the database

```bash
python seeds/runner.py --insurer MY_INSURER
```

The command is safe to run multiple times — all operations are upserts.

To re-seed all insurers at once (e.g. after pulling changes):

```bash
python seeds/runner.py
```

---

## Step 4 — Verify

```bash
python seeds/runner.py --list
```

The insurer code should appear in the output.

Optionally, confirm in the database:

```sql
SELECT code, name FROM insurers WHERE code = 'MY_INSURER';
SELECT code FROM plans WHERE insurer_id = (SELECT id FROM insurers WHERE code = 'MY_INSURER');
SELECT code FROM riders WHERE insurer_id = (SELECT id FROM insurers WHERE code = 'MY_INSURER');
SELECT COUNT(*) FROM rider_coverage_clauses
  WHERE rider_id IN (
    SELECT id FROM riders WHERE insurer_id = (SELECT id FROM insurers WHERE code = 'MY_INSURER')
  );
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Using `CONSUMABLE_OVERRIDE` as `item_category` | Validation error from runner | Change to `CONSUMABLE` |
| Boolean flag is `True` but `clauses` list is empty | Migration 020 aborts deploy | Add a clause row matching the flag |
| `plan_codes` in `PLAN_RIDERS` tuple doesn't match `PLANS` codes | Silent no-op (rider not linked) | Ensure codes match exactly |
| `fallback_kw_set_name` names a keyword set that doesn't exist | Warning in seed log, clause has NULL fallback | Use one of the three built-in names listed above, or set `None` |
| `room_rent_limit_pct` and `room_rent_limit_abs` both set | Pct takes precedence, abs is ignored | Set only one |
| `INSURER_RULES` rule missing `plan_codes` | Rule fires for ALL plans of this insurer | Add `"plan_codes": ["SPECIFIC_PLAN"]` |

---

## Full Minimal Example

```python
# seeds/insurers/acme_health.py

INSURER = {
    "code": "ACME_HEALTH",
    "name": "Acme Health Insurance",
    "logo_url": None,
    "room_rent_default": 3000,
}

PLANS = [
    {
        "code": "SILVER",
        "name": "Silver Plan",
        "description": "Standard plan, room rent capped at ₹3,000/day.",
        "room_rent_limit_pct": None,
        "room_rent_limit_abs": 3000.0,
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
        "description": "Covers consumables billed separately.",
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
]

PLAN_RIDERS = [
    ("SILVER", "CONSUMABLE_COVER"),
]

INSURER_RULES = []

SUBLIMIT_RULES = []
```

Seed it:

```bash
python seeds/runner.py --dry-run --insurer ACME_HEALTH
python seeds/runner.py --insurer ACME_HEALTH
```

Done. The insurer is live — no code deployment required.
