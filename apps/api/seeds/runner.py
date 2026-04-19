"""
seeds/runner.py — Master insurer seed runner.

Runs all insurer seed modules (or a single one) idempotently against the
database defined by the DATABASE_URL environment variable.

Usage (from apps/api/ directory):
    python seeds/runner.py                          # seed all insurers
    python seeds/runner.py --insurer HDFC_ERGO      # seed one insurer
    python seeds/runner.py --dry-run                # validate structure, no DB writes
    python seeds/runner.py --list                   # list registered insurer codes

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

from seeds._base import (
    get_engine,
    link_plan_riders,
    upsert_insurer,
    upsert_insurer_rules,
    upsert_plans,
    upsert_riders,
    upsert_sublimit_rules,
)
from seeds.insurers import INSURER_MODULES

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Required module attributes ───────────────────────────────────────────────

_REQUIRED_ATTRS = ("INSURER", "PLANS", "RIDERS", "PLAN_RIDERS", "INSURER_RULES")


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


# ─── Seed one insurer ─────────────────────────────────────────────────────────

def seed_insurer(conn, module) -> None:
    """Execute all upsert helpers for a single insurer module within an open connection."""
    code = module.INSURER["code"]
    insurer_id = upsert_insurer(conn, module.INSURER)
    upsert_plans(conn, module.PLANS, insurer_id)
    upsert_riders(conn, module.RIDERS, insurer_id)          # also upserts rider_coverage_clauses
    link_plan_riders(conn, module.PLAN_RIDERS, insurer_id)
    upsert_insurer_rules(conn, module.INSURER_RULES, insurer_id)
    upsert_sublimit_rules(conn, getattr(module, "SUBLIMIT_RULES", []), insurer_id)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed insurer configuration data into the ClaimSmart database."
    )
    parser.add_argument(
        "--insurer",
        metavar="CODE",
        help="Seed a single insurer by code (e.g. HDFC_ERGO). "
             "Omit to seed all registered insurers.",
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

    # ── --list ────────────────────────────────────────────────────────────
    if args.list_codes:
        print("Registered insurer seed modules:")
        for m in INSURER_MODULES:
            print(f"  {m.INSURER['code']:<30}  {m.INSURER['name']}")
        return 0

    # ── Filter modules ────────────────────────────────────────────────────
    modules = INSURER_MODULES
    if args.insurer:
        modules = [m for m in modules if m.INSURER["code"] == args.insurer]
        if not modules:
            logger.error(
                "No seed module found for insurer code '%s'. "
                "Use --list to see available codes.",
                args.insurer,
            )
            return 1

    # ── Validate all modules before touching the DB ───────────────────────
    has_errors = False
    for module in modules:
        errors = _validate_module(module)
        for err in errors:
            logger.error("[%s] %s", module.__name__, err)
            has_errors = True

    if has_errors:
        logger.error("Validation failed — no database writes performed.")
        return 1

    if args.dry_run:
        logger.info("Dry-run: %d module(s) validated successfully. No DB writes.", len(modules))
        return 0

    # ── Run seeds inside a single transaction ─────────────────────────────
    engine = get_engine()
    start = time.monotonic()

    with engine.begin() as conn:
        logger.info("Seeding %d insurer(s)...", len(modules))
        for module in modules:
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
