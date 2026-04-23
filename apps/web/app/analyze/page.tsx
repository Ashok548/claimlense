"use client";

import { useState, useEffect } from "react";
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
import { ChevronRight, ChevronLeft, Send, ShieldCheck, Loader2, BedDouble, Pencil, Coins } from "lucide-react";
import { BackButton } from "@/components/navigation/BackButton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getFirebaseIdToken } from "@/lib/firebase";
import Link from "next/link";
import { useCredits } from "@/hooks/useCredits";

const STEPS = ["Insurer", "Plan & Riders", "Policy", "Diagnosis", "Bill Items"];

export default function AnalyzeWizard() {
  const router = useRouter();
  const { credits, isLoading } = useCredits();
  
  // -- Credit Gate: derive from context
  const creditsChecked = !isLoading;
  const insufficientCredits = credits !== undefined && credits < 200;

  useEffect(() => {
     if (!isLoading && credits === undefined) {
         router.replace("/login?callbackUrl=/analyze");
     }
  }, [isLoading, credits, router]);

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
      const firebaseToken = await getFirebaseIdToken();
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${firebaseToken}`,
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to analyze claim");
      }

      const data = await res.json();
      router.push(`/results/${data.analysis_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to analyze claim");
      setLoading(false);
    }
  };

  return (
    <div className="app-shell text-white">
      <div className="mx-auto max-w-5xl">
        <BackButton />
        {/* Header */}
        <div className="mb-6 flex items-center gap-2 sm:mb-8">
          <ShieldCheck className="h-6 w-6 text-sky-400 sm:h-7 sm:w-7" />
          <h1 className="text-2xl font-bold sm:text-3xl">New Bill Analysis</h1>
        </div>

        {/* Credit gate: loading spinner while we verify credits */}
        {!creditsChecked && (
          <div className="flex items-center justify-center py-12 gap-3 text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>Verifying account...</span>
          </div>
        )}

        {/* Blocked state: not enough credits */}
        {creditsChecked && insufficientCredits && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-5 text-center sm:p-6">
            <Coins className="w-10 h-10 text-amber-400 mx-auto mb-3" />
            <h2 className="text-xl font-bold text-white mb-2">Insufficient Credits</h2>
            <p className="text-slate-400 mb-6">
              You need at least <strong className="text-white">200 credits</strong> to run an analysis. Top up your wallet to continue.
            </p>
            <Link
              href="/credits"
              className="inline-flex items-center justify-center rounded-lg bg-sky-500 hover:bg-sky-400 text-white font-medium px-6 h-9 transition-colors"
            >
              Open Credits Wallet →
            </Link>
          </div>
        )}

        {/* Main wizard — only shown when credits are OK */}
        {creditsChecked && !insufficientCredits && (
          <>
        {/* Stepper — mobile: compact progress bar; sm+: full labelled row */}

        {/* Mobile stepper (< sm) */}
        <div className="mb-6 sm:hidden">
          <div className="mb-2 flex items-center gap-1">
            {STEPS.map((_, idx) => (
              <div
                key={idx}
                className={`h-1 flex-1 rounded-full transition-colors ${
                  step > idx ? "bg-sky-500" : step === idx ? "bg-sky-400" : "bg-slate-700"
                }`}
              />
            ))}
          </div>
          <p className="text-xs text-slate-400">
            Step <span className="font-semibold text-white">{step + 1}</span> of {STEPS.length}
            <span className="ml-1.5 font-medium text-sky-400">— {STEPS[step]}</span>
          </p>
        </div>

        {/* Desktop stepper (≥ sm) */}
        <div className="mb-8 hidden items-center justify-between pb-4 sm:flex">
          {STEPS.map((label, idx) => (
            <div key={label} className="flex items-center">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-colors ${
                step > idx ? "bg-sky-500 text-white" :
                step === idx ? "bg-sky-500 ring-4 ring-sky-500/20 text-white" :
                "bg-slate-800 text-slate-500"
              }`}>
                {step > idx ? "✓" : idx + 1}
              </div>
              <span className={`ml-3 mr-6 text-sm font-medium ${
                step >= idx ? "text-white" : "text-slate-500"
              }`}>
                {label}
              </span>
              {idx < STEPS.length - 1 && (
                <div className="mr-6 h-px w-12 bg-white/10" />
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
        <div className="mb-8 min-h-[360px] rounded-2xl border border-white/5 bg-slate-900/40 p-4 sm:min-h-[400px] sm:p-6 lg:p-8">
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
                  <p className="text-slate-400 mb-6 text-sm">Select any riders configured in your policy to ensure items like consumables or OPD aren&apos;t incorrectly rejected.</p>
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

              {/* Stay duration summary */}
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
              className="bg-sky-500 hover:bg-sky-400 text-white px-6"
            >
              Continue
              <ChevronRight className="w-5 h-5 ml-1" />
            </Button>
          ) : (
            <Button
              onClick={submitAnalysis}
              disabled={loading || billItems.length === 0}
              className="bg-green-500 hover:bg-green-400 text-white px-6 shadow-lg shadow-green-500/20"
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

        {/* Mandatory stay-duration popup */}
        <StayDurationDialog
          open={stayDialogOpen}
          onConfirm={({ icuDays: icu, generalWardDays: ward }) => {
            setIcuDays(icu);
            setGeneralWardDays(ward);
            setStayDetectedByBill(false);
            setStayDialogOpen(false);
            const hasStay = (icu ?? 0) > 0 || (ward ?? 0) > 0;
            if (hasStay) submitAnalysis();
          }}
        />
          </>
        )}
      </div>
    </div>
  );
}
