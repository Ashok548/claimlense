import { NextResponse } from "next/server";

export async function GET() {
  try {
    const res = await fetch(`${process.env.FASTAPI_INTERNAL_URL}/v1/insurers`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      next: { revalidate: 600 }, // Cache for 10 minutes
    });

    if (!res.ok) {
      throw new Error(`FastAPI responded with status: ${res.status}`);
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch insurers:", error);
    return NextResponse.json({ error: "Failed to load insurers" }, { status: 500 });
  }
}
