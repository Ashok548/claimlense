"""
seeds/_base.py — Sync SQL upsert helpers for the insurer seed runner.

Uses a plain synchronous SQLAlchemy engine (psycopg2 / pg8000 driver) so it runs
as a standalone script without the FastAPI async context. Mirrors the pattern of
`op.get_bind()` used in Alembic migration upgrades.

DATABASE_URL must be set in the environment. The asyncpg variant
(postgresql+asyncpg://) is automatically rewritten to the sync driver
(postgresql://) so the same env var works in both FastAPI and here.
"""

import os
import uuid
import logging

import sqlalchemy as sa
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


# ─── Engine ──────────────────────────────────────────────────────────────────

def get_engine() -> sa.engine.Engine:
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    # FastAPI uses postgresql+asyncpg://; replace for sync use
    url = raw.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(url, future=True)


# ─── Insurer ──────────────────────────────────────────────────────────────────

def upsert_insurer(conn: sa.engine.Connection, data: dict) -> str:
    """
    Insert or update a row in the `insurers` table.
    Returns the insurer UUID as a string.

    data keys: code, name, logo_url, room_rent_default
    """
    conn.execute(
        text("""
            INSERT INTO insurers (id, code, name, logo_url, room_rent_default, plans, is_active)
            VALUES (:id, :code, :name, :logo_url, :room_rent_default, '[]'::jsonb, true)
            ON CONFLICT (code) DO UPDATE SET
                name             = EXCLUDED.name,
                logo_url         = EXCLUDED.logo_url,
                room_rent_default = EXCLUDED.room_rent_default
        """),
        {
            "id": str(uuid.uuid4()),
            "code": data["code"],
            "name": data["name"],
            "logo_url": data.get("logo_url"),
            "room_rent_default": data.get("room_rent_default"),
        },
    )
    row = conn.execute(
        text("SELECT id FROM insurers WHERE code = :code"),
        {"code": data["code"]},
    ).fetchone()
    return str(row.id)


# ─── Plans ────────────────────────────────────────────────────────────────────

def upsert_plans(conn: sa.engine.Connection, plans: list[dict], insurer_id: str) -> dict[str, str]:
    """
    Upsert every plan in `plans` against `(insurer_id, code)`.
    Returns {plan_code: plan_uuid}.
    """
    plan_ids: dict[str, str] = {}
    for p in plans:
        conn.execute(
            text("""
                INSERT INTO plans (
                    id, insurer_id, code, name, description,
                    room_rent_limit_pct, room_rent_limit_abs, icu_room_rent_limit_abs,
                    co_pay_pct, icu_limit_pct, consumables_covered, consumables_sublimit
                )
                VALUES (
                    :id, :insurer_id, :code, :name, :description,
                    :room_rent_limit_pct, :room_rent_limit_abs, :icu_room_rent_limit_abs,
                    :co_pay_pct, :icu_limit_pct, :consumables_covered, :consumables_sublimit
                )
                ON CONFLICT (insurer_id, code) DO UPDATE SET
                    name                  = EXCLUDED.name,
                    description           = EXCLUDED.description,
                    room_rent_limit_pct   = EXCLUDED.room_rent_limit_pct,
                    room_rent_limit_abs   = EXCLUDED.room_rent_limit_abs,
                    icu_room_rent_limit_abs = EXCLUDED.icu_room_rent_limit_abs,
                    co_pay_pct            = EXCLUDED.co_pay_pct,
                    icu_limit_pct         = EXCLUDED.icu_limit_pct,
                    consumables_covered   = EXCLUDED.consumables_covered,
                    consumables_sublimit  = EXCLUDED.consumables_sublimit
            """),
            {
                "id": str(uuid.uuid4()),
                "insurer_id": insurer_id,
                "code": p["code"],
                "name": p["name"],
                "description": p.get("description"),
                "room_rent_limit_pct": p.get("room_rent_limit_pct"),
                "room_rent_limit_abs": p.get("room_rent_limit_abs"),
                "icu_room_rent_limit_abs": p.get("icu_room_rent_limit_abs"),
                "co_pay_pct": p.get("co_pay_pct", 0),
                "icu_limit_pct": p.get("icu_limit_pct"),
                "consumables_covered": p.get("consumables_covered", False),
                "consumables_sublimit": p.get("consumables_sublimit"),
            },
        )
        row = conn.execute(
            text("SELECT id FROM plans WHERE insurer_id = :iid AND code = :code"),
            {"iid": insurer_id, "code": p["code"]},
        ).fetchone()
        plan_ids[p["code"]] = str(row.id)
    return plan_ids


