"""FastAPI routes — GET /v1/insurers"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Insurer, Plan, Rider
from app.schemas import InsurerResponse, PlanDetail, RiderDetail

router = APIRouter(prefix="/v1/insurers", tags=["insurers"])


def _build_rider_detail(r: Rider) -> RiderDetail:
    """Build RiderDetail from an ORM Rider, deriving coverage_types and
    backward-compatible boolean fields from rider_coverage_clauses."""
    coverage_types: list[str] = []
    if hasattr(r, "coverage_clauses") and r.coverage_clauses:
        seen: set[str] = set()
        for clause in r.coverage_clauses:
            for cat in clause.target_categories:
                if cat not in seen:
                    seen.add(cat)
                    coverage_types.append(cat)

    return RiderDetail(
        id=r.id,
        code=r.code,
        name=r.name,
        description=r.description,
        coverage_types=coverage_types,
        covers_consumables="CONSUMABLE" in coverage_types or r.covers_consumables,
        covers_opd="OPD" in coverage_types or r.covers_opd,
        covers_maternity="MATERNITY" in coverage_types or r.covers_maternity,
        covers_dental="DENTAL" in coverage_types or r.covers_dental,
        covers_critical_illness="CRITICAL_ILLNESS" in coverage_types or r.covers_critical_illness,
        additional_sum_insured=float(r.additional_sum_insured) if r.additional_sum_insured else None,
    )


@router.get("/", response_model=list[InsurerResponse])
async def list_insurers(db: AsyncSession = Depends(get_db)) -> list[InsurerResponse]:
    result = await db.execute(
        select(Insurer)
        .options(
            selectinload(Insurer.plans_rel)
            .selectinload(Plan.riders)
            .selectinload(Rider.coverage_clauses)
        )
        .where(Insurer.is_active == True)
    )  # noqa: E712
    insurers = result.scalars().all()

    return [
        InsurerResponse(
            id=i.id,
            code=i.code,
            name=i.name,
            logo_url=i.logo_url,
            plans=[
                PlanDetail(
                    id=p.id,
                    code=p.code,
                    name=p.name,
                    description=p.description,
                    room_rent_limit_pct=float(p.room_rent_limit_pct) if p.room_rent_limit_pct else None,
                    room_rent_limit_abs=float(p.room_rent_limit_abs) if p.room_rent_limit_abs else None,
                    co_pay_pct=float(p.co_pay_pct) if p.co_pay_pct else None,
                    icu_limit_pct=float(p.icu_limit_pct) if p.icu_limit_pct else None,
                    consumables_covered=p.consumables_covered,
                    consumables_sublimit=float(p.consumables_sublimit) if p.consumables_sublimit else None,
                    riders=[_build_rider_detail(r) for r in p.riders],
                ) for p in i.plans_rel
            ] if i.plans_rel else None,
            room_rent_default=i.room_rent_default,
        )
        for i in insurers
    ]


@router.get("/{insurer_id}/plans", response_model=list[PlanDetail])
async def get_insurer_plans(insurer_id: str, db: AsyncSession = Depends(get_db)) -> list[PlanDetail]:
    insurer_result = await db.execute(select(Insurer).where(Insurer.id == insurer_id))
    insurer = insurer_result.scalar_one_or_none()
    if not insurer:
        raise HTTPException(status_code=404, detail="Insurer not found")

    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.riders).selectinload(Rider.coverage_clauses))
        .where((Plan.insurer_id == insurer.id) & (Plan.is_active == True))
    )
    plans = result.scalars().all()

    return [
        PlanDetail(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            room_rent_limit_pct=float(p.room_rent_limit_pct) if p.room_rent_limit_pct else None,
            room_rent_limit_abs=float(p.room_rent_limit_abs) if p.room_rent_limit_abs else None,
            co_pay_pct=float(p.co_pay_pct) if p.co_pay_pct else None,
            icu_limit_pct=float(p.icu_limit_pct) if p.icu_limit_pct else None,
            consumables_covered=p.consumables_covered,
            consumables_sublimit=float(p.consumables_sublimit) if p.consumables_sublimit else None,
            riders=[_build_rider_detail(r) for r in p.riders],
        ) for p in plans
    ]
