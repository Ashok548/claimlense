# Refactor Blueprint: Truly Config-Driven Policy Engine

Status: Ready for implementation  
Derived from: CONFIG_DRIVEN_ARCHITECTURE_AUDIT.md  
Target outcome: Add any new insurer with zero Python changes — INSERT rows only.

---

## 0. Design Principles

1. Every policy decision that can vary between insurers lives in a DB row, not a Python branch.
2. The engine loads all config at the start of each request and passes it through generic evaluators.
3. Category taxonomy is a single authoritative table; nothing outside it is allowed.
4. Keyword lists are named, versioned DB records — not Python constants.
5. Rider logic is a set of coverage clauses, not a set of boolean columns.
6. Recovery guidance text lives in DB rows — no hardcoded strings.
7. LLM is categorization only; the taxonomy and prompt are seeded from DB.

---

## 1. Implementation Phases

```
Phase 1 — Keyword sets + recovery templates  (non-breaking, additive)
Phase 2 — Room-rent config table             (replaces hardcoded keywords + deduction logic)
Phase 3 — Billing-mode rules table           (replaces step3_billing constants)
Phase 4 — Rider coverage clauses             (replaces boolean columns)
Phase 5 — Taxonomy unification               (fixes insurer rule category mismatch)
Phase 6 — Admin REST API                     (GUI/API onboarding surface)
```

Each phase produces one Alembic migration and modifies only its paired step file.
No phase breaks existing data or API contracts.

---

## 2. New Database Tables

### 2.1 `keyword_sets`

Replaces all hardcoded Python keyword lists.

