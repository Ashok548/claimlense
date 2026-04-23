"use client";

import Link from "next/link";
import { Coins, Crown } from "lucide-react";
import { useCredits } from "@/hooks/useCredits";

export function CreditsHeaderActions() {
  const { credits, isLoading } = useCredits();

  if (isLoading) return <div className="animate-pulse bg-white/10 h-10 w-32 rounded-xl"></div>;

  const hasCredits = credits !== undefined && credits >= 200;

  return (
    <>
      <div
        className={`flex min-h-9 items-center rounded-xl border px-4 py-2 backdrop-blur-md ${
          hasCredits
            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
            : "bg-red-500/10 border-red-500/20 text-red-400"
        }`}
      >
        <Coins className="w-5 h-5 mr-2" />
        <div className="flex flex-col">
          <span className="text-xs uppercase font-semibold opacity-80 leading-tight">Credits</span>
          <span className="text-sm font-bold leading-tight">{credits ?? 0} Available</span>
        </div>
      </div>

      {!hasCredits ? (
        <Link
          href="/credits"
          className="inline-flex h-9 items-center justify-center rounded-lg bg-amber-500 px-6 text-sm font-medium text-white shadow-lg shadow-amber-500/20 transition-colors hover:bg-amber-400"
        >
          <Crown className="w-5 h-5 mr-2" />
          Add Credits
        </Link>
      ) : null}
    </>
  );
}

export function CreditsAlert() {
  const { credits, isLoading } = useCredits();

  if (isLoading) return null;
  const hasCredits = credits !== undefined && credits >= 200;

  if (hasCredits) return null;

  return (
    <div className="flex gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-amber-200 sm:gap-4 mb-4">
      <Crown className="w-6 h-6 text-amber-500 shrink-0" />
      <div>
        <h4 className="font-bold">Insufficient credits!</h4>
        <p className="text-sm opacity-80 mt-1">
          You need at least 200 credits to perform a new analysis. Top up your wallet to continue checking claims.{" "}
          <Link href="/credits" className="underline underline-offset-2 font-semibold hover:text-amber-100">
            Open Wallet →
          </Link>
        </p>
      </div>
    </div>
  );
}
