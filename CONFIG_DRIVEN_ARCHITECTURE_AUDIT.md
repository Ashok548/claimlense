# Config-Driven Architecture Audit

Date: 2026-04-19

## 1. Architecture Type

Verdict: Partially config-driven.

Why:
- The repository does have a real configuration/data layer for insurer logic: insurers, plans, riders, insurer rules, diagnosis overrides, and sub-limits are stored in database tables and loaded generically by the engine.
- But the system is not fully config-driven because core insurance behavior is still encoded in Python modules, fixed enums, hardcoded keyword lists, boolean rider capability flags, and LLM prompts.
- Result: some insurer onboarding can be done through data only, but only when the new insurer fits the existing rule shapes already anticipated by the code.

## 2. Evidence

### Config-driven parts

1. Generic engine loads insurer, plan, riders, and rule records from the database.

Files:
- apps/api/app/rules/engine.py
- apps/api/app/models.py

Patterns:
- analyze_claim loads Insurer by insurer_code, then Plan by plan_code, then Rider rows by rider_codes.
- It preloads universal_rules, diagnosis_overrides, insurer_rules, and sublimit_rules from the database before item evaluation.
- The step ordering is generic. There is no insurer-specific if insurer == "CARE_HEALTH" branching in the engine.

2. Insurer-specific overrides are stored in insurer_rules.

Files:
- apps/api/app/models.py
- apps/api/app/rules/step5_insurer.py
- apps/api/alembic/versions/004_seed_insurer_rules.py

Patterns:
- InsurerRule contains insurer_id, item_category, keywords, verdict, payable_pct, reason, and optional plan_codes.
- step5_insurer.check_insurer_rules iterates over database-loaded rules and applies them generically.
- This is the strongest evidence that the design intends to be data-driven.

3. Plans and riders are stored in normalized tables, not just code.

Files:
- apps/api/app/models.py
- apps/api/alembic/versions/006_plans_and_riders.py
- apps/api/app/routes/insurers.py

Patterns:
- Plan stores room_rent_limit_pct, room_rent_limit_abs, icu_room_rent_limit_abs, co_pay_pct, consumables_covered, consumables_sublimit.
- Rider stores coverage flags and additional_sum_insured.
- The API exposes plans and riders dynamically from the database.

4. Some policy caps are data-driven.

Files:
- apps/api/app/models.py
- apps/api/app/rules/step7_sublimit.py
- apps/api/alembic/versions/009_sublimit_rules.py

Patterns:
- SubLimitRule stores insurer_id, item_category, optional plan_codes, and max_amount.
- step7_sublimit applies caps generically from table data.

### Hardcoded parts

1. Billing-mode insurance logic is hardcoded in Python.

File:
- apps/api/app/rules/step3_billing.py

Patterns:
- CONSUMABLE_KEYWORDS is a hardcoded Python list.
- Package and mixed billing behavior is implemented directly in code.
- Which categories are treated as never-consumable is also hardcoded.

Impact:
- If a new insurer introduces a billing interpretation beyond the current package/itemized/mixed model, onboarding requires code changes.

2. Room-rent detection and deduction behavior are hardcoded.

File:
- apps/api/app/rules/step4_room_rent.py

Patterns:
- ROOM_RENT_KEYWORDS and ICU_KEYWORDS are fixed Python lists.
- The proportional deduction algorithm is embedded in code.
- The system assumes one specific room-rent reduction model for all insurers.

Impact:
- If a new insurer has a different room-rent deduction policy, slab logic, or exception structure, you cannot express it through config only.

3. Rider behavior is only partially data-driven; the rider model is hardcoded to a fixed capability set.

Files:
- apps/api/app/models.py
- apps/api/app/rules/step5b_riders.py

Patterns:
- Rider supports only predefined booleans: covers_consumables, covers_opd, covers_maternity, covers_dental, covers_critical_illness.
- step5b_riders hardcodes CONSUMABLE_CATEGORIES, OPD_CATEGORIES, MATERNITY_CATEGORIES, and MATERNITY_KEYWORDS.
- The override decision tree is fixed in code.

Impact:
- A new rider type outside these predefined fields requires schema and code changes.
- This is not Prisma-style declarative extensibility.

4. Universal insurance knowledge is embedded in code instead of config.

Files:
- apps/api/app/rules/step1_universal.py
- apps/api/app/rules/step0_categorize.py
- apps/api/app/rules/step6_llm.py

