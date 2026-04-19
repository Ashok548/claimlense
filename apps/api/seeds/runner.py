"""
seeds/runner.py — Master reference-data and insurer seed runner.

Runs all reference seed modules plus all insurer seed modules (or a filtered
subset) idempotently against the database defined by the DATABASE_URL
environment variable.

Usage (from apps/api/ directory):
    python seeds/runner.py                          # seed reference domains, then all insurers
    python seeds/runner.py --global-only            # seed reference/global domains only
    python seeds/runner.py --domain item_categories # seed one reference domain
    python seeds/runner.py --insurer HDFC_ERGO      # seed one insurer
    python seeds/runner.py --dry-run                # validate structure, no DB writes
    python seeds/runner.py --list                   # list registered reference domains and insurer codes

The runner is safe to run multiple times — every helper uses ON CONFLICT DO
UPDATE or DELETE + INSERT with no incoming FK references.
"""

import argparse
import logging
import os
import sys
import time

# Allow running as `python seeds/runner.py` directly (not only as `python -m seeds.runner`).
# When executed as a script, __file__ is seeds/runner.py — add the api/ directory to path.
_HERE = os.path.dirname(os.path.abspath(__file__))
_API_ROOT = os.path.dirname(_HERE)
if _API_ROOT not in sys.path:
    sys.path.insert(0, _API_ROOT)

# Load .env file if DATABASE_URL is not already set in the environment.
# This allows the runner to work without manual env var setup on each terminal session.
if "DATABASE_URL" not in os.environ:
    _ENV_FILE = os.path.join(_API_ROOT, ".env")
    if os.path.exists(_ENV_FILE):
        from dotenv import load_dotenv
        load_dotenv(_ENV_FILE)

from seeds._base import (
    get_engine,
    link_plan_riders,
    upsert_billing_mode_rules,
    upsert_diagnosis_overrides,
    upsert_diagnosis_synonym_groups,
    upsert_exclusion_rules,
    upsert_item_categories,
    upsert_insurer,
    upsert_insurer_rules,
    upsert_keyword_sets,
    upsert_plans,
    upsert_room_rent_config,
    upsert_riders,
    upsert_sublimit_rules,
)
from seeds.insurers import INSURER_MODULES
from seeds.reference import REFERENCE_MODULES

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Required module attributes ───────────────────────────────────────────────

_REQUIRED_ATTRS = ("INSURER", "PLANS", "RIDERS", "PLAN_RIDERS", "INSURER_RULES")

_REFERENCE_DOMAIN_ATTRS = {
    "irdai_exclusions": ("EXCLUSION_RULES",),
    "keyword_sets": ("KEYWORD_SETS",),
    "item_categories": ("ITEM_CATEGORIES",),
    "diagnosis": ("DIAGNOSIS_OVERRIDES", "DIAGNOSIS_SYNONYM_GROUPS"),
    "room_rent": ("ROOM_RENT_CONFIGS",),
    "billing_mode": ("BILLING_MODE_RULES",),
}

def _seed_diagnosis(conn, module) -> None:
    upsert_diagnosis_overrides(conn, module.DIAGNOSIS_OVERRIDES)
    upsert_diagnosis_synonym_groups(conn, module.DIAGNOSIS_SYNONYM_GROUPS)


_REFERENCE_SEEDERS = {
    "irdai_exclusions": lambda conn, module: upsert_exclusion_rules(conn, module.EXCLUSION_RULES),
    "keyword_sets": lambda conn, module: upsert_keyword_sets(conn, module.KEYWORD_SETS),
    "item_categories": lambda conn, module: upsert_item_categories(conn, module.ITEM_CATEGORIES),
    "diagnosis": _seed_diagnosis,
    "room_rent": lambda conn, module: upsert_room_rent_config(conn, module.ROOM_RENT_CONFIGS),
    "billing_mode": lambda conn, module: upsert_billing_mode_rules(conn, module.BILLING_MODE_RULES),
}

_REFERENCE_SUMMARIES = {
    "irdai_exclusions": lambda module: f"{len(module.EXCLUSION_RULES)} exclusion rules",
    "keyword_sets": lambda module: f"{len(module.KEYWORD_SETS)} keyword sets",
    "item_categories": lambda module: f"{len(module.ITEM_CATEGORIES)} item categories",
    "diagnosis": lambda module: (
        f"{len(module.DIAGNOSIS_OVERRIDES)} diagnosis overrides  "
        f"{len(module.DIAGNOSIS_SYNONYM_GROUPS)} synonym groups"
    ),
    "room_rent": lambda module: f"{len(module.ROOM_RENT_CONFIGS)} room-rent configs",
    "billing_mode": lambda module: f"{len(module.BILLING_MODE_RULES)} billing rules",
}


