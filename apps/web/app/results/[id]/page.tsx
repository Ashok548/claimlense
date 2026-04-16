import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";
import { SummaryCards } from "@/components/results/SummaryCards";
import { ResultsTable } from "@/components/results/ResultsTable";
import { ActionChecklist } from "@/components/results/ActionChecklist";
import { DownloadReportButton } from "@/components/results/DownloadReportButton";
import { ShieldCheck, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BackButton } from "@/components/navigation/BackButton";

type ActionItem = {
  type: string;
  item_name?: string;
  instruction: string;
};

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

  const actionItems = Array.isArray(analysis.action_items)
    ? (analysis.action_items as ActionItem[])
    : [];
  const createdAtLabel = analysis.created_at
    ? new Date(analysis.created_at).toLocaleDateString()
    : "Date unavailable";
  
  // Safe cast since we know they are Decimal
  const totalBilled = Number(analysis.total_billed) || 0;
  const totalPayable = Number(analysis.total_payable) || 0;
  const totalAtRisk = Number(analysis.total_at_risk) || 0;
  const rejectionPct = Number(analysis.rejection_rate_pct) || 0;

  return (
    <main className="min-h-screen bg-[hsl(222,47%,4%)] p-4 sm:p-6 lg:p-8 pt-24">
      <div className="max-w-7xl mx-auto space-y-8">
        <BackButton fallbackHref="/reports" />
        {/* Header Options */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-white/5 pb-6">
          <div>
             <h1 className="text-3xl font-bold text-white flex items-center gap-3">
               <ShieldCheck className="w-8 h-8 text-sky-400" />
               Analysis Results
             </h1>
             <p className="text-slate-400 mt-2">
               {analysis.insurers.name} • {analysis.diagnosis || "General Admission"} • {createdAtLabel}
             </p>
          </div>
          
          <div className="flex gap-3 w-full sm:w-auto items-start">
            {/* Phase 3 hook */}
            <DownloadReportButton analysisId={analysisId} />
            <Button className="flex-1 sm:flex-none bg-sky-500 hover:bg-sky-400 text-white">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
          </div>
        </div>

        {/* Action Items (Priority) */}
        <ActionChecklist actionItems={actionItems} />

        {/* Summary Metrics */}
        <SummaryCards 
          totalBilled={totalBilled} 
          totalPayable={totalPayable} 
          totalAtRisk={totalAtRisk} 
          rejectionPct={rejectionPct} 
        />

        {/* Line Items Breakdown */}
        <div>
          <h2 className="text-xl font-bold text-white mb-4">Detailed Breakdown</h2>
          <ResultsTable items={analysis.bill_line_items.map(item => ({
            ...item,
            billed_amount: Number(item.billed_amount),
            payable_amount: item.payable_amount !== null ? Number(item.payable_amount) : null,
            confidence: item.confidence !== null ? Number(item.confidence) : null,
          }))} />
        </div>

        {/* Info Banner */}
        <div className="bg-sky-500/5 border border-sky-500/10 rounded-xl p-4 text-sm text-slate-400 text-center">
          This analysis is based on IRDAI guidelines and known insurer behaviors. It is not a guarantee of claim settlement. 
          Final decisions rest with the TPA and Insurer.
        </div>

      </div>
    </main>
  );
}
