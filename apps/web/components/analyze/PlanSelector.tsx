"use client";

import { useEffect, useState } from "react";
import { PlanDetail } from "@/types/analyze";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, ShieldAlert, CheckCircle2 } from "lucide-react";

interface Props {
  insurerId: string;
  selectedPlanCode: string | undefined;
  onSelect: (planCode: string) => void;
  onPlanChange?: (plan: PlanDetail) => void;
}

export function PlanSelector({ insurerId, selectedPlanCode, onSelect, onPlanChange }: Props) {
  const [plans, setPlans] = useState<PlanDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!insurerId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/insurers/${insurerId}/plans`)
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data?.error || "Failed to load plans");
        if (!Array.isArray(data)) throw new Error("Unexpected response format");
        setPlans(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("PlanSelector error:", err);
        setError("Could not load plans for this insurer.");
        setLoading(false);
      });
  }, [insurerId]);
  
  useEffect(() => {
     if (selectedPlanCode && plans.length > 0) {
        const found = plans.find(p => p.code === selectedPlanCode);
        if (found && onPlanChange) onPlanChange(found);
     }
  }, [selectedPlanCode, plans, onPlanChange]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-sky-500" />
      </div>
    );
  }

  if (error) {
    return <div className="text-red-400 p-4 bg-red-500/10 rounded-lg">{error}</div>;
  }

  if (plans.length === 0) {
    return <div className="text-slate-400 p-4">No plans found. Please select a different insurer.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {plans.map((plan) => (
          <Card
            key={plan.code}
            className={`cursor-pointer transition-all ${
              selectedPlanCode === plan.code
                ? "border-sky-500 bg-sky-500/10 ring-1 ring-sky-500"
                : "border-white/10 hover:border-white/30 glass"
            }`}
            onClick={() => onSelect(plan.code)}
          >
            <CardContent className="p-5 flex flex-col h-full">
              <h3 className="text-base font-medium text-white mb-3 sm:text-lg">{plan.name}</h3>
              
              <div className="space-y-2 text-sm text-slate-300 flex-grow">
                <div className="flex justify-between border-b border-white/5 pb-1">
                  <span className="text-slate-400">Room Rent Limit:</span>
                  <span className="font-medium text-white">
                    {plan.room_rent_limit_abs ? `₹${plan.room_rent_limit_abs}/day` : plan.room_rent_limit_pct ? `${plan.room_rent_limit_pct}% of Sum Insured` : "No Limit"}
                  </span>
                </div>
                <div className="flex justify-between border-b border-white/5 pb-1">
                  <span className="text-slate-400">Co-pay:</span>
                  <span className="font-medium text-white">
                    {plan.co_pay_pct ? `${plan.co_pay_pct}%` : "0%"}
                  </span>
                </div>
                <div className="flex justify-between pt-1">
                  <span className="text-slate-400">Consumables:</span>
                  {plan.consumables_covered ? (
                    <span className="flex items-center text-green-400 font-medium">
                      <CheckCircle2 className="w-4 h-4 mr-1"/> Covered
                    </span>
                  ) : (
                    <span className="flex items-center text-red-400 font-medium">
                      <ShieldAlert className="w-4 h-4 mr-1"/> Excluded
                    </span>
                  )}
                </div>
              </div>
              
              <div className="mt-4 pt-3 border-t border-white/10 flex flex-wrap gap-2">
                {plan.riders && plan.riders.length > 0 && (
                  <Badge variant="secondary" className="bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                    +{plan.riders.length} Add-on Riders Available
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
