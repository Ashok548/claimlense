import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { Coins, History, FileText, CheckCircle2, Clock, XCircle } from "lucide-react";
import { BackButton } from "@/components/navigation/BackButton";
import { RazorpayCheckout } from "@/components/credits/RazorpayCheckout";
import { PromoCodeRedeemer } from "@/components/credits/PromoCodeRedeemer";

export const metadata = {
  title: "Credits | ClaimSmart",
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
      select: { credits: true },
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

  const credits = dbUser.credits;
  const hasEnough = credits >= 200;

  return (
    <main className="min-h-screen bg-[hsl(222,47%,4%)] p-4 sm:p-6 lg:p-8 pt-24 text-slate-200">
      <div className="max-w-4xl mx-auto space-y-8">
        <BackButton />
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
              <Coins className="w-8 h-8 text-sky-400" />
              Credits Wallet
            </h1>
            <p className="text-slate-400 mt-1">Manage your balance and top up for more claim analyses.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Balance Card */}
          <div className="glass rounded-2xl p-6 border border-white/10 shadow-2xl relative overflow-hidden flex flex-col justify-between">
            <div className="absolute top-0 right-0 p-8 opacity-10">
              <Coins className="w-32 h-32 text-sky-500" />
            </div>
            
            <div className="relative z-10">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-2">Current Balance</h2>
              <div className="flex items-end gap-3 mb-4">
                <span className={`text-6xl font-bold tracking-tighter ${hasEnough ? "text-white" : "text-amber-400"}`}>
                  {credits}
                </span>
                <span className="text-xl text-slate-500 mb-2">credits</span>
              </div>
              
              <div className={`text-sm font-medium px-3 py-1.5 rounded-full inline-flex items-center ${
                hasEnough ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              }`}>
                {hasEnough ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Sufficient for new analysis (200 req)
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 mr-2" />
                    Insufficient. Top up 200 to analyze.
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Action Cards */}
          <div className="space-y-6 flex flex-col">
            
            <div className="glass rounded-2xl p-6 border border-white/10 shadow-lg flex-1">
              <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
                Add Credits
              </h3>
              <RazorpayCheckout userName={userName} userEmail={userEmail} />
              <p className="text-xs text-slate-500 mt-4 text-center">
                Secure payment powered by Razorpay. 
              </p>
            </div>

            <div className="glass rounded-2xl p-6 border border-white/10 shadow-lg">
              <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
                Redeem Promo
              </h3>
              <PromoCodeRedeemer />
            </div>

          </div>
        </div>

        {/* Transaction History */}
        <div className="glass rounded-2xl border border-white/10 shadow-xl overflow-hidden mt-12">
          <div className="p-6 border-b border-white/10 flex items-center gap-3 bg-white/5">
            <History className="w-5 h-5 text-slate-400" />
            <h3 className="font-semibold text-white">Payment History</h3>
          </div>
          
          <div className="p-0">
            {payments.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <FileText className="w-8 h-8 opacity-20 mx-auto mb-3" />
                No transactions found.
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {payments.map((payment) => (
                  <div key={payment.id} className="p-4 sm:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:bg-white/5 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-xl border ${
                        payment.status === "SUCCESS" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                        payment.status === "PENDING" ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                        "bg-red-500/10 border-red-500/20 text-red-400"
                      }`}>
                        {payment.status === "SUCCESS" ? <CheckCircle2 className="w-5 h-5" /> :
                         payment.status === "PENDING" ? <Clock className="w-5 h-5" /> :
                         <XCircle className="w-5 h-5" />}
                      </div>
                      <div>
                        <p className="font-semibold text-white">
                          +200 credits &mdash; ₹{(payment.amountPaise / 100).toFixed(2)} Top-up
                        </p>
                        <p className="text-sm text-slate-400 mt-1">
                          {payment.createdAt.toLocaleDateString("en-IN", { 
                            day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" 
                          })}
                        </p>
                      </div>
                    </div>
                    <span className={`text-sm font-medium ${
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
          <div className="glass rounded-2xl border border-white/10 shadow-xl overflow-hidden mt-6">
            <div className="p-6 border-b border-white/10 flex items-center gap-3 bg-white/5">
              <XCircle className="w-5 h-5 text-slate-400" />
              <h3 className="font-semibold text-white">Credit Usage (Analyses)</h3>
            </div>
            <div className="divide-y divide-white/5">
              {reports.map((report) => (
                <div key={report.id} className="p-4 sm:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-xl border bg-red-500/10 border-red-400/20 text-red-400">
                      <XCircle className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="font-semibold text-white">
                        &minus;200 credits &mdash; {report.insurerName} analysis
                      </p>
                      {report.diagnosis && (
                        <p className="text-xs text-slate-500 mt-0.5">{report.diagnosis}</p>
                      )}
                      <p className="text-sm text-slate-400 mt-1">
                        {report.createdAt.toLocaleDateString("en-IN", { 
                          day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
                        })}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm font-medium text-red-400">DEDUCTED</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </main>
  );
}
