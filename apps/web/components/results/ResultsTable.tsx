"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { Info, Sparkles } from "lucide-react";

interface BillLineItem {
  id: string;
  description: string;
  billed_amount: any;
  payable_amount: any | null;
  status: string;
  category: string | null;
  rule_matched: string | null;
  confidence: any | null;
  rejection_reason: string | null;
  recovery_action: string | null;
  llm_used: boolean | null;
}

interface Props {
  items: BillLineItem[];
}

function getStatusConfig(status: string) {
  switch (status) {
    case "PAYABLE":
      return { label: "PAYABLE", class: "status-payable" };
    case "NOT_PAYABLE":
      return { label: "REJECTED", class: "status-not-payable" };
    case "PARTIALLY_PAYABLE":
      return { label: "PARTIAL", class: "status-partial" };
    case "VERIFY_WITH_TPA":
      return { label: "VERIFY", class: "status-verify" };
    default:
      return { label: status, class: "bg-slate-800 text-slate-300" };
  }
}

function getPayableColor(status: string) {
  if (status === "PAYABLE") return "text-green-400";
  if (status === "NOT_PAYABLE") return "text-red-400";
  return "text-yellow-400";
}

/* ─── Mobile card for a single line item ─────────────────────────── */
function LineItemCard({ item }: { item: BillLineItem }) {
  const statusConfig = getStatusConfig(item.status);
  const billedStr = `₹${Number(item.billed_amount).toLocaleString()}`;
  const payStr =
    item.payable_amount !== null
      ? `₹${Number(item.payable_amount).toLocaleString()}`
      : "TBD";

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-3">
      {/* Row 1: description + status badge */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 flex-wrap">
            <p className="text-sm font-semibold text-white leading-snug">
              {item.description}
            </p>
            {item.llm_used && (
              <Tooltip>
                <TooltipTrigger>
                  <Sparkles className="h-3 w-3 shrink-0 text-purple-400" />
                </TooltipTrigger>
                <TooltipContent className="bg-slate-800 border-white/10">
                  AI evaluated this item as no explicit rule was found.
                </TooltipContent>
              </Tooltip>
            )}
          </div>
          {item.category && (
            <span className="mt-0.5 block text-xs text-slate-500">
              {item.category}
            </span>
          )}
        </div>
        <Badge
          variant="outline"
          className={`${statusConfig.class} shrink-0 border shadow-none font-semibold uppercase text-[10px] tracking-wider`}
        >
          {statusConfig.label}
        </Badge>
      </div>

      {/* Row 2: billed / payable amounts */}
      <div className="grid grid-cols-2 gap-3 rounded-lg border border-white/5 bg-white/[0.03] p-3">
        <div>
          <p className="text-[10px] uppercase tracking-wide text-slate-500 mb-0.5">
            Billed
          </p>
          <p className="text-sm font-semibold text-slate-300">{billedStr}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wide text-slate-500 mb-0.5">
            Payable
          </p>
          <p className={`text-sm font-bold ${getPayableColor(item.status)}`}>
            {payStr}
          </p>
        </div>
      </div>

      {/* Row 3: reason + recovery */}
      {item.rejection_reason ? (
        <div className="space-y-1">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">
            Reason / Rule
          </p>
          <div className="flex items-start gap-2">
            <p className="text-xs text-slate-300 leading-relaxed flex-1">
              {item.rejection_reason}
            </p>
            {item.recovery_action && (
              <Tooltip>
                <TooltipTrigger>
                  <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                </TooltipTrigger>
                <TooltipContent className="bg-slate-800 border-white/10 max-w-sm p-3">
                  <p className="font-semibold text-white mb-1">Recovery Advice:</p>
                  <p className="text-slate-300 text-sm">{item.recovery_action}</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>
      ) : (
        <p className="text-xs text-slate-500 italic">Standard payable item</p>
      )}

      {/* Row 4: confidence */}
      <div className="flex items-center justify-between pt-1 border-t border-white/5">
        <span className="text-[10px] uppercase tracking-wide text-slate-500">
          AI Confidence
        </span>
        <ConfidenceBadge
          confidence={Number(item.confidence) || 0}
          basis={item.rule_matched || "Unknown"}
        />
      </div>
    </div>
  );
}

/* ─── Main component ─────────────────────────────────────────────── */
export function ResultsTable({ items }: Props) {
  return (
    <>
      {/* ── Mobile: card list (hidden on md+) ───────────────────── */}
      <div className="flex flex-col gap-3 md:hidden">
        {items.map((item) => (
          <LineItemCard key={item.id} item={item} />
        ))}
      </div>

      {/* ── Desktop: original table (hidden below md) ─────────── */}
      <div className="hidden md:block overflow-hidden rounded-xl border border-white/10 glass">
        <div className="overflow-x-auto">
          <table className="min-w-[860px] w-full text-sm">
            <thead className="border-b border-white/10 bg-white/5">
              <tr className="text-left">
                <th className="px-4 py-3 text-xs text-slate-300 font-medium">Item Description</th>
                <th className="px-4 py-3 text-xs text-right text-slate-300 font-medium">Billed</th>
                <th className="px-4 py-3 text-xs text-right text-slate-300 font-medium">Payable</th>
                <th className="px-4 py-3 text-xs text-slate-300 font-medium">Status</th>
                <th className="px-4 py-3 text-xs text-slate-300 font-medium">Reason / Rule</th>
                <th className="px-4 py-3 text-xs text-slate-300 font-medium">AI Confidence</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const statusConfig = getStatusConfig(item.status);
                const billedStr = `₹${Number(item.billed_amount).toLocaleString()}`;
                const payStr =
                  item.payable_amount !== null
                    ? `₹${Number(item.payable_amount).toLocaleString()}`
                    : "TBD";

                return (
                  <tr
                    key={item.id}
                    className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="min-w-[240px] max-w-[300px] px-4 py-3 align-top font-medium text-white" title={item.description}>
                      <div className="flex items-center gap-2">
                        <span className="line-clamp-2 break-words">{item.description}</span>
                        {item.llm_used && (
                          <Tooltip>
                            <TooltipTrigger>
                              <Sparkles className="h-3 w-3 shrink-0 text-purple-400" />
                            </TooltipTrigger>
                            <TooltipContent className="bg-slate-800 border-white/10">
                              AI evaluated this item as no explicit rule was found.
                            </TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                      {item.category && (
                        <span className="text-xs text-slate-500 block mt-1">{item.category}</span>
                      )}
                    </td>

                    <td className="px-4 py-3 text-right align-top text-slate-300">{billedStr}</td>

                    <td className={`px-4 py-3 text-right align-top font-medium ${getPayableColor(item.status)}`}>
                      {payStr}
                    </td>

                    <td className="px-4 py-3 align-top">
                      <Badge
                        variant="outline"
                        className={`${statusConfig.class} border shadow-none font-semibold uppercase text-[10px] tracking-wider`}
                      >
                        {statusConfig.label}
                      </Badge>
                    </td>

                    <td className="max-w-[280px] px-4 py-3 align-top">
                      {item.rejection_reason ? (
                        <div className="flex items-start gap-2">
                          <p className="text-sm text-slate-300 line-clamp-2" title={item.rejection_reason}>
                            {item.rejection_reason}
                          </p>
                          {item.recovery_action && (
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                              </TooltipTrigger>
                              <TooltipContent className="bg-slate-800 border-white/10 max-w-sm p-3">
                                <p className="font-semibold text-white mb-1">Recovery Advice:</p>
                                <p className="text-slate-300 text-sm">{item.recovery_action}</p>
                              </TooltipContent>
                            </Tooltip>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-500 text-sm italic">Standard payable item</span>
                      )}
                    </td>

                    <td className="px-4 py-3 align-top">
                      <ConfidenceBadge
                        confidence={Number(item.confidence) || 0}
                        basis={item.rule_matched || "Unknown"}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
