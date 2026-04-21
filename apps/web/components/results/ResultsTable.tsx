"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { Info, Sparkles } from "lucide-react";
import { PayabilityStatus } from "@/types/analyze";

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

export function ResultsTable({ items }: Props) {
  const getStatusConfig = (status: string) => {
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
  };

  return (
    <div className="overflow-hidden rounded-xl border border-white/10 glass">
      <div className="overflow-x-auto">
      <Table className="min-w-[860px] text-sm">
        <TableHeader className="border-b border-white/10 bg-white/5">
          <TableRow className="hover:bg-transparent">
            <TableHead className="text-xs text-slate-300">Item Description</TableHead>
            <TableHead className="text-xs text-right text-slate-300">Billed</TableHead>
            <TableHead className="text-xs text-right text-slate-300">Payable</TableHead>
            <TableHead className="text-xs text-slate-300">Status</TableHead>
            <TableHead className="text-xs text-slate-300">Reason / Rule</TableHead>
            <TableHead className="text-xs text-slate-300">AI Confidence</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => {
            const statusConfig = getStatusConfig(item.status);
            const billedStr = `₹${Number(item.billed_amount).toLocaleString()}`;
            const payStr = item.payable_amount !== null 
              ? `₹${Number(item.payable_amount).toLocaleString()}` 
              : "TBD";
            
            return (
              <TableRow key={item.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                <TableCell className="min-w-[240px] max-w-[300px] py-3 align-top font-medium text-white" title={item.description}>
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
                </TableCell>
                
                <TableCell className="py-3 text-right align-top text-slate-300">{billedStr}</TableCell>
                
                <TableCell className={`py-3 text-right align-top font-medium ${item.status === 'PAYABLE' ? 'text-green-400' : item.status === 'NOT_PAYABLE' ? 'text-red-400' : 'text-yellow-400'}`}>
                  {payStr}
                </TableCell>
                
                <TableCell className="py-3 align-top">
                  <Badge variant="outline" className={`${statusConfig.class} border shadow-none font-semibold uppercase text-[10px] tracking-wider`}>
                    {statusConfig.label}
                  </Badge>
                </TableCell>
                
                <TableCell className="max-w-[280px] py-3 align-top">
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
                </TableCell>
                
                <TableCell className="py-3 align-top">
                  <ConfidenceBadge 
                    confidence={Number(item.confidence) || 0} 
                    basis={item.rule_matched || "Unknown"} 
                  />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      </div>
    </div>
  );
}