```sql
CREATE TABLE keyword_sets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL UNIQUE,   -- e.g. "ROOM_RENT_DETECTION"
    keywords    TEXT[]       NOT NULL,
    description TEXT,
    is_system   BOOLEAN      NOT NULL DEFAULT false,  -- system sets cannot be deleted
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

Built-in seeds (run once in migration, never change via application code):

| name                         | purpose                                              |
|------------------------------|------------------------------------------------------|
| ROOM_RENT_DETECTION          | ward/accommodation keywords for step4               |
| ICU_DETECTION                | ICU/ICCU/HDU/NICU/PICU keywords for step4           |
| CONSUMABLE_BILLING_MODE      | consumable keywords used by step3 fallback          |
| MATERNITY_DETECTION          | obstetric keywords used by step5b fallback          |
| STEP0_CONSUMABLE_EXAMPLES    | consumable examples fed into the Step 0 LLM prompt  |
| STEP0_DIAGNOSTIC_EXAMPLES    | diagnostic examples fed into Step 0 prompt          |

New insurers can add their own keyword sets (is_system = false) if they need to detect categories that don't fit the global sets.

---

### 2.2 `item_categories`

Single authoritative category registry. Replaces the scattered enum/list in schemas.py, step0_categorize.py, and step1_universal.py.

```sql
CREATE TABLE item_categories (
    code             VARCHAR(50) PRIMARY KEY,  -- e.g. "CONSUMABLE"
    display_name     VARCHAR(100) NOT NULL,
    description      TEXT,
    never_excluded   BOOLEAN NOT NULL DEFAULT false,   -- safe-list for step1
    is_payable_by_default BOOLEAN NOT NULL DEFAULT false,
    llm_examples     TEXT[],    -- fed into Step 0 system prompt
    recovery_template TEXT,     -- fed into step1 recovery action
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Seeded rows replace:
- `_NEVER_EXCLUDED_CATEGORIES` set in step1_universal.py
- `_recovery_action()` dict in step1_universal.py
- `VALID_CATEGORIES` set in step0_categorize.py
- Step 0 `SYSTEM_PROMPT` category list

Step 0 builds its prompt dynamically by querying this table. Step 1 loads the never_excluded set from it. Adding a new category is a single INSERT.

---

### 2.3 `room_rent_config`

Replaces `ROOM_RENT_KEYWORDS`, `ICU_KEYWORDS`, and the deduction assumptions in step4_room_rent.py.

```sql
CREATE TABLE room_rent_config (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer_id              UUID REFERENCES insurers(id),   -- NULL = global default
    plan_codes              TEXT[],                         -- NULL = all plans
    detection_kw_set_id     UUID NOT NULL REFERENCES keyword_sets(id),
    icu_kw_set_id           UUID NOT NULL REFERENCES keyword_sets(id),
    deduction_method        VARCHAR(30) NOT NULL DEFAULT 'proportional',
        -- 'proportional' : deduction_ratio = limit / billed, applied across all items
        -- 'room_only'    : cap room rent only, no spillover to other items
        -- 'none'         : no deduction (insurer absorbs excess)
    icu_deduction_separate  BOOLEAN NOT NULL DEFAULT true,
        -- true  = ICU ratio tracked independently from ward ratio
        -- false = single worst ratio applied to entire claim
    priority                INT NOT NULL DEFAULT 0
        -- higher priority row wins when multiple rows match
);
```

Global default row uses the current keyword lists as seeds.
Insurer or plan-specific rows can override detection keywords or deduction behavior.
Step 4 loads the matching config row instead of reading Python constants.

---

### 2.4 `billing_mode_rules`

Replaces `CONSUMABLE_KEYWORDS` and the billing mode branch logic in step3_billing.py.

```sql
CREATE TABLE billing_mode_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer_id      UUID REFERENCES insurers(id),  -- NULL = universal
    plan_codes      TEXT[],
    item_category   VARCHAR(50) REFERENCES item_categories(code),
    billing_mode    billing_mode NOT NULL,           -- itemized | package | mixed
    verdict         payability_status NOT NULL,
    payable_pct     NUMERIC(5,2),
    reason          TEXT NOT NULL,
    recovery        TEXT,
    fallback_kw_set_id  UUID REFERENCES keyword_sets(id),
        -- used when item is UNCLASSIFIED; keywords from this set trigger this rule
    priority        INT NOT NULL DEFAULT 0
);
```

The four scenarios that step3_billing.py currently handles via code become rows:

| item_category | billing_mode | verdict           | notes                                |
|---------------|--------------|-------------------|--------------------------------------|
| CONSUMABLE    | package      | PAYABLE           | consumable absorbed into package     |
| CONSUMABLE    | itemized     | NOT_PAYABLE       | default IRDAI exclusion applies      |
| CONSUMABLE    | mixed        | VERIFY_WITH_TPA   | ambiguous — TPA must confirm         |
| CONSUMABLE    | package      | PAYABLE           | keyword fallback for UNCLASSIFIED    |

Insurer-specific rows can override: e.g. Insurer X treats all itemized consumables as VERIFY_WITH_TPA instead of NOT_PAYABLE.

---

### 2.5 `rider_coverage_clauses`

Replaces the five hardcoded booleans on the `riders` table and the fixed rescue branches in step5b_riders.py.

```sql
CREATE TABLE rider_coverage_clauses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rider_id            UUID NOT NULL REFERENCES riders(id) ON DELETE CASCADE,
    -- which item categories / keywords this clause covers
    target_categories   TEXT[] NOT NULL,   -- canonical codes from item_categories
    fallback_kw_set_id  UUID REFERENCES keyword_sets(id),
        -- keyword fallback for UNCLASSIFIED items; NULL = category-match only
    -- what the clause does
    verdict             payability_status NOT NULL DEFAULT 'PAYABLE',
    payable_pct         NUMERIC(5,2),
    -- guardrails
    only_rescues_status VARCHAR(30)[] NOT NULL DEFAULT ARRAY['NOT_PAYABLE'],
        -- this clause fires only when the current status is in this list
        -- prevents riders from overriding deliberate partial payouts
    -- tracking
    priority            INT NOT NULL DEFAULT 0,
        -- lower = evaluated first; allows per-insurer ordering of clauses
    reason_template     TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Migration seeds translate existing rider boolean columns → clause rows:

```
covers_consumables = true
  → rider_coverage_clauses(target_categories=['CONSUMABLE','CONSUMABLE_OVERRIDE'], verdict='PAYABLE', ...)

covers_opd = true
  → rider_coverage_clauses(target_categories=['OPD','CONSULTATION'], verdict='PAYABLE', ...)

covers_maternity = true
  → rider_coverage_clauses(target_categories=['MATERNITY','DELIVERY'],
                            fallback_kw_set_id = <MATERNITY_DETECTION set>, verdict='PAYABLE', ...)
```

After migration the boolean columns are deprecated (kept for one release, then dropped).
A new rider with `covers_dental` is now added by inserting a row with `target_categories=['DENTAL']` — no code change.

---

### 2.6 Canonical category map for `insurer_rules`

This is not a new table. It is a data migration + a code fix.

Problem: `insurer_rules.item_category` currently uses ad hoc values like `MODERN_TREATMENT`, `CATARACT_PACKAGE`, `CONSUMABLE_OVERRIDE` that do not exist in the Step 0 taxonomy, so category-matched lookup always fails for classified items.

Fix:
1. Add those custom category codes to `item_categories` so they are valid canonical tokens.
2. Remap the seeded insurer rules to use canonical codes or a structured keyword-plus-category approach.
3. step5_insurer.check_insurer_rules already does category equality match; this fix makes it reliable.

---

## 3. Engine Loading Changes

Current `engine.py` pre-loads:
```python
universal_rules = await load_universal_exclusion_rules(db)
diagnosis_overrides = await load_diagnosis_overrides(db)
insurer_rules = await load_insurer_rules(insurer.id, db)
sublimit_rules = await load_sublimit_rules(insurer.id, db)
```

After the refactor, add:
```python
# new config loads
item_categories = await load_item_categories(db)             # replaces _NEVER_EXCLUDED_CATEGORIES
billing_mode_rules = await load_billing_mode_rules(          # replaces CONSUMABLE_KEYWORDS in step3
    db, insurer_id=insurer.id, plan_code=request.plan_code
)
room_rent_cfg = await load_room_rent_config(                 # replaces ROOM_RENT_KEYWORDS in step4
    db, insurer_id=insurer.id, plan_code=request.plan_code
)
rider_clauses = await load_rider_clauses(db, rider_ids=[r.id for r in riders])  # replaces boolean checks
```

Each loader returns a list of ORM rows, same pattern as the existing loaders.
The loaders are dead-simple `SELECT * WHERE insurer_id = X ORDER BY priority` queries.

---

## 4. Per-Step Code Changes

### Step 0 — `step0_categorize.py`

**Before:** `SYSTEM_PROMPT` is a hardcoded 50-line string with category names and examples.

**After:**

```python
async def build_step0_prompt(db: AsyncSession) -> str:
    """Build the Step 0 categorization prompt from the item_categories table."""
    cats = await db.execute(select(ItemCategory).order_by(ItemCategory.code))
    lines = []
    for cat in cats.scalars():
        examples = ", ".join(cat.llm_examples[:5]) if cat.llm_examples else "—"
        lines.append(f"- {cat.code}: {examples}")
    category_block = "\n".join(lines)
    return STEP0_PROMPT_TEMPLATE.replace("{CATEGORIES}", category_block)
```

`STEP0_PROMPT_TEMPLATE` is a short string in config.py with a `{CATEGORIES}` slot.
Prompt regenerated each call (cached per worker startup is fine).
Adding a new category = one row in `item_categories`, zero code.

---

### Step 1 — `step1_universal.py`

**Before:**
```python
_NEVER_EXCLUDED_CATEGORIES = {"DIAGNOSTIC_TEST", "IMPLANT", "PROCEDURE", "ROOM_RENT", "DRUG"}

def _recovery_action(category: str) -> str:
    actions = {
        "CONSUMABLE": "Ask the hospital billing desk to bundle ...",
        "ADMIN": "Administrative charges ...",
        ...
    }
    return actions.get(category, "Remove this item ...")
```

**After:**
- Drop both constants.
- `check_universal_exclusions` accepts `item_categories: dict[str, ItemCategory]` (code → row) loaded by engine.
- The never-exit check becomes: `if item_categories.get(item_category, ItemCategory()).never_excluded: return None`
- Recovery text: `rule.rejection_reason` stays. Recovery action: `item_categories[cat].recovery_template`
- Adding a new IRDAI exclusion category with custom recovery text = one INSERT into `item_categories`.

---

### Step 3 — `step3_billing.py`

**Before:** CONSUMABLE_KEYWORDS hardcoded list + `check_billing_mode()` with embedded branch logic.

**After:**

```python
def check_billing_mode(
    item: BillItemInput,
    billing_mode: BillingMode,
    billing_mode_rules: list[BillingModeRule],   # NEW: loaded from DB by engine
    item_category: str | None = None,
) -> AnalyzedLineItem | None:
    desc_lower = item.description.lower()
    for rule in sorted(billing_mode_rules, key=lambda r: -r.priority):
        if rule.billing_mode != billing_mode.value:
            continue
        # Category match path
        if item_category and item_category == rule.item_category:
            return _build_result(item, rule, rule_matched=f"BILLING:{rule.item_category}:CATEGORY")
        # Keyword fallback path (only for UNCLASSIFIED)
        if not item_category or item_category == "UNCLASSIFIED":
            if rule.fallback_kw_set and any(kw in desc_lower for kw in rule.fallback_kw_set.keywords):
                return _build_result(item, rule, rule_matched=f"BILLING:{rule.item_category}:KW")
    return None
```

No insurer name appears. No billing-mode enum checked in an if statement. Logic is entirely driven by priority-ordered rows.

---

### Step 4 — `step4_room_rent.py`

**Before:** `ROOM_RENT_KEYWORDS` and `ICU_KEYWORDS` as module-level Python sets.

**After:**

```python
def is_room_rent_item(description: str, room_rent_cfg: RoomRentConfig) -> bool:
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in room_rent_cfg.detection_keyword_set.keywords)

