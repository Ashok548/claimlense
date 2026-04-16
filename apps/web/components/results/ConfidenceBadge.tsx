import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ShieldCheck, HelpCircle, BrainCircuit, AlertCircle, Calculator } from "lucide-react";

interface Props {
  confidence: number; // 0.0 to 1.0
  basis: string; // IRDAI_RULE, LLM_REASONING, etc
}

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
      description = "High confidence based on strict IRDAI/Insurer rules";
    }
  } else if (pct >= 80) {
    color = "bg-sky-500/20 text-sky-400 border-sky-500/30";
    icon = <ShieldCheck className="w-3 h-3 mr-1" />;
    description = "Good confidence based on known insurer patterns";
  } else if (pct >= 70) {
    color = "bg-purple-500/20 text-purple-400 border-purple-500/30";
    icon = <BrainCircuit className="w-3 h-3 mr-1" />;
    description = "AI inferred from similar historic claims";
  } else {
    color = "bg-orange-500/20 text-orange-400 border-orange-500/30";
    icon = <AlertCircle className="w-3 h-3 mr-1" />;
    description = "Low confidence. TPA verification strongly advised.";
  }

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
        <p className="text-xs text-slate-500 mt-2">Source: {basis}</p>
      </TooltipContent>
    </Tooltip>
  );
}
