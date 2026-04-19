# IRDAI Exclusion Rules — Reference Seed Spec

**Seed file:** `seeds/reference/irdai_exclusions.py`  
**Domain:** `irdai_exclusions`  
**Governing circular:** IRDAI/HLT/REG/CIR/193/07/2020  
**Applies to:** All insurers (no `insurer_code` filter)

---

## Purpose

These rules define the set of line-item categories that are universally excluded from
health insurance payouts in India regardless of the insurer, plan, or policyholder. They
are mandated by the IRDAI circular above and cannot be overridden by any insurer seed.

At runtime, `step1_universal.py` queries `exclusion_rules WHERE applies_to_all = true`
and applies them before any insurer-specific logic runs.

---

## How to Update

1. Edit `seeds/reference/irdai_exclusions.py`.
2. Change keywords or rejection_reason text as needed.
3. Run dry-run to validate: `python seeds/runner.py --domain irdai_exclusions --dry-run`
4. Apply to DB: `python seeds/runner.py --domain irdai_exclusions`

The upsert strategy is **DELETE + INSERT** scoped to `applies_to_all = true` rows, so
every run is fully idempotent.

> **Do not edit the historical Alembic migration (002).** It is bootstrap-only. The seed
> file is the canonical, living source for these rules.

---

## Category Reference

| Category | `item_category` code | IRDAI Basis |
|---|---|---|
| Consumables & disposables | `CONSUMABLE` | Circular 193/2020, Annexure I |
| Administrative charges | `ADMIN` | Circular 193/2020, Annexure I |
| Non-medical / comfort items | `NON_MEDICAL` | Circular 193/2020, Annexure I |
| Attendant / bystander charges | `ATTENDANT` | Circular 193/2020, Annexure I |
| Equipment rental | `EQUIPMENT_RENTAL` | Circular 193/2020, Annexure I |
| Cosmetic procedures | `COSMETIC` | Standard policy exclusion |
| External pharmacy bills | `EXTERNAL_PHARMACY` | Circular 193/2020, Annexure I |

---

## Rule Data Shape

Each entry in `EXCLUSION_RULES` maps to a row in the `exclusion_rules` table:

| Field | Type | Description |
|---|---|---|
| `category` | `str` | FK to `item_categories.code` |
| `keywords` | `list[str]` | Case-insensitive keyword list used by the rule engine |
| `rejection_reason` | `str` | Human-readable reason shown in analysis output |
| `source_circular` | `str` | IRDAI circular reference |
| `applies_to_all` | `bool` | Always `True` for this domain — seeds WHERE clause depends on this |

---

## Keyword Management

### Adding a keyword
Append to the `keywords` list for the relevant category. Keywords are matched
case-insensitively by the rule engine. Use the most specific term possible to avoid
false positives.

### Removing a keyword (migration 007 precedent)
Migration 007 removed `"tube"` and `"kit"` from the `CONSUMABLE` keyword list because
they matched legitimate payable items (e.g., chest tube, cardiac stent kit). This pattern
should guide any future keyword narrowing — if a keyword causes false rejections on
otherwise payable items, remove it and handle those items via `diagnosis_overrides` if needed.

### Keywords NOT included (intentional gaps)
The following terms were reviewed and excluded to prevent false positives:

| Term | Reason omitted |
|---|---|
| `tube` | Too generic — matches chest tube (payable), NG tube (payable) |
| `kit` | Too generic — matches surgical kit (payable), procedure packs |
| `bandage` | Retained; always a consumable unless diagnosis override applies |

---

## Interaction with Other Domains

| Scenario | How it resolves |
|---|---|
| Item matches CONSUMABLE keywords but diagnosis is knee surgery | `diagnosis_overrides` (seeded by `diagnosis.py`) intercepts first — implant/prosthesis overrides run before exclusion rules |
| Item is consumable but patient has a Consumable Cover rider | `step5b_riders.py` checks rider coverage and overrides the exclusion verdict post step1 |
| Item matches COSMETIC keywords but is reconstructive | No automatic override — must be manually adjudicated; no rule engine bypass exists today |
| External pharmacy bill with valid prescription | `EXTERNAL_PHARMACY` rejection stands; manual TPA review is required |

---

## Validation

The runner validates each exclusion rule's `category` against `item_categories.code`
before any DB write. If the category code does not exist in the `item_categories` seed,
the run is aborted with a descriptive error.

Run validation without DB writes:

```bash
cd apps/api
python seeds/runner.py --domain irdai_exclusions --dry-run
```

Expected output: `Dry-run: 1 reference domain(s) and 0 insurer module(s) validated successfully.`

---

## Migration History

| Migration | Change |
|---|---|
| `002_seed_irdai_rules.py` | Original bootstrap — seeded all 7 exclusion categories |
| `007_fix_consumable_keywords.py` | Removed `"tube"` and `"kit"` from CONSUMABLE keywords to reduce false positives |

Both migrations are now **read-only history**. `irdai_exclusions.py` is the forward source
of truth and already incorporates the migration 007 fix.
