"use client";

import { PolicyType, HospitalType, BillingMode, PlanDetail } from "@/types/analyze";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  sumInsured: number;
  policyType: PolicyType;
  hospitalType: HospitalType;
  billingMode: BillingMode;
  selectedPlan?: PlanDetail;
  onChange: (updates: Partial<Props>) => void;
}

export function PolicyForm({ sumInsured, policyType, hospitalType, billingMode, selectedPlan, onChange }: Props) {
  const getRoomRentText = () => {
    if (!selectedPlan) return "Unknown";
    if (selectedPlan.room_rent_limit_abs) return `₹${selectedPlan.room_rent_limit_abs}/day`;
    if (selectedPlan.room_rent_limit_pct) return `${selectedPlan.room_rent_limit_pct}% of Sum Insured (₹${(selectedPlan.room_rent_limit_pct / 100 * sumInsured).toLocaleString()}/day)`;
    return "No Limit";
  };
  return (
    <Card className="glass border-white/10">
      <CardHeader>
        <CardTitle className="text-white text-lg">Policy Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        
        <div className="grid grid-cols-1 gap-6">
          <div className="space-y-2">
            <Label className="text-white">Sum Insured (₹) *</Label>
            <Input 
              type="number" 
              className="bg-slate-900 border-white/10 text-white"
              value={sumInsured || ""}
              onChange={(e) => onChange({ sumInsured: parseInt(e.target.value) || 0 })}
              placeholder="e.g. 500000"
            />
          </div>
        </div>

        <div className="space-y-3 bg-slate-800/50 p-4 rounded-xl border border-white/5">
            <Label className="text-white">Active Plan Limits</Label>
            {selectedPlan ? (
               <div className="text-sm text-slate-300 space-y-1">
                 <div className="flex justify-between">
                    <span>Room Rent:</span>
                    <span className="text-white">{getRoomRentText()}</span>
                 </div>
                 <div className="flex justify-between">
                    <span>Co-Pay:</span>
                    <span className="text-white">{selectedPlan.co_pay_pct ? `${selectedPlan.co_pay_pct}%` : "None"}</span>
                 </div>
               </div>
            ) : (
               <div className="text-sm text-slate-500">No plan selected.</div>
            )}
          </div>
       

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t border-white/5">
          <div className="space-y-2">
            <Label className="text-white">Policy Type</Label>
            <Select 
              value={policyType} 
              onValueChange={(val) => onChange({ policyType: val as PolicyType })}
            >
              <SelectTrigger className="bg-slate-900 border-white/10 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-white/10 text-white">
                <SelectItem value={PolicyType.INDIVIDUAL}>Individual</SelectItem>
                <SelectItem value={PolicyType.FLOATER}>Family Floater</SelectItem>
                <SelectItem value={PolicyType.GROUP}>Group / Corporate</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Hospital Network</Label>
            <Select 
              value={hospitalType} 
              onValueChange={(val) => onChange({ hospitalType: val as HospitalType })}
            >
              <SelectTrigger className="bg-slate-900 border-white/10 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-white/10 text-white">
                <SelectItem value={HospitalType.EMPANELLED}>Empanelled (Network)</SelectItem>
                <SelectItem value={HospitalType.NON_EMPANELLED}>Non-Empanelled (Reimbursement)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Hospital Billing Mode</Label>
            <Select 
              value={billingMode} 
              onValueChange={(val) => onChange({ billingMode: val as BillingMode })}
            >
              <SelectTrigger className="bg-slate-900 border-white/10 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-white/10 text-white">
                <SelectItem value={BillingMode.ITEMIZED}>Itemized (Detailed)</SelectItem>
                <SelectItem value={BillingMode.PACKAGE}>Package (e.g. Cataract Package)</SelectItem>
                <SelectItem value={BillingMode.MIXED}>Mixed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

      </CardContent>
    </Card>
  );
}
