# ClaimSmart — Implementation Phases

> **Root:** `c:\Users\Rupa\Documents\Ashok Projects\claimAnalyse`
> **Architecture:** Next.js 15 (BFF) + FastAPI (Intelligence) + PostgreSQL + Cloudflare R2
> **Last updated:** April 2026

---

## ✅ Phase 1 — DONE: Backend Foundation + FastAPI Intelligence Core

- [x] Monorepo structure (`apps/api`, `apps/web`)
- [x] `docker-compose.yml` — PostgreSQL + FastAPI + Next.js
- [x] FastAPI: all ORM models, Pydantic schemas, config, database engine
- [x] FastAPI: 7-step rule engine (steps 1–6 + default)
- [x] FastAPI: routes — `/v1/analyze`, `/v1/parse`, `/v1/insurers`
- [x] FastAPI: services — GPT-4o, OCR (pdfplumber + pytesseract), Cloudflare R2
- [x] Alembic: 5 migrations — schema + IRDAI seed + 7 insurers + rules + diagnosis overrides
- [x] Next.js 15 scaffold + Tailwind + shadcn/ui (13 components)
- [x] Prisma schema — users, reports, upload_jobs, payments
- [x] Landing page (dark, animated, live bill preview)
- [x] Design system (CSS tokens, payability colors, glassmorphism)

---

## 🔴 Phase 2 — Analyze Wizard + Results Dashboard (NEXT)

> **Goal:** Users can manually enter bill items and get a full analysis displayed.
> **Estimated time:** 3–5 days

### 2.1 — Multi-Step Analyze Wizard (`/analyze`)

**File:** `apps/web/app/analyze/page.tsx`

```
Step 1 → Select Insurer        (cards with logo + plan selector)
Step 2 → Policy Details        (sum insured, room rent limit, type, hospital type)
Step 3 → Diagnosis             (free text with auto-suggest)
Step 4 → Enter Bill Items      (dynamic table: add/edit/delete rows)
Step 5 → Review & Submit
```

**Components to build:**
- `components/InsurerSelector.tsx` — grid of insurer cards, fetchs from `/api/insurers`
- `components/PolicyForm.tsx`     — sum insured, room rent, type dropdowns
- `components/BillEntryTable.tsx` — dynamic row add/edit/delete, amount formatting
- `components/StepIndicator.tsx`  — numbered step breadcrumb
- `hooks/useAnalyze.ts`           — manages wizard state and API calls

**API route:**
- `app/api/analyze/route.ts` — Next.js BFF: auth check (optional) → POST to FastAPI `/v1/analyze` → save report to Prisma → return response

### 2.2 — Results Dashboard (`/results/[id]`)

**File:** `apps/web/app/results/[id]/page.tsx`

**Sections:**
1. **Summary Cards** — Billed / Payable / At Risk / Rejection %
2. **Line Items Table** — color-coded by status, confidence badge, reason, recovery action
3. **Pre-Discharge Action Checklist** — prioritized list of things to do NOW
4. **Download Report button** (Phase 3)
5. **WhatsApp Share button**

**Components to build:**
- `components/SummaryCards.tsx`    — 4 animated metric cards
- `components/ResultsTable.tsx`    — sortable table with status colors
- `components/ConfidenceBadge.tsx` — color + icon + tooltip
- `components/ActionChecklist.tsx` — expandable action items
- `components/ShareButtons.tsx`    — WhatsApp + copy link

### 2.3 — Insurer API Proxy (BFF)

**File:** `app/api/insurers/route.ts`
- GET → fetch from FastAPI `/v1/insurers` → cache for 10 min → return to browser

### 2.4 — FastAPI Docker + Local Dev Setup

**Files:**
- `apps/api/Dockerfile`
- `apps/web/Dockerfile`
- `.env` creation steps in README

---

## 🟠 Phase 3 — File Upload + PDF Report Generation

> **Goal:** Users can upload a PDF/image hospital bill, items are auto-extracted.
> Also generates a downloadable PDF advisory report.
> **Estimated time:** 3–4 days

