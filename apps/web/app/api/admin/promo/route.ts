import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { generatePromoCode, normalizePromoCode } from "@/lib/promo";
import { requireProApiUser } from "@/lib/admin";

const createPromoSchema = z.object({
  code: z.string().trim().min(1).optional(),
  creditsValue: z.coerce.number().int().positive(),
  maxUses: z.coerce.number().int().positive().default(1),
  expiresAt: z.union([z.string().datetime(), z.literal(""), z.null()]).optional(),
});

export async function GET(req: Request) {
  const authResult = await requireProApiUser();
  if ("error" in authResult) {
    return NextResponse.json({ error: authResult.error }, { status: authResult.status });
  }

  const url = new URL(req.url);
  const activeOnly = url.searchParams.get("active") === "true";

  const promoCodes = await prisma.promoCode.findMany({
    where: activeOnly ? { isActive: true } : undefined,
    orderBy: { createdAt: "desc" },
    include: {
      _count: {
        select: { redemptions: true },
      },
    },
  });

  return NextResponse.json({ promoCodes });
}

export async function POST(req: Request) {
  const authResult = await requireProApiUser();
  if ("error" in authResult) {
    return NextResponse.json({ error: authResult.error }, { status: authResult.status });
  }

  try {
    const body = createPromoSchema.parse(await req.json());
    const code = body.code ? normalizePromoCode(body.code) : generatePromoCode();

    const promoCode = await prisma.promoCode.create({
      data: {
        code,
        creditsValue: body.creditsValue,
        maxUses: body.maxUses,
        expiresAt: body.expiresAt ? new Date(body.expiresAt) : null,
      },
      include: {
        _count: {
          select: { redemptions: true },
        },
      },
    });

    return NextResponse.json({ promoCode }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.issues[0]?.message ?? "Invalid input." }, { status: 400 });
    }

    if (
      typeof error === "object" &&
      error !== null &&
      "code" in error &&
      error.code === "P2002"
    ) {
      return NextResponse.json({ error: "Promo code already exists." }, { status: 409 });
    }

    console.error("Promo creation failed:", error);
    return NextResponse.json({ error: "Failed to create promo code." }, { status: 500 });
  }
}
