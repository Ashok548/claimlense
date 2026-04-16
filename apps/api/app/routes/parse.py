"""FastAPI routes — POST /v1/parse (OCR + GPT-4o structured extraction)"""

import json

from fastapi import APIRouter, HTTPException
import asyncio

from app.schemas import ParseRequest, ParseResponse, ParsedItem
from app.services.ocr_service import extract_text
from app.services.s3_service import download_file
from app.services.gpt_service import gpt_client, settings as gpt_settings

router = APIRouter(prefix="/v1/parse", tags=["parse"])

PARSE_SYSTEM_PROMPT = """You are an expert in hospital bill parsing and financial data extraction.

Your task has TWO parts:
1. Extract all valid billable line items from the hospital invoice.
2. Extract hospital stay duration details (admission date, discharge date, ICU days, ward days).

---

### PART A — BILL ITEMS — CRITICAL RULES:

1. DO NOT include summary rows or category headers.

Examples of headers (DO NOT include):
- ROOM CHARGES
- CONSULTATION CHARGES
- INVESTIGATION CHARGES
- SERVICE CHARGES
- Any row that represents a total of sub-items

---

2. ONLY include leaf-level items (actual billed services)

Examples (VALID):
- Warmer Charges - NICU
- DMO Charges - NICU
- Dr. T.V. Nagaraju
- X-Ray Chest
- Ultrasound Scan
- Blood Test

---

3. Avoid double counting

If a parent total equals the sum of child items:
- Ignore the parent
- Include only child items

---

4. Each item must have:
- description
- billed_amount

---

5. If quantity and rate are present:
- Calculate billed_amount = qty × rate
- If billed_amount already exists, use it

---

6. Output STRICT JSON format:

{
  "items": [
    {
      "description": "string",
      "billed_amount": number
    }
  ],
  "total": number
}

---

7. Total must be:
- Sum of ONLY the extracted leaf-level items
- No duplicates
- No headers included

---

8. Be careful:
- Do NOT repeat same amount under different labels
- Do NOT include both doctor name and consultation total if they represent same charge

---

9. If unsure whether a row is header or item:
- If it has sub-items → treat as header (exclude)
- If it has qty/rate → treat as item (include)

10. Only count positive numbers. If there are any negative numbers, ignore them.

11. If an item shows quantity/days and rate (e.g. "ICU Charges - 5 days @ ₹3,000"), set the `days` field on that item to the number of days.

---

### PART B — HOSPITAL STAY DURATION:

Look for and extract the following from any part of the bill (header, footer, summary, line items):

- `admission_date`: Date of admission (string, e.g. "15-Mar-2026" or "2026-03-15"). Null if not found.
- `discharge_date`: Date of discharge (string). Null if not found.
- `icu_days`: Total number of days in ICU / ICCU / HDU / NICU / PICU. Sum across all such line items if multiplied out. Null if not found.
- `general_ward_days`: Total days in general ward, private room, semi-private, AC room, or standard bed. Null if not found.
- `total_days`: Total length of hospital stay in days. Prefer explicit value from bill. If not explicit, calculate as icu_days + general_ward_days if both present. If not computable, derive from admission/discharge dates. Null if unknown.

Examples of how days appear on bills:
- "ICU Charges - 5 Days @ ₹5,000" → icu_days: 5
- "General Ward - 3 days × ₹2,000" → general_ward_days: 3
- "Room Rent (10 days)" → general_ward_days: 10 (if no ICU)
- "Date of Admission: 10-Mar-2026" → admission_date: "10-Mar-2026"
- "Discharge Date: 15-Mar-2026" → discharge_date: "15-Mar-2026"

---

### OUTPUT FORMAT:

Return STRICT JSON with BOTH parts:

{
  "items": [
    {
      "description": "string",
      "billed_amount": number,
      "days": number_or_null
    }
  ],
  "total": number,
  "admission_date": "string_or_null",
  "discharge_date": "string_or_null",
  "icu_days": number_or_null,
  "general_ward_days": number_or_null,
  "total_days": number_or_null
}

---

### GOAL:
Return accurate, non-duplicated, billable items AND complete stay duration information."""


@router.post("/", response_model=ParseResponse)
async def parse_bill(request: ParseRequest) -> ParseResponse:
    try:
        # 1. Download from R2 (run in thread because botocore is sync)
        file_bytes = await asyncio.to_thread(download_file, request.s3_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download file from R2: {e}")

    import base64
    
    ocr_method = "gpt4o-vision"
    raw_text = ""
    
    if request.file_type == "pdf":
        try:
            # 2. OCR extraction for PDF
            raw_text, ocr_method = await asyncio.to_thread(extract_text, file_bytes, request.file_type)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF OCR failed: {e}")

        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="No text could be extracted from the PDF.")

    try:
        # 3. GPT-4o structured extraction
        admission_date: str | None = None
        discharge_date: str | None = None
        icu_days: int | None = None
        general_ward_days: int | None = None
        total_days: int | None = None
        messages = [
            {"role": "system", "content": PARSE_SYSTEM_PROMPT.replace("text below", "document below")},
        ]

        if request.file_type == "image":
            # Pass image directly to GPT-4o Vision
            base64_image = base64.b64encode(file_bytes).decode("utf-8")
            messages.append({
                "role": "user", 
                "content": [
                    {"type": "text", "text": "Extract items from this hospital bill image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            })
        else:
            # Pass extracted text for PDFs
            messages.append({"role": "user", "content": raw_text[:24000]})

        response = await gpt_client.chat.completions.create(
            model=gpt_settings.openai_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        # GPT returns {"items": [...], "icu_days": ..., ...} or directly [...]
        data = json.loads(content)
        raw_items = data if isinstance(data, list) else data.get("items", [])

        items = [
            ParsedItem(
                description=str(it.get("description", "")).strip(),
                billed_amount=float(it.get("billed_amount", 0) or 0),
                days=int(it["days"]) if it.get("days") and int(it.get("days", 0) or 0) > 0 else None,
            )
            for it in raw_items
            if it.get("description") and float(it.get("billed_amount", 0) or 0) > 0
        ]

        def _safe_int(val: any) -> int | None:
            try:
                v = int(val)
                return v if v > 0 else None
            except (TypeError, ValueError):
                return None

        icu_days = _safe_int(data.get("icu_days"))
        general_ward_days = _safe_int(data.get("general_ward_days"))
        total_days = _safe_int(data.get("total_days"))

        # Derive total_days from parts if GPT didn't provide it
        if total_days is None and (icu_days or general_ward_days):
            total_days = (icu_days or 0) + (general_ward_days or 0) or None

        admission_date = str(data["admission_date"]).strip() if data.get("admission_date") else None
        discharge_date = str(data["discharge_date"]).strip() if data.get("discharge_date") else None

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT-4o parsing failed: {e}")

    return ParseResponse(
        job_id=request.job_id,
        items=items,
        raw_item_count=len(items),
        parse_method=f"{ocr_method}+gpt4o",
        admission_date=admission_date,
        discharge_date=discharge_date,
        icu_days=icu_days,
        general_ward_days=general_ward_days,
        total_days=total_days,
    )
