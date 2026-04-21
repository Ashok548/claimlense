import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { auth } from "@/lib/auth";

export async function POST(req: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { jobId, key, fileType } = await req.json();

    if (!jobId || !key || !fileType) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    // Ensure users can only parse their own pending upload jobs.
    const existingJob = await prisma.uploadJob.findUnique({
      where: { id: jobId },
      select: { id: true, userId: true, status: true },
    });

    if (!existingJob || existingJob.userId !== session.user.id) {
      return NextResponse.json({ error: "Upload job not found" }, { status: 404 });
    }

    // Call FastAPI Parse Endpoint
    const internalSecret =
      process.env.FASTAPI_INTERNAL_SECRET ??
      process.env.INTERNAL_API_SECRET ??
      "change-me";

    const response = await fetch(`${process.env.FASTAPI_INTERNAL_URL}/v1/parse`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-internal-api-secret": internalSecret,
      },
      body: JSON.stringify({
        s3_key: key,
        file_type: fileType,
        job_id: jobId
      }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error("FastAPI parse error:", response.status, errorText);
        
        // Update job to FAILED
        await prisma.uploadJob.update({
            where: { id: jobId },
            data: { status: "FAILED" }
        });

        // Parse detail safely if possible
        let detail = `FastAPI returned ${response.status}`;
        try {
          const parsed = JSON.parse(errorText);
          detail = parsed.detail || detail;
        } catch {}

        return NextResponse.json(
            { error: detail },
            { status: response.status }
        );
    }

    const data = await response.json();

    // Update job to PARSED
    await prisma.uploadJob.update({
        where: { id: jobId },
        data: { status: "PARSED" }
    });

    return NextResponse.json(data);
  } catch (error) {
    console.error("Parse proxy failed:", error);
    return NextResponse.json({ error: "Failed to parse claim" }, { status: 500 });
  }
}
