import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  const report = await prisma.report.findFirst({
    where: {
      id,
      userId: session.user.id as string,
    },
    select: {
      id: true,
      analysisId: true,
      insurerName: true,
      insurerCode: true,
      diagnosis: true,
      totalBilled: true,
      totalPayable: true,
      totalAtRisk: true,
      rejectionPct: true,
      status: true,
      createdAt: true,
    },
  });

  if (!report) {
    return NextResponse.json({ error: "Report not found" }, { status: 404 });
  }

  return NextResponse.json({
    ...report,
    totalBilled: Number(report.totalBilled),
    totalPayable: Number(report.totalPayable),
    totalAtRisk: Number(report.totalAtRisk),
    rejectionPct: Number(report.rejectionPct),
    createdAt: report.createdAt.toISOString(),
  });
}
