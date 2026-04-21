import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { redirect } from "next/navigation";
import Link from "next/link";
import { ShieldCheck, Coins, Crown } from "lucide-react";
import { BackButton } from "@/components/navigation/BackButton";
import { ReportHistoryTable } from "@/components/dashboard/ReportHistoryTable";
import { isProAdmin } from "@/lib/admin";

export default async function ReportsPage() {
	const session = await auth();
	if (!session?.user) {
		redirect("/login");
	}

	const userId = session.user.id;

	// Fetch db user to get latest credits accurately
	const dbUser = await prisma.user.findUnique({
		where: { id: userId },
		include: { reports: { orderBy: { createdAt: "desc" } } },
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
	const canAccessAdmin = isProAdmin(dbUser.plan);

	return (
		<main className="app-shell text-slate-200">
			<div className="app-container space-y-6 sm:space-y-8">
				<BackButton />

				{/* Header & Quick Stats */}
				<div className="flex flex-col items-start justify-between gap-5 lg:flex-row lg:items-center">
					<div className="flex items-center gap-3 sm:gap-4">
						<div className="flex h-12 w-12 items-center justify-center rounded-full border border-sky-500/20 bg-sky-500/10 sm:h-14 sm:w-14">
							<span className="text-xl font-bold text-sky-400 sm:text-2xl">
								{(session.user.name || "U")[0].toUpperCase()}
							</span>
						</div>
						<div className="min-w-0">
							<h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">My Reports</h1>
							<p className="text-sm text-slate-400 sm:text-base">Welcome back, {session.user.name || session.user.email}</p>
						</div>
					</div>

					<div className="flex w-full flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center lg:w-auto lg:justify-end">
						{canAccessAdmin ? (
							<Link
								href="/admin/promo"
								className="inline-flex h-9 items-center justify-center rounded-lg border border-sky-500/20 bg-sky-500/10 px-4 text-sm font-medium text-sky-300 transition-colors hover:bg-sky-500/20"
							>
								<ShieldCheck className="w-4 h-4 mr-2" />
								Admin Console
							</Link>
						) : null}

						{/* Credit Badge */}
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
								<span className="text-sm font-bold leading-tight">{credits} Available</span>
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
					</div>
				</div>

				{/* Not enough Credits Alert */}
				{!hasCredits && (
					<div className="flex gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-amber-200 sm:gap-4">
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
					<div className="mb-4 flex items-center justify-between">
						<h2 className="flex items-center text-lg font-bold text-white sm:text-xl">
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