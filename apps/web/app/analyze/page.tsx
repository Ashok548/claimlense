"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { InsurerSelector } from "@/components/analyze/InsurerSelector";
import { PlanSelector } from "@/components/analyze/PlanSelector";
import { RiderSelector } from "@/components/analyze/RiderSelector";
import { PolicyForm } from "@/components/analyze/PolicyForm";
import { BillEntryTable } from "@/components/analyze/BillEntryTable";
import { UploadZone } from "@/components/analyze/UploadZone";
import { StayDurationDialog } from "@/components/analyze/StayDurationDialog";
import { PolicyType, HospitalType, BillingMode, BillItemInput, AnalyzeRequest, PlanDetail, InsurerResponse } from "@/types/analyze";
import { Button } from "@/components/ui/button";
import { ChevronRight, ChevronLeft, Send, ShieldCheck, Loader2, BedDouble, Pencil } from "lucide-react";
import { BackButton } from "@/components/navigation/BackButton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const STEPS = ["Insurer", "Plan & Riders", "Policy", "Diagnosis", "Bill Items"];

export default function AnalyzeWizard() {
  const router = useRouter();
  
  // -- Wizard State
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // -- Form Data
  const [insurerId, setInsurerId] = useState("");
  const [insurerCode, setInsurerCode] = useState("");
  const [planCode, setPlanCode] = useState<string | undefined>();
  const [planDetail, setPlanDetail] = useState<PlanDetail | undefined>();
  const [riderCodes, setRiderCodes] = useState<string[]>([]);
  
  const [sumInsured, setSumInsured] = useState(500000);
  const [icuDays, setIcuDays] = useState<number | undefined>();
  const [generalWardDays, setGeneralWardDays] = useState<number | undefined>();
  const [stayDetectedByBill, setStayDetectedByBill] = useState(false);
  const [stayDialogOpen, setStayDialogOpen] = useState(false);
  const [policyType, setPolicyType] = useState<PolicyType>(PolicyType.INDIVIDUAL);
  const [hospitalType, setHospitalType] = useState<HospitalType>(HospitalType.EMPANELLED);
  const [billingMode, setBillingMode] = useState<BillingMode>(BillingMode.ITEMIZED);
  
  const [diagnosis, setDiagnosis] = useState("");
  const [billItems, setBillItems] = useState<BillItemInput[]>([]);

  // -- Navigation
  const nextStep = () => {
    if (step === 0 && !insurerCode) return setError("Please select an insurer");
    if (step === 1 && !planCode) return setError("Please select a plan to continue");
    setError(null);
    setStep(s => Math.min(STEPS.length - 1, s + 1));
  };
  
  const prevStep = () => {
    setError(null);
    setStep(s => Math.max(0, s - 1));
  };

  const handleInsurerSelect = (insurer: InsurerResponse) => {
    setInsurerId(String(insurer.id));
    setInsurerCode(insurer.code);
    setPlanCode(undefined);
    setPlanDetail(undefined);
    setRiderCodes([]);
    setError(null);
  };

  const submitAnalysis = async () => {
    if (billItems.length === 0) return setError("Please add at least one bill item");

    // If no stay duration has been determined, require the user to enter it
    const hasStayInfo = (icuDays ?? 0) > 0 || (generalWardDays ?? 0) > 0;
    if (!hasStayInfo) {
      setStayDialogOpen(true);
      return;
    }
    
    setLoading(true);
    setError(null);

    const payload: AnalyzeRequest = {
      insurer_code: insurerCode,
      plan_code: planCode!,
      rider_codes: riderCodes,
      policy_type: policyType,
      hospital_type: hospitalType,
      billing_mode: billingMode,
      sum_insured: sumInsured,
      icu_days: icuDays,
      general_ward_days: generalWardDays,
      diagnosis: diagnosis || undefined,
      // Omit frontend 'id' before sending
      bill_items: billItems.map(({ description, billed_amount }) => ({
        description,
        billed_amount
      })),
    };

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to analyze claim");
      }

      const data = await res.json();
      router.push(`/results/${data.analysis_id}`);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[hsl(222,47%,4%)] text-white pt-5 pb-12 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto">
        <BackButton />
        {/* Header */}
        <div className="flex items-center gap-2 mb-8">
          <ShieldCheck className="w-8 h-8 text-sky-400" />
          <h1 className="text-3xl font-bold">New Bill Analysis</h1>
        </div>

        {/* Stepper */}
        <div className="flex items-center justify-between mb-8 overflow-x-auto pb-4">
          {STEPS.map((label, idx) => (
            <div key={label} className="flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm transition-colors ${
                step > idx ? "bg-sky-500 text-white" : 
                step === idx ? "bg-sky-500 ring-4 ring-sky-500/20 text-white" : 
                "bg-slate-800 text-slate-500"
              }`}>
                {step > idx ? "✓" : idx + 1}
              </div>
              <span className={`ml-3 mr-6 font-medium whitespace-nowrap ${
                step >= idx ? "text-white" : "text-slate-500"
              }`}>
                {label}
              </span>
              {idx < STEPS.length - 1 && (
                <div className="h-px w-12 bg-white/10 hidden sm:block mr-6" />
              )}
            </div>
          ))}
        </div>

        {/* Error Banner */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg mb-6 flex items-center justify-between">
            {error}
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">×</button>
          </div>
        )}

        {/* Step Content */}
        <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 sm:p-8 mb-8 min-h-[400px]">
          {step === 0 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <h2 className="text-xl font-semibold mb-6">Select Your Health Insurance Provider</h2>
              <InsurerSelector 
                selectedInsurerId={insurerId} 
                onSelect={handleInsurerSelect} 
              />
            </div>
          )}

          {step === 1 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300 space-y-8">
              <div>
                <h2 className="text-xl font-semibold mb-4">Select Policy Plan</h2>
                <PlanSelector 
                  insurerId={insurerId}
                  selectedPlanCode={planCode}
                  onSelect={(code) => {
                    setPlanCode(code);
                    setRiderCodes([]); // reset riders if plan changes
                    setError(null);
                  }}
                  onPlanChange={(plan) => setPlanDetail(plan)}
                />
              </div>

              {planDetail && planDetail.riders && planDetail.riders.length > 0 && (
                <div className="pt-8 border-t border-white/5 animate-in fade-in slide-in-from-bottom-2">
                  <h2 className="text-xl font-semibold mb-2">Select Active Add-on Riders (Optional)</h2>
                  <p className="text-slate-400 mb-6 text-sm">Select any riders configured in your policy to ensure items like consumables or OPD aren't incorrectly rejected.</p>
                  <RiderSelector 
                    riders={planDetail.riders}
                    selectedRiderCodes={riderCodes}
                    onChange={setRiderCodes}
                  />
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <PolicyForm
                sumInsured={sumInsured}
                policyType={policyType}
                hospitalType={hospitalType}
                billingMode={billingMode}
                selectedPlan={planDetail}
                onChange={(updates) => {
                  if (updates.sumInsured !== undefined) setSumInsured(updates.sumInsured);
                  if (updates.policyType !== undefined) setPolicyType(updates.policyType);
                  if (updates.hospitalType !== undefined) setHospitalType(updates.hospitalType);
                  if (updates.billingMode !== undefined) setBillingMode(updates.billingMode);
                }}
              />
            </div>
          )}

          {step === 3 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300 max-w-xl">
              <h2 className="text-xl font-semibold mb-6">Why were you admitted?</h2>
              <div className="space-y-4">
                <Label className="text-slate-300">Diagnosis / Reason for stay (Optional)</Label>
                <Input
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="e.g. Cataract, Appendicitis, Dengue Fever..."
                  className="bg-slate-900 border-white/10 text-white h-12"
                />
                <p className="text-sm text-slate-500">
                  Providing a diagnosis helps our AI find specific rule overrides (like preventing your knee implants from being rejected).
                </p>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <h2 className="text-xl font-semibold mb-2">Enter Hospital Bill Items</h2>
              <p className="text-slate-400 mb-6">Upload a hospital bill to let our AI extract items, or add them manually below.</p>

              {/* Stay duration summary — shown when detected from bill or entered via popup */}
              {((icuDays ?? 0) > 0 || (generalWardDays ?? 0) > 0) && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3 mb-6 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 text-emerald-300">
                    <BedDouble className="w-4 h-4" />
                    <span>
                      {stayDetectedByBill ? "Auto-detected stay:" : "Stay duration:"}
                      {" "}
                      <span className="font-semibold">
                        {[icuDays ? `${icuDays} ICU day${icuDays !== 1 ? "s" : ""}` : null, generalWardDays ? `${generalWardDays} ward day${generalWardDays !== 1 ? "s" : ""}` : null].filter(Boolean).join(" + ")}
                      </span>
                    </span>
                  </div>
                  <button
                    onClick={() => setStayDialogOpen(true)}
                    className="flex items-center gap-1 text-slate-400 hover:text-white text-xs"
                  >
                    <Pencil className="w-3 h-3" />
                    Edit
                  </button>
                </div>
              )}

              {billItems.length === 0 ? (
                <div className="space-y-8">
                  <UploadZone 
                    onItemsParsed={(items) => {
                       const parsed = items.map(it => ({
                          id: crypto.randomUUID(),
                          description: it.description || "",
                          billed_amount: it.billed_amount || 0
                       }));
                       setBillItems(parsed);
                    }}
                    onStayDetected={(icu, ward) => {
                      if ((icu ?? 0) > 0 || (ward ?? 0) > 0) {
                        setIcuDays(icu ?? undefined);
                        setGeneralWardDays(ward ?? undefined);
                        setStayDetectedByBill(true);
                      }
                    }}
                    onError={setError}
                  />
                  
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-white/10" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-[hsl(222,47%,4%)] px-2 text-slate-500">Or enter manually</span>
                    </div>
                  </div>

                  <BillEntryTable items={billItems} onChange={setBillItems} />
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="bg-sky-500/10 border border-sky-500/20 text-sky-400 p-4 rounded-xl flex items-center justify-between text-sm">
                    Review and edit the extracted items below before continuing.
                    <Button variant="outline" size="sm" onClick={() => setBillItems([])} className="border-sky-500/30 text-slate-200">
                      Clear &amp; Upload New
                    </Button>
                  </div>
                  <BillEntryTable items={billItems} onChange={setBillItems} />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="flex justify-between border-t border-white/5 pt-6">
          <Button
            variant="ghost"
            onClick={prevStep}
            disabled={step === 0 || loading}
            className="text-slate-400 hover:text-white"
          >
            <ChevronLeft className="w-5 h-5 mr-1" />
            Back
          </Button>

          {step < STEPS.length - 1 ? (
            <Button
              onClick={nextStep}
              className="bg-sky-500 hover:bg-sky-400 text-white px-8"
            >
              Continue
              <ChevronRight className="w-5 h-5 ml-1" />
            </Button>
          ) : (
            <Button
              onClick={submitAnalysis}
              disabled={loading || billItems.length === 0}
              className="bg-green-500 hover:bg-green-400 text-white px-8 shadow-lg shadow-green-500/20"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
              ) : (
                <Send className="w-5 h-5 mr-2" />
              )}
              {loading ? "Analyzing rules..." : "Analyze Bill NOW"}
            </Button>
          )}
        </div>
      </div>

      {/* Mandatory stay-duration popup — shown when the system cannot detect days from bill */}
      <StayDurationDialog
        open={stayDialogOpen}
        onConfirm={({ icuDays: icu, generalWardDays: ward }) => {
          setIcuDays(icu);
          setGeneralWardDays(ward);
          setStayDetectedByBill(false);
          setStayDialogOpen(false);
          // Re-trigger submit with the now-populated stay info
          const hasStay = (icu ?? 0) > 0 || (ward ?? 0) > 0;
          if (hasStay) submitAnalysis();
        }}
      />
    </div>
  );
}
