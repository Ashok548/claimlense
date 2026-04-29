/**
 * Format a number as Indian-locale currency (comma as thousands separator).
 * Uses 'en-US' locale for consistent rendering on server + client.
 */
export function formatCurrency(amount: number): string {
  return amount.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

/**
 * Translates internal engine rule codes into plain-English labels.
 *
 * Rule patterns (may be pipe-joined, e.g. "IRDAI:NON_MEDICAL:gloves|COPAY"):
 *   IRDAI:<CATEGORY>:<keyword>       – matched an IRDAI non-payable rule
 *   IRDAI:<CATEGORY>:CATEGORY_MATCH  – matched by category alone
 *   DIAGNOSIS:<kw1>:<kw2>            – diagnosis-specific override
 *   ROOM_RENT:NO_LIMIT               – no room-rent cap on this policy
 *   ROOM_RENT:WITHIN_LIMIT           – room rent within allowed limit
 *   ROOM_RENT:EXCEEDS_LIMIT:<amt>    – room rent exceeds cap
 *   ROOM_RENT:DAYS_UNKNOWN           – stay duration could not be determined
 *   INSURER:<CATEGORY>:<keyword>     – insurer-specific rule matched
 *   CATEGORY_DEFAULT:<CATEGORY>      – fallback category classification
 *   LLM:GPT4O                        – AI evaluated (no hard rule found)
 *   DEFAULT:VERIFY                   – could not classify; needs TPA check
 *   CALCULATION                      – exact mathematical calculation
 *   |COPAY                           – co-pay modifier applied
 *   |PROPORTIONAL_DEDUCTION          – proportional deduction applied
 *   |SUBLIMIT_<CATEGORY>             – sub-limit cap applied
 */
export function humanizeRuleCode(raw: string): string {
  if (!raw || raw === "Unknown") return "Not determined";

  const parts = raw.split("|");
  const primary = parts[0].trim();
  const modifiers = parts.slice(1).map((m) => m.trim());

  let label = translatePrimary(primary);

  const modifierLabels = modifiers
    .map(translateModifier)
    .filter(Boolean)
    .join(", ");

  if (modifierLabels) {
    label += ` + ${modifierLabels}`;
  }

  return label;
}

function translatePrimary(code: string): string {
  if (code === "CALCULATION") return "Exact mathematical calculation";
  if (code === "LLM:GPT4O") return "AI model evaluation (GPT-4o)";
  if (code === "DEFAULT:VERIFY") return "Unclassified — TPA verification required";

  if (code === "ROOM_RENT:NO_LIMIT") return "Room rent — no cap on this policy";
  if (code === "ROOM_RENT:WITHIN_LIMIT") return "Room rent — within policy limit";
  if (code === "ROOM_RENT:DAYS_UNKNOWN") return "Room rent — stay duration unknown";
  if (code.startsWith("ROOM_RENT:EXCEEDS_LIMIT:")) {
    const limit = code.split(":")[2];
    const limitFmt = limit ? `₹${Number(limit).toLocaleString()}` : "";
    return `Room rent — exceeds policy limit${limitFmt ? ` (cap: ${limitFmt}/day)` : ""}`;
  }

  if (code.startsWith("IRDAI:") && code.endsWith(":CATEGORY_MATCH")) {
    const category = code.split(":")[1];
    return `IRDAI guideline — ${humanizeCategory(category)} (category match)`;
  }
  if (code.startsWith("IRDAI:")) {
    const [, category, keyword] = code.split(":");
    if (category && keyword) return `IRDAI guideline — ${humanizeCategory(category)} ("${keyword}")`;
    if (category) return `IRDAI guideline — ${humanizeCategory(category)}`;
  }

  if (code.startsWith("DIAGNOSIS:")) {
    const [, diagnosis, keyword] = code.split(":");
    if (diagnosis && keyword) return `Diagnosis-specific rule — ${humanizeDiagnosis(diagnosis)} ("${keyword}")`;
    if (diagnosis) return `Diagnosis-specific rule — ${humanizeDiagnosis(diagnosis)}`;
  }

  if (code.startsWith("INSURER:")) {
    const [, category, keyword] = code.split(":");
    if (category && keyword) return `Insurer-specific rule — ${humanizeCategory(category)} ("${keyword}")`;
    if (category) return `Insurer-specific rule — ${humanizeCategory(category)}`;
  }

  if (code.startsWith("CATEGORY_DEFAULT:")) {
    const category = code.split(":")[1];
    return `Default classification — ${humanizeCategory(category)}`;
  }

  return code.replace(/_/g, " ").replace(/:/g, " › ");
}

function translateModifier(mod: string): string {
  if (mod === "COPAY") return "co-pay applied";
  if (mod === "PROPORTIONAL_DEDUCTION") return "proportional deduction applied";
  if (mod.startsWith("SUBLIMIT_")) {
    const cat = mod.replace("SUBLIMIT_", "");
    return `${humanizeCategory(cat)} sub-limit cap`;
  }
  return mod.replace(/_/g, " ").toLowerCase();
}

/** Converts SNAKE_CASE category codes → readable labels */
export function humanizeCategory(code: string): string {
  const map: Record<string, string> = {
    NON_MEDICAL: "Non-medical item",
    ROOM_RENT: "Room rent",
    CONSUMABLE: "Consumable / disposable",
    CONSUMABLE_SUBLIMIT: "Consumable (sub-limit)",
    SURGICAL_PROCEDURE: "Surgical procedure",
    ANAESTHESIA: "Anaesthesia",
    DIAGNOSTIC: "Diagnostic test",
    PHARMACY: "Pharmacy / medicine",
    PHARMACY_COPAY: "Pharmacy (co-pay)",
    OPD: "OPD / outpatient",
    NURSING: "Nursing charges",
    ICU: "ICU charges",
    EQUIPMENT: "Medical equipment",
    DOCTOR_FEE: "Doctor / consultation fee",
    SURGEON_CONSULTATION: "Surgeon consultation",
    MODERN_TREATMENT: "Modern / advanced treatment",
    CATARACT_PACKAGE: "Cataract package",
    ROOM_UPGRADE_COPAY: "Room upgrade (co-pay)",
    PRE_EXISTING: "Pre-existing condition",
    EXCLUSION: "Policy exclusion",
    ADMINISTRATIVE: "Administrative charge",
    MISCELLANEOUS: "Miscellaneous",
    UNKNOWN: "Unclassified",
  };
  return map[code] ?? code.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function humanizeDiagnosis(code: string): string {
  return code
    .split(/[_\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

/**
 * Maps PayabilityStatus codes to display config.
 * Pure data — usable on web and mobile.
 */
export function getStatusConfig(status: string): { label: string; key: string } {
  switch (status) {
    case "PAYABLE":
      return { label: "PAYABLE", key: "payable" };
    case "NOT_PAYABLE":
      return { label: "REJECTED", key: "not_payable" };
    case "PARTIALLY_PAYABLE":
      return { label: "PARTIAL", key: "partial" };
    case "VERIFY_WITH_TPA":
      return { label: "VERIFY", key: "verify" };
    default:
      return { label: status, key: "unknown" };
  }
}
