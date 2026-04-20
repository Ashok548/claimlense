import { NextResponse } from "next/server";
import crypto from "crypto";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(req: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { razorpayOrderId, razorpayPaymentId, razorpaySignature } = await req.json();

    const body = razorpayOrderId + "|" + razorpayPaymentId;
    const expectedSignature = crypto
      .createHmac("sha256", process.env.RAZORPAY_KEY_SECRET!)
      .update(body.toString())
      .digest("hex");

    const isAuthentic = expectedSignature === razorpaySignature;

    if (!isAuthentic) {
      return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
    }

    // Wrap the payment update and credit increment in a single transaction
    await prisma.$transaction(async (tx) => {
      // Find the pending payment — MUST belong to THIS user to prevent cross-user fraud
      const payment = await tx.payment.findFirst({
        where: {
          razorpayOrderId,
          userId: session.user!.id,  // ownership check
          status: "PENDING",
        },
      });

      if (!payment) {
        throw new Error("Payment record not found or already verified");
      }

      // Update payment record to SUCCESS
      await tx.payment.update({
        where: { id: payment.id },
        data: {
          status: "SUCCESS",
          razorpayPaymentId,
        },
      });

      // Increment user credits by 200
      await tx.user.update({
        where: { id: session.user?.id },
        data: {
          credits: { increment: 200 },
        },
      });
    });

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error("Razorpay verification failed:", error);
    return NextResponse.json(
      { error: "Verification failed" },
      { status: 500 }
    );
  }
}
