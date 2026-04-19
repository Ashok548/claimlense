// Mapped to FastAPI schemas

export enum PayabilityStatus {
  PAYABLE = "PAYABLE",
  NOT_PAYABLE = "NOT_PAYABLE",
  PARTIALLY_PAYABLE = "PARTIALLY_PAYABLE",
  VERIFY_WITH_TPA = "VERIFY_WITH_TPA",
}

export enum BillingMode {
  ITEMIZED = "itemized",
  PACKAGE = "package",
  MIXED = "mixed",
}

export enum PolicyType {
  INDIVIDUAL = "individual",
  FLOATER = "floater",
  GROUP = "group",
}

export enum HospitalType {
  EMPANELLED = "empanelled",
  NON_EMPANELLED = "non_empanelled",
}

export interface BillItemInput {
  id: string; // Used for frontend table rows only
  description: string;
  billed_amount: number;
}

export interface AnalyzeRequest {
  insurer_code: string;
  plan_code: string;
  rider_codes: string[];
  policy_type: PolicyType;
  hospital_type: HospitalType;
  billing_mode: BillingMode;
  diagnosis?: string;
  sum_insured: number;
  icu_days?: number;
  general_ward_days?: number;
  bill_items: Omit<BillItemInput, "id">[];
}

export interface RiderDetail {
  id: string;
  code: string;
  name: string;
  description: string | null;
  covers_consumables: boolean;
  covers_opd: boolean;
  covers_maternity: boolean;
  covers_dental: boolean;
  covers_critical_illness: boolean;
  additional_sum_insured: number | null;
}

export interface PlanDetail {
  id: string;
  code: string;
  name: string;
  description: string | null;
  room_rent_limit_pct: number | null;
  room_rent_limit_abs: number | null;
  co_pay_pct: number | null;
  icu_limit_pct: number | null;
  consumables_covered: boolean;
  consumables_sublimit: number | null;
  riders: RiderDetail[];
}

export interface AnalysisSummary {
  total_billed: number;
  total_payable: number;
  total_pending_verification: number;
  total_at_risk: number;
  rejection_rate_pct: number;
  items_count: number;
  not_payable_count: number;
  partial_count: number;
  verify_count: number;
  top_rejection_categories: string[];
}

export interface InsurerResponse {
  id: string;
  code: string;
  name: string;
  logo_url: string | null;
  plans: PlanDetail[] | null;
  room_rent_default: number | null;
}

export interface ParsedItemResponse {
  description: string;
  billed_amount: number;
  days?: number | null;
}

export interface ParseResponse {
  job_id: string;
  items: ParsedItemResponse[];
  raw_item_count: number;
  parse_method: string;
  admission_date?: string | null;
  discharge_date?: string | null;
  icu_days?: number | null;
  general_ward_days?: number | null;
  total_days?: number | null;
}
