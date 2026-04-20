import { redirect } from "next/navigation";
import { Shield, TicketPercent } from "lucide-react";
import { auth } from "@/lib/auth";
import { isProAdmin } from "@/lib/admin";

export default async function AdminLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/login?callbackUrl=/admin/promo");
  }

  if (!isProAdmin(session.user.plan)) {
    redirect("/dashboard");
  }

  return (
    <main className="min-h-screen bg-[hsl(222,47%,4%)] p-4 pt-24 text-slate-200 sm:p-6 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <div className="rounded-3xl border border-sky-500/15 bg-slate-950/60 p-6 shadow-2xl shadow-sky-950/30 backdrop-blur">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="mb-2 inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-sky-300">
                <Shield className="h-3.5 w-3.5" />
                Admin Console
              </p>
              <h1 className="text-3xl font-bold tracking-tight text-white">Redeem Code Control</h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-400">
                Generate promo codes, control expiry and usage limits, and disable leaked codes before they are redeemed again.
              </p>
            </div>
            <div className="inline-flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
              <TicketPercent className="h-5 w-5 text-emerald-400" />
              Access granted via PRO plan
            </div>
          </div>
        </div>
        {children}
      </div>
    </main>
  );
}