def is_icu_item(description: str, room_rent_cfg: RoomRentConfig) -> bool:
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in room_rent_cfg.icu_keyword_set.keywords)

def check_room_rent(
    item: BillItemInput,
    room_rent_limit: float | None,
    icu_days: int | None,
    general_ward_days: int | None,
    icu_room_rent_limit: float | None = None,
    room_rent_cfg: RoomRentConfig | None = None,   # NEW
) -> tuple[AnalyzedLineItem | None, float, bool]:
    cfg = room_rent_cfg or _global_default_config()
    if not is_room_rent_item(item.description, cfg):
        return None, 1.0, False
    icu_item = is_icu_item(item.description, cfg)
    ...
    # deduction_method from cfg determines whether spillover applies
    if cfg.deduction_method == "room_only":
        return result, 1.0, icu_item   # no spillover regardless of cap
    ...
```

A new insurer that does not want proportional spillover deduction? Add a row with `deduction_method = 'room_only'`. Zero code.

---

### Step 5b — `step5b_riders.py`

**Before:**
```python
CONSUMABLE_CATEGORIES = ["CONSUMABLE", "CONSUMABLE_OVERRIDE", "CONSUMABLE_SUBLIMIT"]
OPD_CATEGORIES = ["OPD", "CONSULTATION"]
MATERNITY_CATEGORIES = ["MATERNITY", "DELIVERY"]
MATERNITY_KEYWORDS = ["maternity", "delivery", "c-section", ...]

