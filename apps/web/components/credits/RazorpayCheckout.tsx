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
    <div className="flex flex-col gap-3 h-full">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" />
      
      <Button 
        onClick={startCheckout} 
        disabled={loading}
        className="w-full bg-sky-500 hover:bg-sky-400 text-white font-bold py-6 text-lg shadow-lg shadow-sky-500/20"
      >
        {loading ? (
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
        ) : (
          <Coins className="w-6 h-6 mr-2" />
        )}
        Add 200 Credits (₹200)
      </Button>

      {error && (
        <p className="text-sm text-red-400 font-medium text-center bg-red-500/10 p-2 rounded border border-red-500/20">
          {error}
        </p>
      )}
    </div>
  );
}
