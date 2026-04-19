"""
Rule Engine Orchestrator - 8-step pipeline per bill item.

Step 0: LLM batch categorizer - single GPT-4o call assigns a category to every item
         before rule evaluation begins. Rules then match by category, not substring.
Step 1: IRDAI universal exclusions (DB query)
Step 2: Diagnosis-aware overrides (DB query) - can RESCUE items from Step 1
Step 3: Billing mode context (package bypasses consumable exclusions)
Step 4: Room rent cap + proportional deduction ratio
Step 5: Insurer-specific rules (DB query)
Step 6: GPT-4o LLM fallback (verdict only - category already known from Step 0)
Step 7: Sub-limit aggregate cap (DB + plan-level consumables_sublimit)
Step 8: Default -> VERIFY_WITH_TPA (never PAYABLE for unknowns)
"""

import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClaimAnalysis, BillLineItem, Insurer, Plan, Rider
from app.rules.step0_categorize import batch_categorize_items
from app.rules.step1_universal import load_universal_exclusion_rules, check_universal_exclusions
from app.rules.step2_diagnosis import load_diagnosis_overrides, check_diagnosis_override
from app.rules.step3_billing import check_billing_mode
from app.rules.step4_room_rent import (
    apply_proportional_deduction,
    check_room_rent,
)
from app.rules.step5_insurer import load_insurer_rules, check_insurer_rules
from app.rules.step5b_riders import check_rider_and_plan_coverage
from app.rules.step6_llm import llm_classify_item, _default_verify
from app.rules.step7_sublimit import load_sublimit_rules, apply_sublimit_cap
from app.schemas import (
    AnalyzedLineItem,
    AnalyzeRequest,
    AnalyzeResponse,
    AnalysisSummary,
    BillingMode,
    ConfidenceBasis,
    PayabilityStatus,
)