if is_consumable:
    if plan.consumables_covered:
        ...
    for rider in _ordered_riders(riders):
        if rider.covers_consumables:
            ...
if is_opd:
    for rider in _ordered_riders(riders):
        if rider.covers_opd:
            ...
```

**After:** All category sets, keyword lists, and capability checks replaced by iterating loaded clauses.

```python
def check_rider_and_plan_coverage(
    item: BillItemInput,
    current_result: AnalyzedLineItem | None,
    plan: Plan,
    riders: list[Rider],
    rider_clauses: list[RiderCoverageClause],   # NEW: loaded by engine
    item_category: str | None = None,
    rider_remaining: dict[uuid.UUID, float | None] | None = None,
) -> AnalyzedLineItem | None:
    if current_result is None:
        return None

    # Guard: never override a deliberate insurer partial payout
    if (
        current_result.status == PayabilityStatus.PARTIALLY_PAYABLE
        and current_result.confidence_basis == ConfidenceBasis.INSURER_RULE
    ):
        return current_result

    desc_lower = item.description.lower()
    for clause in sorted(rider_clauses, key=lambda c: c.priority):
        # Category match
        if item_category and item_category in clause.target_categories:
            matched = True
        # Keyword fallback for UNCLASSIFIED
        elif clause.fallback_kw_set and (
            not item_category or item_category == "UNCLASSIFIED"
        ):
            matched = any(kw in desc_lower for kw in clause.fallback_kw_set.keywords)
        else:
            matched = False
        if not matched:
            continue
        # Guard: only apply when the current status is in the clause's rescue scope
        if current_result.status.value not in clause.only_rescues_status:
            continue
        # Apply the clause
        rider = next((r for r in riders if _clause_belongs_to_rider(clause, r)), None)
        if rider is None:
            continue
        return _apply_rider_with_cap(item, current_result, rider, clause.reason_template, rider_remaining)

    return current_result