### 3.1 — File Upload to Cloudflare R2

**File:** `app/api/upload/route.ts`
- Accept multipart file upload
- Validate: PDF or image, max 10MB
- Upload to R2: key = `bills/{userId}/{jobId}.{ext}`
- Create `UploadJob` record in Prisma (status: PENDING)
- Return `{ jobId, s3Key }`

**Component:** `components/UploadZone.tsx`
- Drag-and-drop zone (react-dropzone)
- Upload progress bar
- File preview (PDF first page thumbnail)
- Error handling (wrong format, too large)

### 3.2 — OCR + GPT-4o Item Extraction

**BFF Route:** `app/api/parse/route.ts`
- POST `{ jobId, s3Key, fileType }` → FastAPI `/v1/parse`
- FastAPI downloads from R2 → OCR → GPT-4o → returns items
- Update `UploadJob` status to PARSED

**UI:** Extracted items review screen (Step 4 of wizard)
- Show items from parse result
- Allow user to edit/delete/add before submitting analysis
- Works for both upload and manual entry paths

### 3.3 — PDF Report Generation

**FastAPI Route:** `/v1/report`
- `report_service.py` using `reportlab`
- Generates branded PDF: summary + table + action checklist + disclaimer
- Uploads PDF to R2: `reports/{analysisId}.pdf`
- Returns presigned download URL (1 hour validity)

**BFF Route:** `app/api/reports/[id]/pdf/route.ts`
- POST → call FastAPI `/v1/report` → returns presigned URL to browser

**Report PDF contents:**
```
Page 1: Header (insurer, date, diagnosis)
        Executive Summary (4 metric cards)
        Action Items
Page 2: Line item table (all items, status, amounts, reasons)
Page 3: Recovery Guide (per rejected category)
        Disclaimer + IRDAI circular references
```

---

## 🔵 Phase 4 — Authentication + User Dashboard

> **Goal:** Users can log in, see their report history, use saved credits.
> **Estimated time:** 3–4 days

### 4.1 — NextAuth.js v5 Setup

**Files:**
- `app/api/auth/[...nextauth]/route.ts`
- `lib/auth.ts` — NextAuth config

**Providers:**
- **Google OAuth** (primary — easiest for Indian users)
- **OTP/Email** (via Resend for sending OTPs — no password needed)
- **Magic Link** (optional — email-based passwordless)

**Middleware:**
- `middleware.ts` — protect `/dashboard`, `/results` routes

### 4.2 — Login / Signup Pages

**Files:**
- `app/(auth)/login/page.tsx`  — Google + OTP options
- `app/(auth)/verify/page.tsx` — OTP verify screen

### 4.3 — User Dashboard (`/dashboard`)

**File:** `app/dashboard/page.tsx`

**Sections:**
- **Credits remaining** (3 free, buy more)
- **Past reports table** — date, insurer, at-risk amount, status
- **Download buttons** (free: summary, paid: full PDF)

**Components:**
- `components/ReportHistoryTable.tsx`
- `components/CreditBadge.tsx`

**BFF Routes:**
- `app/api/reports/route.ts` — GET: list user's reports (Prisma query)
- `app/api/reports/[id]/route.ts` — GET: single report details

### 4.4 — Credit Gating

Logic in `app/api/analyze/route.ts`:
```
if not logged in:
  → allow (anonymous, counted by cookie, 1 free)
if logged in + credits > 0:
  → allow, decrement credits
if logged in + credits === 0:
  → return 402 Payment Required
  → frontend shows upgrade modal
```

---

## 🟡 Phase 5 — Payments + Freemium Model

> **Goal:** Monetize via Razorpay. Credits, PDF reports, appeal letters.
> **Estimated time:** 3–4 days

### 5.1 — Razorpay Integration

**Files:**
- `app/api/payment/create/route.ts` — Create Razorpay order
- `app/api/payment/verify/route.ts` — Verify HMAC signature → grant credits