# ─── Riders ───────────────────────────────────────────────────────────────────

def upsert_riders(
    conn: sa.engine.Connection,
    riders: list[dict],
    insurer_id: str,
) -> dict[str, str]:
    """
    Upsert every rider in `riders` against `(insurer_id, code)`.
    Each rider dict may have a `clauses` key with a list of coverage clause dicts.
    Returns {rider_code: rider_uuid}.
    """
    rider_ids: dict[str, str] = {}
    for r in riders:
        conn.execute(
            text("""
                INSERT INTO riders (
                    id, insurer_id, code, name, description,
                    covers_consumables, covers_opd, covers_maternity,
                    covers_dental, covers_critical_illness
                )
                VALUES (
                    :id, :insurer_id, :code, :name, :description,
                    :covers_consumables, :covers_opd, :covers_maternity,
                    :covers_dental, :covers_critical_illness
                )
                ON CONFLICT (insurer_id, code) DO UPDATE SET
                    name                  = EXCLUDED.name,
                    description           = EXCLUDED.description,
                    covers_consumables    = EXCLUDED.covers_consumables,
                    covers_opd            = EXCLUDED.covers_opd,
                    covers_maternity      = EXCLUDED.covers_maternity,
                    covers_dental         = EXCLUDED.covers_dental,
                    covers_critical_illness = EXCLUDED.covers_critical_illness
            """),
            {
                "id": str(uuid.uuid4()),
                "insurer_id": insurer_id,
                "code": r["code"],
                "name": r["name"],
                "description": r.get("description"),
                "covers_consumables": r.get("covers_consumables", False),
                "covers_opd": r.get("covers_opd", False),
                "covers_maternity": r.get("covers_maternity", False),
                "covers_dental": r.get("covers_dental", False),
                "covers_critical_illness": r.get("covers_critical_illness", False),
            },
        )
        row = conn.execute(
            text("SELECT id FROM riders WHERE insurer_id = :iid AND code = :code"),
            {"iid": insurer_id, "code": r["code"]},
        ).fetchone()
        rider_id = str(row.id)
        rider_ids[r["code"]] = rider_id

        # Always re-seed rider_coverage_clauses (DELETE + INSERT is safe — no incoming FKs other than cascade)
        upsert_rider_clauses(conn, r.get("clauses", []), rider_id, r["name"])

    return rider_ids


def _resolve_kw_set_id(conn: sa.engine.Connection, name: str | None) -> str | None:
    if not name:
        return None
    row = conn.execute(
        text("SELECT id FROM keyword_sets WHERE name = :name"),
        {"name": name},
    ).fetchone()
    if row is None:
        logger.warning("keyword_set '%s' not found in DB — clause will have NULL fallback_kw_set_id", name)
        return None
    return str(row.id)


def upsert_rider_clauses(
    conn: sa.engine.Connection,
    clauses: list[dict],
    rider_id: str,
    rider_name: str = "",
) -> None:
    """
    Replace all rider_coverage_clauses for `rider_id` with the provided list.
    Idempotent — safe to call multiple times.

    Each clause dict keys:
      target_categories      list[str]   — canonical item category codes
      verdict                str         — default "PAYABLE"
      payable_pct            float|None
      only_rescues_status    list[str]   — default ["NOT_PAYABLE","VERIFY_WITH_TPA"]
      priority               int         — default 0
      reason_template        str
      fallback_kw_set_name   str|None    — name lookup in keyword_sets table
    """
    conn.execute(
        text("DELETE FROM rider_coverage_clauses WHERE rider_id = :rid"),
        {"rid": rider_id},
    )
    for c in clauses:
        fallback_kw_set_id = _resolve_kw_set_id(conn, c.get("fallback_kw_set_name"))
        conn.execute(
            text("""
                INSERT INTO rider_coverage_clauses (
                    id, rider_id, target_categories, fallback_kw_set_id,
                    verdict, payable_pct, only_rescues_status, priority, reason_template
                )
                VALUES (
                    :id, :rider_id, :target_categories, :fallback_kw_set_id,
                    :verdict, :payable_pct, :only_rescues_status, :priority, :reason_template
                )
            """),
            {
                "id": str(uuid.uuid4()),
                "rider_id": rider_id,
                "target_categories": c["target_categories"],
                "fallback_kw_set_id": fallback_kw_set_id,
                "verdict": c.get("verdict", "PAYABLE"),
                "payable_pct": c.get("payable_pct"),
                "only_rescues_status": c.get("only_rescues_status", ["NOT_PAYABLE", "VERIFY_WITH_TPA"]),
                "priority": c.get("priority", 0),
                "reason_template": c["reason_template"],
            },
        )