```

Entire rider logic becomes: iterate clauses loaded from DB. No hardcoded category names. No boolean columns. A new rider covering DENTAL items = INSERT a rider_coverage_clauses row with `target_categories=['DENTAL']`.

---

## 5. New Alembic Migrations

```
011_keyword_sets_and_item_categories.py
012_room_rent_config.py
013_billing_mode_rules.py
014_rider_coverage_clauses.py
015_backfill_rider_clauses_from_booleans.py
016_taxonomy_unification.py   (remap ad hoc insurer rule categories to canonical codes)
```

Each migration is additive:
- Creates table, seeds rows, does NOT drop existing columns/tables yet.
- New boolean rider columns marked deprecated in a comment; dropped in `017_drop_deprecated.py`.
- All rollback (downgrade) paths documented.

---

## 6. New Insurer Onboarding — After Refactor

Below is the complete SQL needed to add "MAX BUPA HEALTH RECHARGE" as a new insurer.
No Python file is touched. No deployment required if the DB is live.

```sql
-- 1. Insurer master
INSERT INTO insurers (id, code, name, room_rent_default, is_active)
VALUES (gen_random_uuid(), 'MAX_BUPA_RECHARGE', 'Max Bupa Health Recharge', 4500, true);

-- 2. Plan
INSERT INTO plans (
    id, insurer_id, code, name,
    room_rent_limit_abs,   -- ₹4,500 / day
    co_pay_pct,
    consumables_covered,
    is_active
)
SELECT gen_random_uuid(), id, 'RECHARGE_STANDARD', 'Recharge Standard',
       4500.00, 10.00, false, true
FROM insurers WHERE code = 'MAX_BUPA_RECHARGE';

-- 3. Rider: consumables cover, ₹25,000 cap
INSERT INTO riders (
    id, insurer_id, code, name,
    additional_sum_insured, covers_consumables, is_active
)
SELECT gen_random_uuid(), id, 'CONSUMABLE_COVER', 'Consumables Rider', 25000.00, true, true
FROM insurers WHERE code = 'MAX_BUPA_RECHARGE';

-- 4. Rider coverage clause (after Phase 4 migration)
INSERT INTO rider_coverage_clauses (
    id, rider_id, target_categories, verdict,
    only_rescues_status, reason_template, priority
)
SELECT gen_random_uuid(), r.id,
       ARRAY['CONSUMABLE','CONSUMABLE_OVERRIDE'],
       'PAYABLE',
       ARRAY['NOT_PAYABLE'],
       'Rider ''{rider_name}'' covers consumables up to ₹25,000',
       10
