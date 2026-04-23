import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { Coins, History, FileText, CheckCircle2, Clock, XCircle } from "lucide-react";
import { BackButton } from "@/components/navigation/BackButton";
import { RazorpayCheckout } from "@/components/credits/RazorpayCheckout";
import { PromoCodeRedeemer } from "@/components/credits/PromoCodeRedeemer";
import { CreditsBalanceCard } from "@/components/credits/CreditsBalanceCard";

export const metadata = {
  title: "Credits | ClaimLense",
};

export default async function CreditsPage() {
  const session = await auth();
  if (!session?.user?.id) {
    redirect("/login?callbackUrl=/credits");
  }

  // session is guaranteed non-null after the redirect guard above
  const userId = session!.user!.id;
  const userName = session!.user!.name ?? undefined;
  const userEmail = session!.user!.email ?? undefined;

  const [dbUser, payments, reports] = await Promise.all([
    prisma.user.findUnique({
      where: { id: userId },
      select: { id: true },
    }),
    prisma.payment.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" },
      take: 50,
    }),
    // Fetch completed reports to show credit deduction history
    prisma.report.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" },
      take: 50,
      select: { id: true, insurerName: true, diagnosis: true, createdAt: true },
    }),
  ]);

  if (!dbUser) {
    redirect("/login");
  }

  return (
    <main className="app-shell text-slate-200">
      <div className="app-container space-y-5 sm:space-y-6">
        <BackButton />
        
        <div className="flex flex-col items-start justify-between gap-5 md:flex-row md:items-center">
          <div>
            <h1 className="flex items-center gap-2.5 text-xl font-bold tracking-tight text-white sm:text-2xl">
              <Coins className="h-5 w-5 text-sky-400 sm:h-6 sm:w-6" />
              Credits Wallet
            </h1>
            <p className="mt-1 text-sm text-slate-400">Manage your balance and top up for more claim analyses.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          
          {/* Balance Card */}
          <CreditsBalanceCard />

          {/* Action Cards */}
          <div className="flex flex-col space-y-5">
            
            <div className="glass flex-1 rounded-xl border border-white/10 p-5 shadow-lg">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white sm:text-base">
                Add Credits
              </h3>
              <RazorpayCheckout userName={userName} userEmail={userEmail} />
              <p className="mt-3 text-center text-xs text-slate-500">
                Secure payment powered by Razorpay. 
              </p>
            </div>

            <div className="glass rounded-xl border border-white/10 p-5 shadow-lg">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white sm:text-base">
                Redeem Promo
              </h3>
              <PromoCodeRedeemer />
            </div>

          </div>
        </div>

        {/* Transaction History */}
        <div className="glass mt-8 overflow-hidden rounded-xl border border-white/10 shadow-xl">
          <div className="flex items-center gap-2 border-b border-white/10 bg-white/5 p-5">
            <History className="h-4 w-4 text-slate-400 sm:h-5 sm:w-5" />
            <h3 className="text-sm font-semibold text-white sm:text-base">Payment History</h3>
          </div>
          
          <div className="p-0">
            {payments.length === 0 ? (
              <div className="p-6 text-center text-slate-500">
                <FileText className="mx-auto mb-2 h-7 w-7 opacity-20" />
                No transactions found.
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {payments.map((payment) => (
                  <div key={payment.id} className="flex flex-col items-start justify-between gap-3 p-3 transition-colors hover:bg-white/5 sm:flex-row sm:items-center sm:p-4">
                    <div className="flex items-center gap-3">
                      <div className={`rounded-lg border p-2.5 ${
                        payment.status === "SUCCESS" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                        payment.status === "PENDING" ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                        "bg-red-500/10 border-red-500/20 text-red-400"
                      }`}>
                        {payment.status === "SUCCESS" ? <CheckCircle2 className="h-4 w-4" /> :
                         payment.status === "PENDING" ? <Clock className="h-4 w-4" /> :
                         <XCircle className="h-4 w-4" />}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-white sm:text-base">
                          +200 credits &mdash; ₹{(payment.amountPaise / 100).toFixed(2)} Top-up
                        </p>
                        <p className="mt-1 text-xs text-slate-400 sm:text-sm">
                          {payment.createdAt.toLocaleDateString("en-IN", { 
                            day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" 
                          })}
                        </p>
                      </div>
                    </div>
                    <span className={`text-xs font-medium sm:text-sm ${
                      payment.status === "SUCCESS" ? "text-emerald-400" :
                      payment.status === "PENDING" ? "text-amber-400" :
                      "text-red-400"
                    }`}>
                      {payment.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Credit Deductions — analysis history */}
        {reports.length > 0 && (
          <div className="glass mt-5 overflow-hidden rounded-xl border border-white/10 shadow-xl">
            <div className="flex items-center gap-2 border-b border-white/10 bg-white/5 p-5">
              <XCircle className="h-4 w-4 text-slate-400 sm:h-5 sm:w-5" />
              <h3 className="text-sm font-semibold text-white sm:text-base">Credit Usage (Analyses)</h3>
            </div>
            <div className="divide-y divide-white/5">
              {reports.map((report) => (
                <div key={report.id} className="flex flex-col items-start justify-between gap-3 p-3 transition-colors hover:bg-white/5 sm:flex-row sm:items-center sm:p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg border border-red-400/20 bg-red-500/10 p-2.5 text-red-400">
                      <XCircle className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white sm:text-base">
                        &minus;200 credits &mdash; {report.insurerName} analysis
                      </p>
                      {report.diagnosis && (
                        <p className="mt-0.5 text-[11px] text-slate-500 sm:text-xs">{report.diagnosis}</p>
                      )}
                      <p className="mt-1 text-xs text-slate-400 sm:text-sm">
                        {report.createdAt.toLocaleDateString("en-IN", { 
                          day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
                        })}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-medium text-red-400 sm:text-sm">DEDUCTED</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </main>
  );
}