def _validate_module(module) -> list[str]:
    """Return list of validation errors. Empty list means valid."""
    errors: list[str] = []
    for attr in _REQUIRED_ATTRS:
        if not hasattr(module, attr):
            errors.append(f"missing required attribute: {attr}")

    if hasattr(module, "INSURER"):
        for key in ("code", "name"):
            if key not in module.INSURER:
                errors.append(f"INSURER dict missing key: {key}")

    if hasattr(module, "INSURER_RULES"):
        for i, r in enumerate(module.INSURER_RULES):
            cat = r.get("item_category", "")
            # Warn on legacy names caught before taxonomy unification
            if cat in ("CONSUMABLE_OVERRIDE", "CONSUMABLE_SUBLIMIT"):
                errors.append(
                    f"INSURER_RULES[{i}]: item_category '{cat}' is a pre-016 legacy name. "
                    f"Use 'CONSUMABLE' instead."
                )

    return errors


def _build_reference_lookup() -> tuple[set[str], set[str]]:
    keyword_set_names: set[str] = set()
    item_category_codes: set[str] = set()
    for module in REFERENCE_MODULES:
        keyword_set_names.update(
            keyword_set["name"]
            for keyword_set in getattr(module, "KEYWORD_SETS", [])
        )
        item_category_codes.update(
            category["code"]
            for category in getattr(module, "ITEM_CATEGORIES", [])
        )
    return keyword_set_names, item_category_codes


def _validate_reference_module(
    module,
    keyword_set_names: set[str],
    item_category_codes: set[str],
) -> list[str]:
    errors: list[str] = []
    domain = getattr(module, "DOMAIN", None)
    if not domain:
        return ["missing required attribute: DOMAIN"]

    required_attrs = _REFERENCE_DOMAIN_ATTRS.get(domain)
    if required_attrs is None:
        return [f"unknown DOMAIN '{domain}'"]

    for attr in required_attrs:
        if not hasattr(module, attr):
            errors.append(f"missing required attribute: {attr}")

    if domain == "room_rent":
        for i, config in enumerate(module.ROOM_RENT_CONFIGS):
            for key in ("detection_kw_set_name", "icu_kw_set_name"):
                if config.get(key) not in keyword_set_names:
                    errors.append(
                        f"ROOM_RENT_CONFIGS[{i}]: unknown keyword set '{config.get(key)}'"
                    )

    if domain == "billing_mode":
        for i, rule in enumerate(module.BILLING_MODE_RULES):
            if rule.get("item_category") not in item_category_codes:
                errors.append(
                    f"BILLING_MODE_RULES[{i}]: unknown item_category '{rule.get('item_category')}'"
                )
            fallback_name = rule.get("fallback_kw_set_name")
            if fallback_name and fallback_name not in keyword_set_names:
                errors.append(
                    f"BILLING_MODE_RULES[{i}]: unknown fallback keyword set '{fallback_name}'"
                )
            for category in rule.get("bypass_categories") or []:
                if category not in item_category_codes:
                    errors.append(
                        f"BILLING_MODE_RULES[{i}]: unknown bypass category '{category}'"
                    )

    if domain == "irdai_exclusions":
        for i, rule in enumerate(module.EXCLUSION_RULES):
            if rule.get("category") not in item_category_codes:
                errors.append(
                    f"EXCLUSION_RULES[{i}]: unknown category '{rule.get('category')}'"
                )

    if domain == "diagnosis":
        for i, override in enumerate(module.DIAGNOSIS_OVERRIDES):
            if override.get("item_category") not in item_category_codes:
                errors.append(
                    f"DIAGNOSIS_OVERRIDES[{i}]: unknown item_category '{override.get('item_category')}'"
                )

    return errors


# ─── Seed one insurer ─────────────────────────────────────────────────────────

def seed_insurer(conn, module) -> None:
    """Execute all upsert helpers for a single insurer module within an open connection."""
    insurer_id = upsert_insurer(conn, module.INSURER)
    upsert_plans(conn, module.PLANS, insurer_id)
    upsert_riders(conn, module.RIDERS, insurer_id)          # also upserts rider_coverage_clauses
    link_plan_riders(conn, module.PLAN_RIDERS, insurer_id)
    upsert_insurer_rules(conn, module.INSURER_RULES, insurer_id)
    upsert_sublimit_rules(conn, getattr(module, "SUBLIMIT_RULES", []), insurer_id)