**Credit Packs:**
```
₹49  → 1 basic analysis (summary only)
₹99  → 1 analysis + PDF report
₹299 → 5 analyses + PDF reports
₹999 → 20 analyses + PDFs + appeal letters
```

**Component:** `components/PaymentModal.tsx`
- Plan cards with Razorpay checkout
- Loading state + success redirect to dashboard

### 5.2 — Pricing Page (`/pricing`)

**File:** `app/pricing/page.tsx`

| Plan | Price | Features |
|---|---|---|
| Free | ₹0 | 3 analyses, summary only |
| Basic | ₹49 | 1 analysis + PDF |
| Pro | ₹299 | 5 analyses + PDFs |
| Unlimited | ₹999 | 20 + appeal letters |

### 5.3 — Appeal Letter Generator (GPT-4o)

**FastAPI Route:** `POST /v1/appeal-letter`
- Takes rejected items + patient info
- GPT-4o generates formal letter
- Cites: IRDAI Grievance process, Insurance Ombudsman, IRDAI Bima Bharosa
- Returns PDF appeal letter

**Trigger:** Premium feature after analysis — "Generate Appeal Letter" button

---

## 🟣 Phase 6 — Intelligence Upgrades + B2B

> **Goal:** Advanced AI features and scalability for B2B customers.
> **Estimated time:** 1–2 weeks

### 6.1 — Duplicate Billing Detector

**FastAPI logic in engine.py:**
- After all items analyzed, scan for duplicates
- Flag: same description billed twice, same amount with different names
- Add to `action_items` in analysis response

### 6.2 — Admin Rules Dashboard (Next.js)

**File:** `app/admin/rules/page.tsx`
- CRUD interface for `exclusion_rules`, `insurer_rules`, `diagnosis_overrides`
- No Alembic needed for updates — direct Prisma/FastAPI calls
- Protected by admin role check

### 6.3 — B2B API

- API key system (table: `api_keys` with rate limits)
- Webhook support (POST analysis result to client URL)
- Usage analytics dashboard for B2B clients

### 6.4 — RAG Pipeline (Policy PDFs)

- Embed insurer policy PDFs using OpenAI embeddings
- Store in pgvector (PostgreSQL extension)
- RAG retrieval: "Is robotic surgery covered under HDFC Optima Secure?"
- Supplement rule engine with real policy sub-limits

### 6.5 — Claim History Analytics

**File:** `app/dashboard/analytics/page.tsx`
- Rejection trend charts (Recharts)
- Most rejected categories per insurer
- Month-over-month comparison

---

## Local Dev Quick Start

```bash
# 1. Start PostgreSQL (requires Docker Desktop)
docker compose up postgres -d

# 2. Set up FastAPI
cd apps/api
copy .env.example .env        # Fill in OPENAI_API_KEY + R2 credentials
pip install -r requirements.txt
alembic upgrade head           # Creates tables + seeds all data
uvicorn main:app --reload --port 8000

# 3. Start Next.js
cd apps/web
copy .env.example .env.local   # Fill in DATABASE_URL
npx prisma migrate dev --name init
npm run dev                    # http://localhost:3000
```

> **Without Docker:** Install PostgreSQL 16 directly on Windows from https://www.postgresql.org/download/windows/
> After install, create DB: `psql -U postgres -c "CREATE DATABASE claimsmart;"`
> Then use `DATABASE_URL=postgresql://postgres:<password>@localhost:5432/claimsmart`

---

## Current Status

| Phase | Status | What's built |
|---|---|---|
| Phase 1 | ✅ Complete | FastAPI + DB + Rule Engine + Next.js scaffold + Landing |
| Phase 2 | 🔴 Next | Analyze wizard + Results dashboard |
| Phase 3 | ⬜ Pending | File upload + OCR + PDF report |
| Phase 4 | ⬜ Pending | Auth + User dashboard + Credits |
| Phase 5 | ⬜ Pending | Razorpay + Freemium + Appeal letters |
| Phase 6 | ⬜ Pending | B2B API + Admin + RAG + Analytics |
