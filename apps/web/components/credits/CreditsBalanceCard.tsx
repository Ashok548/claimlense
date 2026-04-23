"use client";

import { useCredits } from "@/hooks/useCredits";
import { Coins, CheckCircle2, XCircle } from "lucide-react";

export function CreditsBalanceCard() {
  const { credits, isLoading } = useCredits();

  if (isLoading) {
    return (
      <div className="glass relative flex flex-col justify-between overflow-hidden rounded-xl border border-white/10 p-5 shadow-2xl min-h-[160px] animate-pulse">
        <div className="absolute right-0 top-0 p-6 opacity-10">
          <Coins className="h-24 w-24 text-sky-500" />
        </div>
      </div>
    );
  }

  const hasEnough = credits !== undefined && credits >= 200;

  return (
    <div className="glass relative flex flex-col justify-between overflow-hidden rounded-xl border border-white/10 p-5 shadow-2xl">
      <div className="absolute right-0 top-0 p-6 opacity-10">
        <Coins className="h-24 w-24 text-sky-500" />
      </div>
      
      <div className="relative z-10">
        <h2 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">Current Balance</h2>
        <div className="mb-3 flex items-end gap-2">
          <span className={`text-2xl font-bold tracking-tighter sm:text-3xl ${hasEnough ? "text-white" : "text-amber-400"}`}>
            {credits ?? 0}
          </span>
          <span className="mb-0.5 text-base text-slate-500 sm:text-lg">credits</span>
        </div>
        
        <div className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium sm:text-sm ${
          hasEnough ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
        }`}>
          {hasEnough ? (
            <>
              <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />
              Sufficient for new analysis (200 req)
            </>
          ) : (
            <>
              <XCircle className="mr-1.5 h-3.5 w-3.5" />
              Insufficient. Top up 200 to analyze.
            </>
          )}
        </div>
      </div>
    </div>
  );
}