FROM riders r
JOIN insurers i ON r.insurer_id = i.id
WHERE i.code = 'MAX_BUPA_RECHARGE' AND r.code = 'CONSUMABLE_COVER';

-- 5. Insurer-specific rules
INSERT INTO insurer_rules (
    id, insurer_id, item_category, keywords, verdict, payable_pct, reason, plan_codes
)
SELECT gen_random_uuid(), i.id,
       'PROCEDURE',
       ARRAY['robotic surgery','robot assisted'],
       'PARTIALLY_PAYABLE', 60.00,
       'Max Bupa Recharge caps robotic surgery at 60% of actual cost.',
       NULL
FROM insurers i WHERE i.code = 'MAX_BUPA_RECHARGE';

-- 6. Sub-limit
INSERT INTO sublimit_rules (id, insurer_id, item_category, plan_codes, max_amount, note)
SELECT gen_random_uuid(), id, 'CONSUMABLE', ARRAY['RECHARGE_STANDARD'], 30000.00,
       'RECHARGE_STANDARD caps consumables at ₹30,000'
FROM insurers WHERE code = 'MAX_BUPA_RECHARGE';

-- Done. The engine can now analyze claims for MAX_BUPA_RECHARGE with no code changes.
```

---

## 7. Four Remaining Hard Limits (Cannot Be Fully Config-Driven)

These require code changes if a new insurer needs them. Track them as known constraints.

| Constraint | What would trigger it | Mitigation |
|---|---|---|
| Custom deduction formulas | Insurer uses slab-based room rent reduction instead of proportional | Add more `deduction_method` enum values + evaluator branches in step4 |
| New confidence/priority model | Insurer requires rule ordering different from the 8-step pipeline | Re-order pipeline steps via a config table (long-term refactor) |
| New LLM prompt structure | Insurer-specific classification quirks | Add `insurer_prompt_overrides` table; inject in step0 |
| New adjudication logic type | e.g., "day-count-based exclusion" | Add a new `clause_type` to billing_mode_rules + step3 evaluator branch |

Each of these becomes a small, bounded code addition when needed — not a rewrite.

---

## 8. File Change Summary

| File | Current state | After refactor |
|---|---|---|
| `step0_categorize.py` | Hardcoded SYSTEM_PROMPT with category list | Prompt built dynamically from `item_categories` table |
| `step1_universal.py` | Hardcoded never-excluded set, hardcoded recovery text | Both loaded from `item_categories` table |
| `step3_billing.py` | Hardcoded CONSUMABLE_KEYWORDS + branch logic | Generic loop over `billing_mode_rules` rows |
| `step4_room_rent.py` | Hardcoded ROOM_RENT_KEYWORDS + ICU_KEYWORDS | Keywords loaded from `room_rent_config` rows |
| `step5b_riders.py` | Hardcoded category sets + boolean column checks | Generic loop over `rider_coverage_clauses` rows |
| `engine.py` | 4 pre-load calls | 8 pre-load calls (4 new config loaders added) |
| `models.py` | Rider has 5 boolean columns | 5 new ORM models added; booleans deprecated |
| `step6_llm.py` | Hardcoded SYSTEM_PROMPT | SYSTEM_PROMPT template with `{CATEGORIES}` slot |

Files **not changed** at all by this refactor:
- `step2_diagnosis.py` — already fully DB-driven
- `step5_insurer.py` — already fully DB-driven (after taxonomy fix in Phase 5)
- `step7_sublimit.py` — already fully DB-driven
- All routes
- All schemas (Pydantic)
- Next.js BFF layer

---

## 9. What Stays in Code by Design

These items are intentionally in code, not config. They are framework-level, not policy.

- The 8-step execution order in `engine.py` — changing step order is an architectural change, not a policy change.
- Confidence scoring constants (0.95, 0.88, etc.) — these are model calibration, not policy.
- Proportional deduction math formula — universal insurance math, not insurer-specific.
- GPT API call structure and retry logic — infrastructure, not policy.
- Pydantic request/response schemas — API contract.
