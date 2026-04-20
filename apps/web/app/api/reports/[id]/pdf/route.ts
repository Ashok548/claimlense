import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await auth();
    const firebaseAuthorization = req.headers.get("authorization");

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (!firebaseAuthorization?.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Missing Firebase token" }, { status: 401 });
    }

    const resolvedParams = await params;
    const analysisId = resolvedParams.id;
    if (!analysisId) {
      return NextResponse.json({ error: "Missing analysis ID" }, { status: 400 });
    }

    // Proxy to FastAPI
    const response = await fetch(`${process.env.FASTAPI_INTERNAL_URL}/v1/report/${analysisId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: firebaseAuthorization,
      },
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error("FastAPI report error:", response.status, errorText);
        return NextResponse.json(
            { error: "Report generation failed on intelligence engine" },
            { status: response.status }
        );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Report proxy failed:", error);
    return NextResponse.json({ error: "Failed to generate report" }, { status: 500 });
  }
}
