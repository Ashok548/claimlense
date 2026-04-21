import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";
import { SummaryCards } from "@/components/results/SummaryCards";
import { ResultsTable } from "@/components/results/ResultsTable";
import { ActionChecklist } from "@/components/results/ActionChecklist";
import { DownloadReportButton } from "@/components/results/DownloadReportButton";
import { ShareButton } from "@/components/results/ShareButton";
import { ShieldCheck } from "lucide-react";
import { BackButton } from "@/components/navigation/BackButton";

type ActionItem = {
  type: string;
  item_name?: string;
  instruction: string;
};

type RawActionObject = {
  type?: string;
  title?: string;
  item_name?: string;
  instruction?: string;
  text?: string;
  action?: string;
  message?: string;
};

function normalizeActionItems(actionItems: unknown): ActionItem[] {
  if (!Array.isArray(actionItems)) {
    return [];
  }

  return actionItems
    .map((item): ActionItem | null => {
      if (typeof item === "string") {
        const text = item.trim();
        if (!text) {
          return null;
        }
        return {
          type: "Action Item",
          instruction: text,
        };
      }

      if (item && typeof item === "object") {
        const raw = item as RawActionObject;
        const instruction =
          raw.instruction?.trim() ||
          raw.text?.trim() ||
          raw.action?.trim() ||
          raw.message?.trim() ||
          "";

        if (!instruction) {
          return null;
        }

        return {
          type: raw.type?.trim() || raw.title?.trim() || "Action Item",
          item_name: raw.item_name,
          instruction,
        };
      }

      return null;
    })
    .filter((item): item is ActionItem => item !== null);
}

export default async function ResultsPage({ params }: { params: Promise<{ id: string }> }) {
  // Validate UUID or whatever ID structure we have
  const resolvedParams = await params;
  const analysisId = resolvedParams.id;

  const analysis = await prisma.claim_analyses.findUnique({
    where: { id: analysisId },

    include: {
      bill_line_items: true,
      insurers: true,
    },
  });

  if (!analysis) {
    notFound();
  }

  const actionItems = normalizeActionItems(analysis.action_items);
  const createdAtLabel = analysis.created_at
    ? new Date(analysis.created_at).toLocaleDateString()
    : "Date unavailable";
  
  // Safe cast since we know they are Decimal
  const totalBilled = Number(analysis.total_billed) || 0;
  const totalPayable = Number(analysis.total_payable) || 0;
  const totalPendingVerification = Number(analysis.total_pending_verification) || 0;
  const totalAtRisk = Number(analysis.total_at_risk) || 0;
  const rejectionPct = Number(analysis.rejection_rate_pct) || 0;

  return (
    <main className="app-shell">
      <div className="app-container space-y-5 sm:space-y-6">
        <BackButton fallbackHref="/reports" />
        {/* Header Options */}
        <div className="flex flex-col items-start justify-between gap-4 border-b border-white/5 pb-4 sm:flex-row sm:items-center sm:pb-5">
          <div className="min-w-0">
             <h1 className="flex items-center gap-3 text-xl font-bold text-white sm:text-2xl">
               <ShieldCheck className="h-6 w-6 text-sky-400 sm:h-7 sm:w-7" />
               Analysis Results
             </h1>
             <p className="mt-2 text-xs text-slate-400 sm:text-sm">
               {analysis.insurers.name} • {analysis.diagnosis || "General Admission"} • {createdAtLabel}
             </p>
          </div>
          
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:items-start">
            {/* Phase 3 hook */}
            <DownloadReportButton analysisId={analysisId} />
            <ShareButton analysisId={analysisId} insurerName={analysis.insurers.name} />
          </div>
        </div>

        {/* Action Items (Priority) */}
        <ActionChecklist actionItems={actionItems} />

        {/* Summary Metrics */}
        <SummaryCards 
          totalBilled={totalBilled} 
          totalPayable={totalPayable}
          totalPendingVerification={totalPendingVerification}
          totalAtRisk={totalAtRisk} 
          rejectionPct={rejectionPct} 
        />

        {/* Line Items Breakdown */}
        <div>
          <h2 className="mb-3 text-base font-bold text-white sm:text-lg">Detailed Breakdown</h2>
          <ResultsTable items={analysis.bill_line_items.map(item => ({
            ...item,
            billed_amount: Number(item.billed_amount),
            payable_amount: item.payable_amount !== null ? Number(item.payable_amount) : null,
            confidence: item.confidence !== null ? Number(item.confidence) : null,
          }))} />
        </div>

        {/* Info Banner */}
        <div className="rounded-xl border border-sky-500/10 bg-sky-500/5 p-3 text-center text-sm text-slate-400 sm:p-4">
          This analysis is based on IRDAI guidelines and known insurer behaviors. It is not a guarantee of claim settlement. 
          Final decisions rest with the TPA and Insurer.
        </div>

      </div>
    </main>
  );
}
