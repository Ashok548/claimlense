import { NextResponse } from "next/server";
import { AnalyzeRequest } from "@/types/analyze";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(req: Request) {
  try {
    const session = await auth();
    let userId: string | null = null;

    if (session?.user) {
      userId = session.user.id as string;
      const dbUser = await prisma.user.findUnique({ where: { id: userId } });
      if (!dbUser || dbUser.credits < 1) {
        return NextResponse.json({ error: "Insufficient credits. Please upgrade." }, { status: 402 });
      }
    }

    const body = await req.json() as AnalyzeRequest & { user_ref?: string };
    
    // Remove user_ref before sending to Python. 
    // Prisma uses CUIDs which crash Python's strict UUID parser.
    // We already map userId to analysisId locally in the Report table anyway.
    delete body.user_ref;

    const response = await fetch(`${process.env.FASTAPI_INTERNAL_URL}/v1/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("FastAPI analyze error:", response.status, errorText);

      let detail = `FastAPI responded with status: ${response.status}`;
      try { detail = JSON.parse(errorText).detail || detail; } catch {}

      return NextResponse.json(
        { error: detail },
        { status: response.status }
      );
    }

    const data = await response.json();

    if (userId) {
      // Decrement credits & save report map
      await prisma.$transaction([
        prisma.user.update({
          where: { id: userId },
          data: { credits: { decrement: 1 } }
        }),
        prisma.report.create({
          data: {
            userId: userId,
            analysisId: data.analysis_id, // Important string representation
            insurerName: data.insurer_name,
            insurerCode: data.insurer_code,
            diagnosis: data.diagnosis,
            totalBilled: data.summary.total_billed,
            totalPayable: data.summary.total_payable,
            totalAtRisk: data.summary.total_at_risk,
            rejectionPct: data.summary.rejection_rate_pct,
            status: "COMPLETE",
          }
        })
      ]);
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Analyze proxy failed:", error);
    return NextResponse.json({ error: "Failed to analyze claim" }, { status: 500 });
  }
}
