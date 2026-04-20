import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userId = session.user.id;
    const dbUser = await prisma.user.findUnique({
      where: { id: userId },
      select: { credits: true },
    });

    if (!dbUser) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    return NextResponse.json({ credits: dbUser.credits });
  } catch (error) {
    console.error("Check credits failed:", error);
    return NextResponse.json({ error: "Failed to check credits" }, { status: 500 });
  }
}