Patterns:
- _NEVER_EXCLUDED_CATEGORIES is hardcoded.
- recovery_action text is hardcoded by category.
- the Step 0 categorization taxonomy and examples are hardcoded in SYSTEM_PROMPT.
- the Step 6 LLM decision prompt contains hardcoded Indian insurance guidance.

Impact:
- The codebase still carries policy semantics directly in source code.
- This makes rule evolution dependent on deployments, not only data changes.

5. Seed data is implemented as code constants, not external declarative config.

Files:
- apps/api/alembic/versions/003_seed_insurers.py
- apps/api/alembic/versions/004_seed_insurer_rules.py
- apps/api/alembic/versions/006_plans_and_riders.py
- apps/web/prisma/seed.ts

Patterns:
- Insurers, plans, riders, and initial insurer rules are defined as Python or TypeScript arrays inside migrations/seeds.
- apps/web/prisma/seed.ts duplicates insurer master data outside the API seed path.

Impact:
- Runtime behavior is DB-backed, but repository onboarding still relies on modifying seed code if data should be tracked in-source.
- There is also duplication risk between API and web seed layers.

6. Insurer rule categories are inconsistent with the shared taxonomy.

Files:
- apps/api/app/schemas.py
- apps/api/app/rules/step0_categorize.py
- apps/api/app/rules/step5_insurer.py
- apps/api/alembic/versions/004_seed_insurer_rules.py

Examples:
- Shared Step 0 taxonomy includes categories like CONSUMABLE, DRUG, PROCEDURE, ROOM_RENT.
- Seeded insurer rules use categories such as MODERN_TREATMENT, CATARACT_PACKAGE, CONSUMABLE_OVERRIDE, CONSUMABLE_SUBLIMIT, PHARMACY_COPAY, ROOM_UPGRADE_COPAY, SURGEON_CONSULTATION.
- step5_insurer does direct category equality for classified items, and only falls back to keyword matching when the item is UNCLASSIFIED.

Impact:
- These insurer rules are brittle because they are outside the main taxonomy used by categorization.
- If Step 0 classifies an item as PROCEDURE or DRUG, a custom insurer category will not match by category, and keyword fallback will not run unless the item is UNCLASSIFIED.
- This is a design inconsistency and weakens the config story.

## 3. Problems Found

1. New insurer onboarding is not fully config-only.

Reason:
- It works only if the insurer fits existing fields, current categories, current rider booleans, and the existing room-rent and billing-mode logic.
- Any new policy construct outside those assumptions forces code changes.

2. The rules engine is generic, but the policy model is not generic enough.

Reason:
- The engine is roughly analyze(item, config, plan, riders), which is good.
- But the config schema is narrow and opinionated, so the engine is only as generic as those fixed columns and hardcoded branches allow.

3. Rider handling is tightly coupled to code.

Reason:
- Riders are represented as fixed boolean capabilities instead of generic rider rules or rider coverage clauses.
- This prevents arbitrary rider expansion.

4. Policy semantics are split between DB and Python.

Reason:
- Some logic is in tables.
- Some logic is in hardcoded keyword arrays, category allowlists, and prompt text.
- That split guarantees onboarding edge cases will leak into code.

5. Seed-based config is not true runtime config.

Reason:
- Migrations are good for bootstrapping data, but adding insurers by editing Alembic seed arrays is still code modification.
- That does not meet the stated goal of adding insurers without changing code.

6. Duplicate insurer master data exists.

Reason:
- apps/api Alembic seeds and apps/web Prisma seed both define insurer records.
- That is a maintainability smell and a likely source of drift.

## 4. Rider Handling

Answer: Riders are only partially config-driven.

What is config-driven:
- Rider records live in the database.
- Rider-plan relationships live in the plan_riders junction table.
- additional_sum_insured is data-driven.

What is hardcoded:
- Which rider types exist is effectively fixed by Rider columns.
- The logic for consumable, OPD, and maternity rescue is coded directly in step5b_riders.py.
- Category detection for rider rescue uses hardcoded lists and keyword fallbacks.

Conclusion:
- Existing rider types can be onboarded via data.
- New rider semantics cannot.

## 5. Policy Rules Assessment

### Room rent limits

Status: Partially config-driven.

Config-driven:
- Plan columns store room_rent_limit_pct, room_rent_limit_abs, icu_room_rent_limit_abs, icu_limit_pct.

Hardcoded:
- Room-rent item detection keywords.
- The deduction formula and application rules.
- The assumption that the same proportional deduction model applies generally.

### Consumables rules