def seed_reference_domain(conn, module) -> None:
    """Execute the registered seeder for a reference-data domain module."""
    _REFERENCE_SEEDERS[module.DOMAIN](conn, module)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed reference and insurer configuration data into the ClaimSmart database."
    )
    parser.add_argument(
        "--insurer",
        metavar="CODE",
        help="Seed a single insurer by code (e.g. HDFC_ERGO). "
             "Omit to seed all registered insurers.",
    )
    parser.add_argument(
        "--global-only",
        action="store_true",
        help="Seed only reference/global configuration domains.",
    )
    parser.add_argument(
        "--domain",
        metavar="NAME",
        help="Seed a single reference domain by name (e.g. irdai_exclusions, item_categories).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate seed module structure without writing to the database.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_codes",
        help="Print registered insurer codes and exit.",
    )
    args = parser.parse_args()

    if args.domain and args.insurer:
        logger.error("--domain cannot be combined with --insurer.")
        return 1

    # ── --list ────────────────────────────────────────────────────────────
    if args.list_codes:
        print("Registered reference seed modules:")
        for m in REFERENCE_MODULES:
            print(f"  {m.DOMAIN:<30}  {m.__name__}")
        print()
        print("Registered insurer seed modules:")
        for m in INSURER_MODULES:
            print(f"  {m.INSURER['code']:<30}  {m.INSURER['name']}")
        return 0

    reference_modules = REFERENCE_MODULES
    if args.domain:
        reference_modules = [m for m in REFERENCE_MODULES if m.DOMAIN == args.domain]
        if not reference_modules:
            logger.error(
                "No reference seed module found for domain '%s'. Use --list to see available domains.",
                args.domain,
            )
            return 1

    insurer_modules = INSURER_MODULES
    if args.insurer:
        insurer_modules = [m for m in insurer_modules if m.INSURER["code"] == args.insurer]
        if not insurer_modules:
            logger.error(
                "No seed module found for insurer code '%s'. "
                "Use --list to see available codes.",
                args.insurer,
            )
            return 1
    elif args.global_only or args.domain:
        insurer_modules = []

    # ── Validate all modules before touching the DB ───────────────────────
    # Build lookup tables once; passed into each _validate_reference_module call.
    kw_set_names, cat_codes = _build_reference_lookup()

    has_errors = False
    for module in reference_modules:
        errors = _validate_reference_module(module, kw_set_names, cat_codes)
        for err in errors:
            logger.error("[%s] %s", module.__name__, err)
            has_errors = True

    for module in insurer_modules:
        errors = _validate_module(module)
        for err in errors:
            logger.error("[%s] %s", module.__name__, err)
            has_errors = True

    if has_errors:
        logger.error("Validation failed — no database writes performed.")
        return 1

    if args.dry_run:
        logger.info(
            "Dry-run: %d reference domain(s) and %d insurer module(s) validated successfully. No DB writes.",
            len(reference_modules),
            len(insurer_modules),
        )
        return 0

    # ── Run seeds inside a single transaction ─────────────────────────────
    engine = get_engine()
    start = time.monotonic()

    with engine.begin() as conn:
        if reference_modules:
            logger.info("Seeding %d reference domain(s)...", len(reference_modules))
        for module in reference_modules:
            domain = module.DOMAIN
            t0 = time.monotonic()
            try:
                seed_reference_domain(conn, module)
                elapsed = time.monotonic() - t0
                logger.info(
                    "  ✓ %-30s  %s  (%.2fs)",
                    domain,
                    _REFERENCE_SUMMARIES[domain](module),
                    elapsed,
                )
            except Exception as exc:
                logger.exception("  ✗ %-30s  FAILED: %s", domain, exc)
                logger.error("Transaction rolled back — no partial writes committed.")
                return 1

        if insurer_modules:
            logger.info("Seeding %d insurer(s)...", len(insurer_modules))
        for module in insurer_modules:
            code = module.INSURER["code"]
            t0 = time.monotonic()
            try:
                seed_insurer(conn, module)
                elapsed = time.monotonic() - t0
                logger.info(
                    "  ✓ %-30s  %d plans  %d riders  %d rules  %d sublimits  (%.2fs)",
                    code,
                    len(module.PLANS),
                    len(module.RIDERS),
                    len(module.INSURER_RULES),
                    len(getattr(module, "SUBLIMIT_RULES", [])),
                    elapsed,
                )
            except Exception as exc:
                logger.exception("  ✗ %-30s  FAILED: %s", code, exc)
                logger.error("Transaction rolled back — no partial writes committed.")
                return 1

    total = time.monotonic() - start
    logger.info("Seed complete in %.2fs.", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
