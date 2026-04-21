"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Ticket } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function PromoCodeRedeemer() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "error" | "success"; text: string } | null>(null);

  const handleRedeem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch("/api/promo/redeem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: code.trim() }),
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || "Failed to redeem code.");
      }
      
      setMessage({ type: "success", text: `Success! ${data.creditsAdded} credits added.` });
      setCode("");
      router.refresh();
      
    } catch (err: any) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleRedeem} className="flex h-full flex-col gap-2">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Ticket className="h-4 w-4 text-slate-500" />
          </div>
          <Input 
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="Enter promo code"
            className="bg-slate-900/50 pl-9 text-sm text-white placeholder:text-slate-600 focus-visible:ring-emerald-500"
            disabled={loading}
          />
        </div>
        <Button 
          type="submit" 
          disabled={loading || !code.trim()}
          className="h-9 bg-emerald-500 px-3 text-sm text-white shadow-lg shadow-emerald-500/20 hover:bg-emerald-400"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Apply"}
        </Button>
      </div>

      {message && (
        <p className={`rounded border p-1.5 text-xs font-medium sm:text-sm ${
          message.type === "success" 
            ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" 
            : "text-red-400 bg-red-500/10 border-red-500/20"
        }`}>
          {message.text}
        </p>
      )}
    </form>
  );
}