async def analyze_claim(
    request: AnalyzeRequest,
    db: AsyncSession,
) -> AnalyzeResponse:
    """Main entrypoint — orchestrates all 7 rule steps, persists results."""

    # ── Load insurer from DB ───────────────────────────────────────────────
    insurer_result = await db.execute(
        select(Insurer).where(Insurer.code == request.insurer_code)
    )
    insurer = insurer_result.scalar_one_or_none()
    if not insurer:
        raise ValueError(f"Insurer '{request.insurer_code}' not found in database.")

    # ── Load Plan and Riders ───────────────────────────────────────────────
    plan_result = await db.execute(
        select(Plan).where((Plan.insurer_id == insurer.id) & (Plan.code == request.plan_code))
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise ValueError(f"Plan '{request.plan_code}' not found for insurer '{request.insurer_code}'.")

    riders = []
    if request.rider_codes:
        riders_result = await db.execute(
            select(Rider).where(
                (Rider.insurer_id == insurer.id)
                & (Rider.code.in_(request.rider_codes))
                & (Rider.plans.any(Plan.id == plan.id))
            )
        )
        riders = riders_result.scalars().all()

    # Compute effective room rent limit (ward)
    effective_room_rent_limit = None
    if plan.room_rent_limit_abs:
        effective_room_rent_limit = float(plan.room_rent_limit_abs)
    elif plan.room_rent_limit_pct and request.sum_insured:
        effective_room_rent_limit = (float(plan.room_rent_limit_pct) / 100.0) * request.sum_insured

    # Compute effective ICU per-day limit (may be separate from general ward limit)
    effective_icu_room_rent_limit: float | None = None
    if plan.icu_room_rent_limit_abs:
        effective_icu_room_rent_limit = float(plan.icu_room_rent_limit_abs)
    # If no explicit ICU limit is set, step4 falls back to effective_room_rent_limit internally.

    # ── Pre-load all rules once (avoids N+1 DB queries) ──────────────────
    universal_rules = await load_universal_exclusion_rules(db)
    diagnosis_overrides = await load_diagnosis_overrides(db)
    insurer_rules = await load_insurer_rules(insurer.id, db)
    sublimit_rules = await load_sublimit_rules(insurer.id, db)

    # ── Step 0: LLM batch categorization (one call for all items) ─────────
    # Returns {} on failure — all steps gracefully fall back to keyword matching.
    category_map: dict[str, str] = await batch_categorize_items(
        request.bill_items, request.diagnosis, request.billing_mode.value
    )

    # ── Process each bill item through pipeline ────────────────────────────
    analyzed_items: list[AnalyzedLineItem] = []
    # Separate deduction ratios for ICU vs general ward.
    # If only a generic room_rent_limit is configured, both ratios converge to the same value.
    ward_deduction_ratio = 1.0
    icu_deduction_ratio = 1.0
    room_rent_item_ids: set[uuid.UUID] = set()
    icu_room_rent_item_ids: set[uuid.UUID] = set()   # subset: ICU lines only

    for item in request.bill_items:
        result: AnalyzedLineItem | None = None
        # Category assigned by Step 0; None means keyword fallback applies in each step
        item_category: str | None = category_map.get(item.description)

        # Step 2 first: Diagnosis override can RESCUE items from IRDAI exclusion
        result = check_diagnosis_override(item, request.diagnosis, diagnosis_overrides, item_category)

        if result is None:
            # Step 1: IRDAI Universal Exclusions
            result = check_universal_exclusions(item, universal_rules, item_category)

        if result is None:
            # Step 3: Billing mode (package bypasses consumable rules)
            result = check_billing_mode(item, request.billing_mode, item_category)

        if result is None:
            # Step 4: Room rent cap check
            room_result, ratio, is_icu_line = check_room_rent(
                item, effective_room_rent_limit,
                icu_days=request.icu_days,
                general_ward_days=request.general_ward_days,
                icu_room_rent_limit=effective_icu_room_rent_limit,
            )
            if room_result is not None:
                result = room_result
                room_rent_item_ids.add(result.id)
                if ratio < 1.0:
                    if is_icu_line:
                        # Use the worst ICU ratio seen so far
                        icu_deduction_ratio = min(icu_deduction_ratio, ratio)
                    else:
                        # Use the worst ward ratio seen so far
                        ward_deduction_ratio = min(ward_deduction_ratio, ratio)
                    if is_icu_line:
                        icu_room_rent_item_ids.add(result.id)

        if result is None:
            # Step 5: Insurer-specific rules
            result = check_insurer_rules(item, insurer_rules, request.plan_code, item_category)
        elif result is not None and result.status == PayabilityStatus.NOT_PAYABLE and result.confidence_basis in (
            ConfidenceBasis.IRDAI_RULE,
            ConfidenceBasis.BILLING_MODE,  # MIXED-mode consumable VERIFY or ITEMIZED NOT_PAYABLE from step3
        ):
            # Step 5 re-runs against IRDAI-rejected or billing-mode-rejected items.
            # Insurers can contractually extend coverage beyond IRDAI minimums
            # (e.g. HDFC Optima Secure covers consumables).
            # Guard: only override NOT_PAYABLE — never downgrade a VERIFY_WITH_TPA
            # or a diagnosis rescue (DIAGNOSIS_OVERRIDE basis is excluded by this condition).
            insurer_override = check_insurer_rules(item, insurer_rules, request.plan_code, item_category)
            if insurer_override is not None:
                result = insurer_override

        # Step 5b: Rider and Plan Coverage Overrides (runs on rejected items only)
        if result is not None and result.status != PayabilityStatus.PAYABLE:
            result = check_rider_and_plan_coverage(item, result, plan, riders, item_category)

        if result is None:
            # Step 6: GPT-4o LLM fallback (verdict only; category already known)
            result = await llm_classify_item(
                item, insurer.name, request.diagnosis, request.billing_mode.value, item_category
            )

        # (Step 7 is embedded in llm_classify_item as the safe default)
        analyzed_items.append(result)

    # ── Apply proportional deduction to ALL non-room-rent items ───────────
    # ICU and general ward over-runs generate independent ratios.
    # When both are < 1.0, non-room-rent items are reduced by the worse of the two
    # (contractually the insurer applies the worst-ratio rule per IRDAI tariff).
    # If only one type exceeded its cap, that ratio applies to all non-rent items.
    # This is conservative but correct — separate per-item attribution of ICU vs
    # ward charges to other bill items is not supported by standard policy wording.
    combined_ratio = min(ward_deduction_ratio, icu_deduction_ratio)
    if combined_ratio < 1.0:
        analyzed_items = [
            item
            if item.id in room_rent_item_ids
            else apply_proportional_deduction(item, combined_ratio)
            for item in analyzed_items
        ]

    # ── Step 7: Sub-limit aggregate cap ────────────────────────────────────
    analyzed_items = apply_sublimit_cap(
        analyzed_items, sublimit_rules, request.plan_code, plan
    )

    # ── Apply Co-pay (immutable model_copy) ───────────────────────────────
    if plan.co_pay_pct and plan.co_pay_pct > 0:
        copay_factor = 1.0 - (float(plan.co_pay_pct) / 100.0)
        analyzed_items = [
            item.model_copy(update={
                "payable_amount": round(item.payable_amount * copay_factor, 2),
                "rule_matched": (item.rule_matched or "") + "|COPAY",
            })
            if item.status in (PayabilityStatus.PAYABLE, PayabilityStatus.PARTIALLY_PAYABLE)
            else item
            for item in analyzed_items
        ]

    # ── Build summary ──────────────────────────────────────────────────────
    total_billed = sum(i.billed_amount for i in analyzed_items)
    # total_payable counts only CONFIRMED payable amounts (PAYABLE + PARTIALLY_PAYABLE).
    # VERIFY_WITH_TPA items are tracked separately so users see an honest confirmed figure.
    total_payable = sum(
        i.payable_amount for i in analyzed_items
        if i.status in (PayabilityStatus.PAYABLE, PayabilityStatus.PARTIALLY_PAYABLE)
    )
    total_pending_verification = sum(
        i.payable_amount for i in analyzed_items
        if i.status == PayabilityStatus.VERIFY_WITH_TPA
    )
    total_at_risk = total_billed - total_payable - total_pending_verification
    rejection_rate = (total_at_risk / total_billed * 100) if total_billed > 0 else 0.0

    categories = [i.category for i in analyzed_items if i.status == PayabilityStatus.NOT_PAYABLE and i.category]
    top_categories = [cat for cat, _ in Counter(categories).most_common(3)]

    summary = AnalysisSummary(
        total_billed=round(total_billed, 2),
        total_payable=round(total_payable, 2),
        total_pending_verification=round(total_pending_verification, 2),
        total_at_risk=round(total_at_risk, 2),
        rejection_rate_pct=round(rejection_rate, 1),
        items_count=len(analyzed_items),
        not_payable_count=sum(1 for i in analyzed_items if i.status == PayabilityStatus.NOT_PAYABLE),
        partial_count=sum(1 for i in analyzed_items if i.status == PayabilityStatus.PARTIALLY_PAYABLE),
        verify_count=sum(1 for i in analyzed_items if i.status == PayabilityStatus.VERIFY_WITH_TPA),
        top_rejection_categories=top_categories,
    )

    action_items = _build_action_items(analyzed_items, summary, effective_room_rent_limit)

    # ── Persist analysis to DB ─────────────────────────────────────────────
    analysis_id = uuid.uuid4()
    analysis_orm = ClaimAnalysis(
        id=analysis_id,
        insurer_id=insurer.id,
        user_ref=request.user_ref,
        billing_mode=request.billing_mode.value,
        policy_type=request.policy_type.value,
        hospital_type=request.hospital_type.value,
        diagnosis=request.diagnosis,
        sum_insured=request.sum_insured,
        room_rent_limit=effective_room_rent_limit,
        total_billed=summary.total_billed,
        total_payable=summary.total_payable,
        total_pending_verification=summary.total_pending_verification,
        total_at_risk=summary.total_at_risk,
        rejection_rate_pct=summary.rejection_rate_pct,
        action_items=action_items,
    )
    db.add(analysis_orm)

    for item in analyzed_items:
        line_orm = BillLineItem(
            id=item.id,
            analysis_id=analysis_id,
            description=item.description,
            billed_amount=item.billed_amount,
            payable_amount=item.payable_amount,
            status=item.status.value,
            category=item.category,
            rule_matched=item.rule_matched,
            confidence=item.confidence,
            rejection_reason=item.rejection_reason,
            recovery_action=item.recovery_action,
            llm_used=item.llm_used,
        )
        db.add(line_orm)

    await db.commit()

    return AnalyzeResponse(
        analysis_id=analysis_id,
        insurer_name=insurer.name,
        insurer_code=insurer.code,
        billing_mode=request.billing_mode,
        diagnosis=request.diagnosis,
        line_items=analyzed_items,
        summary=summary,
        action_items=action_items,
    )


def _build_action_items(
    items: list[AnalyzedLineItem],
    summary: AnalysisSummary,
    effective_room_rent_limit: float | None,
) -> list[str]:
    actions = []

    if summary.total_at_risk > 0:
        actions.append(
            f"⚠️ ₹{summary.total_at_risk:,.0f} is at risk of rejection "
            f"({summary.rejection_rate_pct}% of your total bill)."
        )

    # Room rent exceeded
    room_items = [i for i in items if i.category in ("ROOM_RENT_EXCESS",)]
    if room_items and effective_room_rent_limit:
        actions.append(
            f"🏨 Room rent exceeds your policy cap of ₹{effective_room_rent_limit:,.0f}/day. "
            f"Request a room downgrade before discharge to prevent proportional deductions."
        )

    # Consumables
    consumable_items = [i for i in items if i.category == "CONSUMABLE" and i.status == PayabilityStatus.NOT_PAYABLE]
    if consumable_items:
        total = sum(i.billed_amount for i in consumable_items)
        actions.append(
            f"🧪 ₹{total:,.0f} in consumables are excluded. Ask the billing desk "
            f"to bundle them into procedure/OT package charges."
        )

    # Items needing TPA verification
    verify_items = [i for i in items if i.status == PayabilityStatus.VERIFY_WITH_TPA]
    if verify_items:
        actions.append(
            f"📞 {len(verify_items)} items need TPA verification before relying on them. "
            f"Call your TPA helpline before discharge."
        )

    if not actions:
        actions.append("✅ Your bill appears clean. Proceed with the normal claim process.")

    return actions
