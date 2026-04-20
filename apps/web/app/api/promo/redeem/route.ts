import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(req: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { code } = await req.json();
    
    if (!code || typeof code !== "string") {
      return NextResponse.json({ error: "Promo code is required." }, { status: 400 });
    }

    const userId = session.user.id;
    const cleanCode = code.trim().toUpperCase();

    // Wrapping in a transaction to prevent race conditions during redemption
    const result = await prisma.$transaction(async (tx) => {
      // 1. Find the promo code
      const promoCode = await tx.promoCode.findUnique({
        where: { code: cleanCode },
      });

      if (!promoCode) {
        throw new Error("Invalid promo code.");
      }

      if (!promoCode.isActive) {
        throw new Error("This promo code is no longer active.");
      }

      if (promoCode.expiresAt && new Date() > promoCode.expiresAt) {
        throw new Error("This promo code has expired.");
      }

      if (promoCode.usedCount >= promoCode.maxUses) {
        throw new Error("This promo code has reached its usage limit.");
      }

      // 2. Check if this user has already redeemed this exact code
      const existingRedemption = await tx.promoRedemption.findUnique({
        where: {
          userId_promoCodeId: {
            userId,
            promoCodeId: promoCode.id,
          },
        },
      });

      if (existingRedemption) {
        throw new Error("You have already redeemed this promo code.");
      }

      // 3. Create redemption record
      await tx.promoRedemption.create({
        data: {
          userId,
          promoCodeId: promoCode.id,
        },
      });

      // 4. Update the usage count
      await tx.promoCode.update({
        where: { id: promoCode.id },
        data: { usedCount: { increment: 1 } },
      });

      // 5. Increment user credits
      const updatedUser = await tx.user.update({
        where: { id: userId },
        data: { credits: { increment: promoCode.creditsValue } },
      });

      return {
        creditsAdded: promoCode.creditsValue,
        newBalance: updatedUser.credits,
      };
    });

    return NextResponse.json(result, { status: 200 });
    
  } catch (error: any) {
    console.error("Promo redemption failed:", error);
    
    // Known user-facing validation errors are thrown as plain Error messages
    const knownUserErrors = [
      "Invalid promo code.",
      "This promo code is no longer active.",
      "This promo code has expired.",
      "This promo code has reached its usage limit.",
      "You have already redeemed this promo code.",
    ];
    
    const isUserError = knownUserErrors.includes(error.message);
    
    return NextResponse.json(
      { error: isUserError ? error.message : "An error occurred. Please try again." },
      { status: isUserError ? 400 : 500 }
    );
  }
}
