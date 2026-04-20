import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { redirect } from "next/navigation";
import Link from "next/link";
import { ShieldCheck, Coins, Crown } from "lucide-react";
import { BackButton } from "@/components/navigation/BackButton";
import { ReportHistoryTable } from "@/components/dashboard/ReportHistoryTable";
import { isProAdmin } from "@/lib/admin";

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.user) {
    redirect("/login");
  }

  const userId = session.user.id;

  // Fetch db user to get latest credits accurately
  const dbUser = await prisma.user.findUnique({
    where: { id: userId },
    include: { reports: { orderBy: { createdAt: 'desc' } } }
  });

  if (!dbUser) redirect("/login");

  const reports = dbUser.reports.map((report) => ({
    id: report.id,
    analysisId: report.analysisId,
    insurerName: report.insurerName,
    diagnosis: report.diagnosis,
    totalBilled: Number(report.totalBilled),
    totalAtRisk: Number(report.totalAtRisk),
    createdAt: report.createdAt.toISOString(),
  }));
  const credits = dbUser.credits;
  const hasCredits = credits >= 200;
  const canAccessAdmin = isProAdmin(session.user.plan);

  return (
    <main className="min-h-screen bg-[hsl(222,47%,4%)] p-4 sm:p-6 lg:p-8 pt-24 text-slate-200">
      <div className="max-w-7xl mx-auto space-y-8">
        <BackButton />
        
        {/* Header & Quick Stats */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-sky-500/10 flex items-center justify-center border border-sky-500/20">
              <span className="text-2xl font-bold text-sky-400">
                {(session.user.name || "U")[0].toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">My Reports</h1>
              <p className="text-slate-400">Welcome back, {session.user.name || session.user.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {canAccessAdmin ? (
              <Link
                href="/admin/promo"
                className="inline-flex items-center justify-center rounded-lg border border-sky-500/20 bg-sky-500/10 px-4 h-8 font-medium text-sky-300 transition-colors hover:bg-sky-500/20"
              >
                <ShieldCheck className="w-4 h-4 mr-2" />
                Admin Console
              </Link>
            ) : null}

            {/* Credit Badge */}
            <div className={`flex items-center px-4 py-2 rounded-xl border backdrop-blur-md ${
                hasCredits 
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" 
                : "bg-red-500/10 border-red-500/20 text-red-400"
              }`}
            >
              <Coins className="w-5 h-5 mr-2" />
              <div className="flex flex-col">
                <span className="text-xs uppercase font-semibold opacity-80 leading-tight">Credits</span>
                <span className="text-sm font-bold leading-tight">{credits} Available</span>
              </div>
            </div>

            {!hasCredits ? (
              <Link
                href="/credits"
                className="inline-flex items-center justify-center rounded-lg bg-amber-500 hover:bg-amber-400 text-white font-medium shadow-lg shadow-amber-500/20 px-6 h-8 transition-colors"
              >
                <Crown className="w-5 h-5 mr-2" />
                Add Credits
              </Link>
            ) : null}
          </div>
        </div>

        {/* Not enough Credits Alert */}
        {!hasCredits && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex gap-4 text-amber-200">
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
        )}

        {/* Reports Section */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-white flex items-center">
              <ShieldCheck className="w-5 h-5 mr-2 text-sky-400" />
              Recent Claims
            </h2>
          </div>
          
          <ReportHistoryTable reports={reports} />
        </div>
      </div>
    </main>
  );
}
