import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { requireProApiUser } from "@/lib/admin";

const updatePromoSchema = z.object({
  isActive: z.boolean(),
});

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function PATCH(req: Request, context: RouteContext) {
  const authResult = await requireProApiUser();
  if ("error" in authResult) {
    return NextResponse.json({ error: authResult.error }, { status: authResult.status });
  }

  try {
    const { id } = await context.params;
    const body = updatePromoSchema.parse(await req.json());

    const promoCode = await prisma.promoCode.update({
      where: { id },
      data: { isActive: body.isActive },
      include: {
        _count: {
          select: { redemptions: true },
        },
      },
    });

    return NextResponse.json({ promoCode });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.issues[0]?.message ?? "Invalid input." }, { status: 400 });
    }

    if (
      typeof error === "object" &&
      error !== null &&
      "code" in error &&
      error.code === "P2025"
    ) {
      return NextResponse.json({ error: "Promo code not found." }, { status: 404 });
    }

    console.error("Promo update failed:", error);
    return NextResponse.json({ error: "Failed to update promo code." }, { status: 500 });
  }
}
