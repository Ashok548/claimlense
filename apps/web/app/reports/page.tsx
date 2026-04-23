import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { redirect } from "next/navigation";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { BackButton } from "@/components/navigation/BackButton";
import { ReportHistoryTable } from "@/components/dashboard/ReportHistoryTable";
import { CreditsHeaderActions, CreditsAlert } from "@/components/dashboard/CreditsStatusBadge";
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
	const canAccessAdmin = isProAdmin(dbUser.plan);

	return (
		<main className="app-shell text-slate-200">
			<div className="app-container space-y-4 sm:space-y-6">
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
							<h1 className="text-xl font-bold tracking-tight text-white sm:text-2xl">My Reports</h1>
							<p className="text-xs text-slate-400 sm:text-sm">Welcome back, {session.user.name || session.user.email}</p>
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

						<CreditsHeaderActions />
					</div>
				</div>

				{/* Not enough Credits Alert */}
				<CreditsAlert />

				{/* Reports Section */}
				<div>
					<div className="mb-4 flex items-center justify-between">
						<h2 className="flex items-center text-base font-semibold text-white sm:text-lg">
							<ShieldCheck className="w-4 h-4 mr-2 text-sky-400" />
							Recent Claims
						</h2>
					</div>

					<ReportHistoryTable reports={reports} />
				</div>
			</div>
		</main>
	);
}