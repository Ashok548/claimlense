"use client";

import { format } from "date-fns";
import { CopyX, ExternalLink } from "lucide-react";
import Link from "next/link";
import { DownloadReportButton } from "@/components/results/DownloadReportButton";
import { formatCurrency } from "@/lib/utils";

type ReportHistoryItem = {
  id: string;
  analysisId: string;
  insurerName: string;
  diagnosis: string | null;
  totalBilled: number;
  totalAtRisk: number;
  createdAt: string;
};

interface Props {
  reports: ReportHistoryItem[];
}

export function ReportHistoryTable({ reports }: Props) {
  if (reports.length === 0) {
    return (
      <div className="bg-slate-900/30 border border-white/10 rounded-xl py-10 px-4 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-white/5 flex items-center justify-center mb-3">
          <CopyX className="w-5 h-5 text-slate-400" />
        </div>
        <h3 className="text-base font-semibold text-white mb-1">No reports yet</h3>
        <p className="text-sm text-slate-400 mb-5">
          Start your first claim analysis
        </p>
        <Link 
          href="/analyze" 
          className="inline-flex h-9 items-center justify-center rounded-lg bg-sky-500 px-5 text-sm font-medium text-white shadow-sm shadow-sky-500/20 transition-all hover:bg-sky-400 hover:shadow-sky-500/30 active:scale-[0.98]"
        >
          Analyze Your First Claim
        </Link>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/10 glass">
      <div className="space-y-3 p-3 md:hidden">
        {reports.map((r) => (
          <div key={r.id} className="rounded-xl border border-white/5 bg-slate-900/50 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white">{r.insurerName}</p>
                <p className="mt-1 text-xs text-slate-400">{format(new Date(r.createdAt), "dd MMM yyyy")}</p>
              </div>
              <Link
                href={`/results/${r.analysisId}`}
                className="inline-flex shrink-0 items-center text-sm text-sky-400 hover:text-sky-300"
              >
                View <ExternalLink className="ml-1 h-4 w-4" />
              </Link>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Diagnosis</p>
                <p className="mt-1 break-words text-slate-300">{r.diagnosis || "N/A"}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Billed</p>
                <p className="mt-1 text-slate-300">₹{formatCurrency(r.totalBilled)}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">At Risk</p>
                <p className="mt-1 font-medium text-red-400">₹{formatCurrency(r.totalAtRisk)}</p>
              </div>
              <div className="flex items-end justify-end">
                <DownloadReportButton analysisId={r.analysisId} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="hidden overflow-x-auto md:block">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-white/5 text-slate-300 border-b border-white/10 uppercase text-xs tracking-wider">
          <tr>
            <th className="px-6 py-4">Date</th>
            <th className="px-6 py-4">Insurer</th>
            <th className="px-6 py-4">Diagnosis</th>
            <th className="px-6 py-4 text-right">Billed</th>
            <th className="px-6 py-4 text-right">At Risk</th>
            <th className="px-6 py-4 text-center">Export</th>
            <th className="px-6 py-4 text-center">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {reports.map((r) => (
            <tr key={r.id} className="hover:bg-white/5 transition-colors">
              <td className="px-6 py-4 text-slate-300">
                {format(new Date(r.createdAt), "dd MMM yyyy")}
              </td>
              <td className="px-6 py-4 font-medium text-white">
                {r.insurerName}
              </td>
              <td className="px-6 py-4 text-slate-400 truncate max-w-[200px]" title={r.diagnosis || "N/A"}>
                {r.diagnosis || "N/A"}
              </td>
              <td className="px-6 py-4 text-right text-slate-300">
                ₹{formatCurrency(r.totalBilled)}
              </td>
              <td className="px-6 py-4 text-right text-red-400 font-medium">
                ₹{formatCurrency(r.totalAtRisk)}
              </td>
              <td className="px-6 py-4">
                <div className="flex justify-center">
                   {/* Reusing existing PDF button */}
                   <DownloadReportButton analysisId={r.analysisId} />
                </div>
              </td>
              <td className="px-6 py-4 text-center">
                <Link
                  href={`/results/${r.analysisId}`}
                  className="text-sky-400 hover:text-sky-300 inline-flex items-center text-sm"
                >
                  View <ExternalLink className="w-4 h-4 ml-1" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