# ─── plan_riders junction ─────────────────────────────────────────────────────

def link_plan_riders(
    conn: sa.engine.Connection,
    plan_riders: list[tuple[str, str]],
    insurer_id: str,
) -> None:
    """
    Insert (plan_code, rider_code) pairs into plan_riders.
    Uses ON CONFLICT DO NOTHING — safe to re-run.
    """
    for plan_code, rider_code in plan_riders:
        conn.execute(
            text("""
                INSERT INTO plan_riders (plan_id, rider_id)
                SELECT p.id, r.id
                FROM plans p
                CROSS JOIN riders r
                WHERE p.insurer_id = :iid AND p.code = :pc
                  AND r.insurer_id = :iid AND r.code = :rc
                ON CONFLICT DO NOTHING
            """),
            {"iid": insurer_id, "pc": plan_code, "rc": rider_code},
        )


# ─── Insurer rules ────────────────────────────────────────────────────────────

def upsert_insurer_rules(
    conn: sa.engine.Connection,
    rules: list[dict],
    insurer_id: str,
) -> None:
    """
    Replace all insurer_rules for `insurer_id` with the provided list.
    DELETE + INSERT is safe — insurer_rules has no incoming FKs.

    Each rule dict keys:
      item_category   str        — MUST be a canonical taxonomy code from item_categories
      keywords        list[str]
      verdict         str        — payability_status enum value
      payable_pct     float|None
      reason          str
      plan_codes      list[str]|None
    """
    conn.execute(
        text("DELETE FROM insurer_rules WHERE insurer_id = :iid"),
        {"iid": insurer_id},
    )
    for r in rules:
        conn.execute(
            text("""
                INSERT INTO insurer_rules (
                    id, insurer_id, item_category, keywords,
                    verdict, payable_pct, reason, plan_codes
                )
                VALUES (
                    :id, :insurer_id, :item_category, :keywords,
                    :verdict, :payable_pct, :reason, :plan_codes
                )
            """),
            {
                "id": str(uuid.uuid4()),
                "insurer_id": insurer_id,
                "item_category": r["item_category"],
                "keywords": r["keywords"],
                "verdict": r["verdict"],
                "payable_pct": r.get("payable_pct"),
                "reason": r["reason"],
                "plan_codes": r.get("plan_codes"),
            },
        )


# ─── Sublimit rules ───────────────────────────────────────────────────────────

def upsert_sublimit_rules(
    conn: sa.engine.Connection,
    rules: list[dict],
    insurer_id: str,
) -> None:
    """
    Replace all sublimit_rules for `insurer_id`.
    DELETE + INSERT is safe — sublimit_rules has no incoming FKs.

    Each rule dict keys:
      item_category   str
      max_amount      float
      plan_codes      list[str]|None
      note            str|None
    """
    conn.execute(
        text("DELETE FROM sublimit_rules WHERE insurer_id = :iid"),
        {"iid": insurer_id},
    )
    for r in rules:
        conn.execute(
            text("""
                INSERT INTO sublimit_rules (id, insurer_id, item_category, plan_codes, max_amount, note)
                VALUES (:id, :insurer_id, :item_category, :plan_codes, :max_amount, :note)
            """),
            {
                "id": str(uuid.uuid4()),
                "insurer_id": insurer_id,
                "item_category": r["item_category"],
                "plan_codes": r.get("plan_codes"),
                "max_amount": r["max_amount"],
                "note": r.get("note"),
            },
        )
