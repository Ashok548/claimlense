import { NextResponse } from "next/server";
import Razorpay from "razorpay";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

const razorpay = new Razorpay({
  key_id: process.env.RAZORPAY_KEY_ID!,
  key_secret: process.env.RAZORPAY_KEY_SECRET!,
});

export async function POST(req: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userId = session.user.id;
    // Analysis costs 200 credits = ₹200. Convert to paise (amount * 100)
    const amount = 200 * 100;

    // Razorpay receipt field max length is 40 chars. Use last 8 chars of userId.
    const receipt = `rcpt_${userId.slice(-8)}_${Date.now()}`.slice(0, 40);

    const order = await razorpay.orders.create({ amount, currency: "INR", receipt });

    await prisma.payment.create({
      data: {
        userId,
        razorpayOrderId: order.id,
        amountPaise: amount,
        status: "PENDING",
      },
    });

    return NextResponse.json({
      orderId: order.id,
      amount: order.amount,
      currency: order.currency,
      keyId: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
    });
  } catch (error) {
    console.error("Error creating Razorpay order:", error);
    return NextResponse.json(
      { error: "Failed to create order" },
      { status: 500 }
    );
  }
}
