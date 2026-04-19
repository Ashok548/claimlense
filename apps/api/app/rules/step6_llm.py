"""
Step 6 — GPT-4o LLM Fallback
Only invoked when no DB rule matched the item.
Sends a structured prompt to GPT-4o and parses the JSON response.
Result is marked with llm_used=True and confidence=0.72.
"""

import json
import uuid

from app.schemas import AnalyzedLineItem, BillItemInput, ConfidenceBasis, PayabilityStatus
from app.services.gpt_service import gpt_client, settings as gpt_settings

SYSTEM_PROMPT = """You are an Indian health insurance payability expert.
Classify the given hospital bill item for insurance payability under Indian health insurance.
You must return ONLY valid JSON. No explanation outside the JSON object.

JSON schema:
{
  "status": "PAYABLE" | "NOT_PAYABLE" | "PARTIALLY_PAYABLE" | "VERIFY_WITH_TPA",
  "confidence": 0.0 to 1.0,
  "payable_pct": number (0-100, only required when status is PARTIALLY_PAYABLE, e.g. 50),
  "category": "short category name",
  "reason": "concise explanation citing IRDAI rule or insurer pattern if applicable",
  "recovery_action": "what the patient can do to maximize payability"
}

The input includes a "pre_assigned_category" field — this is the item category already
determined by a prior classification step. Use it as strong context when deciding
the verdict. If it says DIAGNOSTIC_TEST, the item is a medical test and is generally
PAYABLE unless a specific exclusion applies. If it says CONSUMABLE, apply IRDAI rules.
If it says UNCLASSIFIED, use your own judgment.

Key rules to apply:
- IRDAI Circular IRDAI/HLT/REG/CIR/193/07/2020 excludes consumables, admin fees, non-medical items
- Equipment usage billed separately from procedures is NOT_PAYABLE
- Implants for surgery (stent, knee prosthesis) are PAYABLE with pre-auth
- Diagnostic tests (blood work, imaging, pathology) are PAYABLE
- If genuinely uncertain, use VERIFY_WITH_TPA
- Never assume PAYABLE for ambiguous items without justification"""


async def llm_classify_item(
    item: BillItemInput,
    insurer_name: str,
    diagnosis: str | None,
    billing_mode: str,
    item_category: str | None = None,
) -> AnalyzedLineItem:
    """
    Call GPT-4o to decide the payability verdict for an item no DB rule matched.
    Falls back to VERIFY_WITH_TPA if GPT call fails.

    item_category: pre-assigned category from Step 0. Passed as context so GPT
    focuses on deciding the verdict, not re-doing categorization work.
    """
    user_message = json.dumps(
        {
            "item_description": item.description,
            "billed_amount": item.billed_amount,
            "insurer": insurer_name,
            "diagnosis": diagnosis or "Not specified",
            "billing_mode": billing_mode,
            # Step 0 category gives GPT context; None means unknown
            "pre_assigned_category": item_category or "UNCLASSIFIED",
        },
        ensure_ascii=False,
    )

    try:
        response = await gpt_client.chat.completions.create(
            model=gpt_settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for deterministic classification
            max_tokens=400,
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        status = PayabilityStatus(data.get("status", "VERIFY_WITH_TPA"))
        confidence = float(data.get("confidence", 0.72))
        payable_pct = data.get("payable_pct")

        # If LLM declares PARTIALLY_PAYABLE but omits the percentage, we cannot
        # compute a reliable payable amount. Downgrade to VERIFY_WITH_TPA so the
        # item does not inflate the payable total with an unverified full-billed figure.
        if status == PayabilityStatus.PARTIALLY_PAYABLE and payable_pct is None:
            status = PayabilityStatus.VERIFY_WITH_TPA

        payable = _compute_payable(item.billed_amount, status, payable_pct)

        return AnalyzedLineItem(
            id=uuid.uuid4(),
            description=item.description,
            billed_amount=item.billed_amount,
            payable_amount=payable,
            status=status,
            category=data.get("category", "UNCLASSIFIED"),
            rule_matched="LLM:GPT4O",
            confidence=min(confidence, 0.80),  # Cap LLM confidence at 80%
            confidence_basis=ConfidenceBasis.LLM_REASONING,
            rejection_reason=data.get("reason") if status != PayabilityStatus.PAYABLE else None,
            recovery_action=data.get("recovery_action"),
            llm_used=True,
        )

    except Exception:
        # GPT failed — safe fallback
        return _default_verify(item)


def _compute_payable(billed: float, status: PayabilityStatus, payable_pct: float | None) -> float:
    if status == PayabilityStatus.PAYABLE:
        return billed
    if status == PayabilityStatus.NOT_PAYABLE:
        return 0.0
    if status == PayabilityStatus.PARTIALLY_PAYABLE and payable_pct is not None:
        return round(billed * (float(payable_pct) / 100), 2)
    # VERIFY_WITH_TPA (or PARTIALLY_PAYABLE already downgraded before this call)
    # — show full billed as the at-risk figure visible to the user.
    return billed


def _default_verify(item: BillItemInput) -> AnalyzedLineItem:
    """Safe fallback when GPT-4o is unavailable."""
    return AnalyzedLineItem(
        id=uuid.uuid4(),
        description=item.description,
        billed_amount=item.billed_amount,
        payable_amount=item.billed_amount,
        status=PayabilityStatus.VERIFY_WITH_TPA,
        category="UNCLASSIFIED",
        rule_matched="DEFAULT:VERIFY",
        confidence=0.55,
        confidence_basis=ConfidenceBasis.UNCLASSIFIED,
        rejection_reason=None,
        recovery_action=(
            "This item could not be automatically classified. "
            "Verify payability with your TPA before discharge."
        ),
        llm_used=False,
    )
