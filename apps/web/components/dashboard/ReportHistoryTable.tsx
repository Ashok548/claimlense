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
      <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6 text-center flex flex-col items-center sm:p-10sm:p-10">
        <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
          <CopyX className="w-8 h-8 text-slate-500" />
        </div>
        <h3 className="text-xl font-bold text-white mb-2">No Reports Yet</h3>
        <p className="text-slate-400 mb-6 text-sm">
          You haven&apos;t generated any claim analysis reports yet.
        </p>
        <Link 
          href="/analyze" 
          className="bg-sky-500 hover:bg-sky-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
        >
          Start New Analysis
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
