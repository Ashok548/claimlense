import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ShieldCheck, HelpCircle, BrainCircuit, AlertCircle, Calculator } from "lucide-react";

interface Props {
  confidence: number; // 0.0 to 1.0
  basis: string;      // raw rule_matched string from the engine
}

/**
 * Translates internal engine rule codes into plain-English labels.
 *
 * Rule patterns produced by the engine (may be pipe-joined, e.g.
 * "IRDAI:NON_MEDICAL:gloves|COPAY"):
 *   IRDAI:<CATEGORY>:<keyword>       – matched an IRDAI non-payable rule
 *   IRDAI:<CATEGORY>:CATEGORY_MATCH  – matched by category alone
 *   DIAGNOSIS:<kw1>:<kw2>           – diagnosis-specific override
 *   ROOM_RENT:NO_LIMIT              – no room-rent cap on this policy
 *   ROOM_RENT:WITHIN_LIMIT          – room rent within allowed limit
 *   ROOM_RENT:EXCEEDS_LIMIT:<amt>   – room rent exceeds cap
 *   ROOM_RENT:DAYS_UNKNOWN          – stay duration could not be determined
 *   INSURER:<CATEGORY>:<keyword>    – insurer-specific rule matched
 *   CATEGORY_DEFAULT:<CATEGORY>     – fallback category classification
 *   LLM:GPT4O                       – AI evaluated (no hard rule found)
 *   DEFAULT:VERIFY                  – could not classify; needs TPA check
 *   CALCULATION                     – exact mathematical calculation
 *   |COPAY                          – co-pay modifier applied
 *   |PROPORTIONAL_DEDUCTION         – proportional deduction applied
 *   |SUBLIMIT_<CATEGORY>            – sub-limit cap applied
 */
function humanizeRuleCode(raw: string): string {
  if (!raw || raw === "Unknown") return "Not determined";

  // Split pipe-joined modifiers: primary|MODIFIER1|MODIFIER2
  const parts = raw.split("|");
  const primary = parts[0].trim();
  const modifiers = parts.slice(1).map((m) => m.trim());

  // ── Translate primary rule ────────────────────────────────────────
  let label = translatePrimary(primary);

  // ── Translate modifiers ───────────────────────────────────────────
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
  // CALCULATION
  if (code === "CALCULATION") return "Exact mathematical calculation";

  // LLM:GPT4O
  if (code === "LLM:GPT4O") return "Our Engine evaluation (LLM)";

  // DEFAULT:VERIFY
  if (code === "DEFAULT:VERIFY") return "Unclassified — TPA verification required";

  // ROOM_RENT variants
  if (code === "ROOM_RENT:NO_LIMIT")
    return "Room rent — no cap on this policy";
  if (code === "ROOM_RENT:WITHIN_LIMIT")
    return "Room rent — within policy limit";
  if (code === "ROOM_RENT:DAYS_UNKNOWN")
    return "Room rent — stay duration unknown";
  if (code.startsWith("ROOM_RENT:EXCEEDS_LIMIT:")) {
    const limit = code.split(":")[2];
    const limitFmt = limit ? `₹${Number(limit).toLocaleString()}` : "";
    return `Room rent — exceeds policy limit${limitFmt ? ` (cap: ${limitFmt}/day)` : ""}`;
  }

  // IRDAI:<CATEGORY>:CATEGORY_MATCH
  if (code.startsWith("IRDAI:") && code.endsWith(":CATEGORY_MATCH")) {
    const category = code.split(":")[1];
    return `IRDAI guideline — ${humanizeCategory(category)} (category match)`;
  }

  // IRDAI:<CATEGORY>:<keyword>
  if (code.startsWith("IRDAI:")) {
    const [, category, keyword] = code.split(":");
    if (category && keyword) {
      return `IRDAI guideline — ${humanizeCategory(category)} ("${keyword}")`;
    }
    if (category) {
      return `IRDAI guideline — ${humanizeCategory(category)}`;
    }
  }

  // DIAGNOSIS:<diagnosis>:<keyword>
  if (code.startsWith("DIAGNOSIS:")) {
    const [, diagnosis, keyword] = code.split(":");
    if (diagnosis && keyword) {
      return `Diagnosis-specific rule — ${humanizeDiagnosis(diagnosis)} ("${keyword}")`;
    }
    if (diagnosis) {
      return `Diagnosis-specific rule — ${humanizeDiagnosis(diagnosis)}`;
    }
  }

  // INSURER:<CATEGORY>:<keyword>
  if (code.startsWith("INSURER:")) {
    const [, category, keyword] = code.split(":");
    if (category && keyword) {
      return `Insurer-specific rule — ${humanizeCategory(category)} ("${keyword}")`;
    }
    if (category) {
      return `Insurer-specific rule — ${humanizeCategory(category)}`;
    }
  }

  // CATEGORY_DEFAULT:<CATEGORY>
  if (code.startsWith("CATEGORY_DEFAULT:")) {
    const category = code.split(":")[1];
    return `Default classification — ${humanizeCategory(category)}`;
  }

  // Fallback: prettify the raw code
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

/** Converts SNAKE_CASE category codes → Title Case readable labels */
function humanizeCategory(code: string): string {
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
  // Diagnosis keywords are typically plain words stored lowercase
  return code
    .split(/[_\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

/* ─── Component ───────────────────────────────────────────────────── */
export function ConfidenceBadge({ confidence, basis }: Props) {
  const pct = Math.round(confidence * 100);

  let color = "bg-slate-800 text-slate-300";
  let icon = <HelpCircle className="w-3 h-3 mr-1" />;
  let description = "Uncertain AI prediction";

  if (pct >= 95) {
    color = "bg-green-500/20 text-green-400 border-green-500/30";
    if (basis === "CALCULATION") {
      icon = <Calculator className="w-3 h-3 mr-1" />;
      description = "Exact mathematical calculation (e.g. Room Rent)";
    } else {
      icon = <ShieldCheck className="w-3 h-3 mr-1" />;
      description = "High confidence — strict IRDAI / insurer rule matched";
    }
  } else if (pct >= 80) {
    color = "bg-sky-500/20 text-sky-400 border-sky-500/30";
    icon = <ShieldCheck className="w-3 h-3 mr-1" />;
    description = "Good confidence — known insurer pattern matched";
  } else if (pct >= 70) {
    color = "bg-purple-500/20 text-purple-400 border-purple-500/30";
    icon = <BrainCircuit className="w-3 h-3 mr-1" />;
    description = "AI inferred from similar historic claims";
  } else {
    color = "bg-orange-500/20 text-orange-400 border-orange-500/30";
    icon = <AlertCircle className="w-3 h-3 mr-1" />;
    description = "Low confidence — TPA verification strongly advised";
  }

  const sourceLabel = humanizeRuleCode(basis);

  return (
    <Tooltip>
      <TooltipTrigger>
        <Badge variant="outline" className={`cursor-help ${color}`}>
          {icon}
          {pct}%
        </Badge>
      </TooltipTrigger>
      <TooltipContent className="bg-slate-800 border-white/10 text-white p-3 max-w-xs">
        <p className="font-semibold mb-1">Confidence Score: {pct}%</p>
        <p className="text-sm text-slate-300">{description}</p>
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">
          <span className="text-slate-500">Source: </span>
          {sourceLabel}
        </p>
      </TooltipContent>
    </Tooltip>
  );
}
