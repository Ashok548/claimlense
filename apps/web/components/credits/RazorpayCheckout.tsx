"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Coins } from "lucide-react";
import { Button } from "@/components/ui/button";
import Script from "next/script";

// Extend the window object for Razorpay
declare global {
  interface Window {
    Razorpay: any;
  }
}

export function RazorpayCheckout({ userName, userEmail }: { userName?: string; userEmail?: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCheckout = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Check if user is authenticated/has enough credits to prevent double buy? 
      // Not strictly necessary since they can buy as many as they want
      
      // 2. Create Razorpay order on our backend
      const orderRes = await fetch("/api/razorpay/create-order", {
        method: "POST",
      });
      
      const orderData = await orderRes.json();
      
      if (!orderRes.ok || orderData.error) {
        throw new Error(orderData.error || "Failed to create order");
      }

      // 3. Open Razorpay Checkout
      // Guard: Script may not be loaded yet if clicked very quickly
      if (typeof window === "undefined" || !window.Razorpay) {
        setError("Payment system is still loading. Please wait a moment and try again.");
        setLoading(false);
        return;
      }

      const options = {
        key: orderData.keyId,
        amount: orderData.amount,
        currency: orderData.currency,
        name: "ClaimSmart",
        description: "200 Analysis Credits",
        order_id: orderData.orderId,
        handler: async function (response: any) {
          try {
            // 4. Verify payment on our backend
            const verifyRes = await fetch("/api/razorpay/verify", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                razorpayOrderId: response.razorpay_order_id,
                razorpayPaymentId: response.razorpay_payment_id,
                razorpaySignature: response.razorpay_signature,
              }),
            });

            const verifyData = await verifyRes.json();

            if (!verifyRes.ok || verifyData.error) {
              setError("Payment verification failed. Please contact support if money was deducted.");
              return;
            }

            // Success! Refresh the page to show updated balance.
            router.refresh();
          } catch (err) {
            setError("Error processing your payment verification.");
          }
        },
        prefill: {
          name: userName || "",
          email: userEmail || "",
          contact: "",
        },
        theme: {
          color: "#0ea5e9" // sky-500
        }
      };

      const paymentObject = new window.Razorpay(options);
      paymentObject.open();

      paymentObject.on('payment.failed', function (response: any) {
         setError(`Payment failed. Reason: ${response.error.description || "Unknown"}`);
      });
      
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-2">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" />
      
      <Button 
        onClick={startCheckout} 
        disabled={loading}
        className="w-full bg-sky-500 py-5 text-base font-semibold text-white shadow-lg shadow-sky-500/20 hover:bg-sky-400"
      >
        {loading ? (
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        ) : (
          <Coins className="mr-2 h-5 w-5" />
        )}
        Add 200 Credits (₹200)
      </Button>

      {error && (
        <p className="rounded border border-red-500/20 bg-red-500/10 p-1.5 text-center text-xs font-medium text-red-400 sm:text-sm">
          {error}
        </p>
      )}
    </div>
  );
}
