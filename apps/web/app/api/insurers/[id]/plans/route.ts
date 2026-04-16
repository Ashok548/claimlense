import { NextResponse } from "next/server";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    if (!id) {
      return NextResponse.json({ error: "Missing insurer ID" }, { status: 400 });
    }

    const backendUrl = process.env.FASTAPI_INTERNAL_URL || "http://localhost:8000";
    const res = await fetch(`${backendUrl}/v1/insurers/${id}/plans`);

    const text = await res.text();

    if (!res.ok) {
      console.error(`FastAPI plans error ${res.status}:`, text.slice(0, 500));
      return NextResponse.json(
        { error: res.status === 404 ? "Insurer not found" : "Failed to load plans" },
        { status: res.status }
      );
    }

    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      console.error("FastAPI plans returned non-JSON:", text.slice(0, 500));
      return NextResponse.json({ error: "Invalid response from backend" }, { status: 502 });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching plans:", error);
    return NextResponse.json({ error: "Failed to fetch plans" }, { status: 500 });
  }
}