Status: Partially config-driven.

Config-driven:
- exclusion_rules table can reject consumables.
- insurer_rules can override them.
- plans.consumables_covered and sublimit_rules can alter outcome.

Hardcoded:
- Consumable keyword lists in step3_billing.py.
- Consumable rescue categories in step5b_riders.py.
- Consumable definitions and examples in Step 0 prompt.

### Equipment rules

Status: Mostly hardcoded with some config support.

Config-driven:
- exclusion_rules can store EQUIPMENT_RENTAL exclusions.

Hardcoded:
- Equipment meaning is heavily influenced by Step 0 prompt and Step 6 prompt.
- Special distinctions such as equipment billed separately versus integral to a procedure are prompt-driven/code-driven, not a declarative rule layer.

## 6. LLM Usage

Assessment: Mostly acceptable, but not fully isolated from policy logic.

Good:
- Step 0 uses LLM only for categorization, not for final verdict.
- Step 6 is a fallback only when deterministic rules do not resolve the item.
- LLM output is capped in confidence and guarded against unsafe partial-payout behavior.

Not good enough for a pure config-driven architecture:
- The Step 0 and Step 6 prompts contain hardcoded insurance logic and taxonomy.
- That means some policy interpretation still lives in source code, even if the final verdict path is mostly deterministic.

Bottom line:
- LLM is not the primary decision maker, which is good.
- But it is still carrying domain logic that should ideally live in declarative policy definitions or a governed taxonomy/config layer.

## 7. Can a New Insurer Be Added by Config Only?

Short answer: No.

Honest answer:
- A new insurer can be added without changing core engine flow only if its policy can be expressed using the current tables and existing hardcoded assumptions.
- That means the insurer must fit the current category system, current room-rent model, current rider model, current billing-mode behavior, and current prompt taxonomy.
- The moment the insurer has a new benefit type, exception type, rider semantics, or adjudication pattern, the repository requires code changes.

So the architecture does not currently satisfy this goal:

Add new insurer without changing code, only by adding configuration.

It satisfies a weaker goal instead:

Add some insurers without changing engine code, provided their products fit the predefined policy model already baked into the codebase.

## 8. What Needs to Change

1. Replace fixed rider columns with generic rider rules.

Current problem:
- Rider is a table with hardcoded boolean fields.

Refactor:
- Introduce rider_rules or policy_extensions table with fields like rule_type, target_category, condition_json, verdict, payable_pct, cap_amount, scope, priority.

2. Move billing-mode behavior into declarative rule definitions.

Current problem:
- step3_billing.py embeds the package and mixed logic plus consumable keyword definitions.

Refactor:
- Represent billing-mode resolution as table-driven policies by category and insurer or plan.

3. Move room-rent policy variants into config.

Current problem:
- step4_room_rent.py assumes one deduction algorithm.

Refactor:
- Add plan_policy or policy_terms table with room_rent_rule_type, per_day_cap_strategy, deduction_method, icu_handling, and exceptions.

4. Unify category taxonomy.

Current problem:
- Step 0 taxonomy and insurer-rule categories are inconsistent.

Refactor:
- Create a governed category registry table or fixed enum used everywhere.
- Insurer rules should target canonical categories plus optional predicates, not ad hoc category names.

5. Externalize policy text and recovery text.

Current problem:
- recovery actions and prompt-based distinctions are hardcoded.

Refactor:
- Store explanation templates, recovery guidance, and evidence text in config tables or versioned policy files.

6. Stop using migration code as the source of truth for insurer onboarding.

Current problem:
- Initial data lives in Alembic arrays and duplicated Prisma seed code.

Refactor:
- Use a formal configuration import path: JSON/YAML/policy bundle or admin-driven DB ingestion.
- Migrations should create schema, not define ongoing insurer business content.

7. Make the rule engine operate on declarative policy clauses, not named Python steps.

Target shape:
- analyze(item, policy_context, policy_clauses)
- policy clauses loaded from DB or versioned config files
- clause evaluators generic by operator type, not insurer name or specific benefit family

## 9. Final Verdict

Can this system support adding a new insurer in 5 minutes using config only?

No.

Reason:
- The engine is partially data-driven, but the policy model is still constrained by hardcoded Python logic.
- It can onboard insurers that match the existing assumptions.
- It cannot honestly claim true config-driven insurer onboarding for arbitrary insurer logic.

Best one-line summary:

This repository has a generic DB-backed rule engine, but not a fully config-driven insurance architecture.