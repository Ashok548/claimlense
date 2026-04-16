import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(req: Request) {
  try {
    const { jobId, key, fileType } = await req.json();

    if (!jobId || !key || !fileType) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    // Call FastAPI Parse Endpoint
    const response = await fetch(`${process.env.FASTAPI_INTERNAL_URL}/v1/parse`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
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
