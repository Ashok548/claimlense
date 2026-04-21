"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  FileSearch,
  TrendingDown,
  Zap,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const STATS = [
  { value: "₹18,400", label: "Average claim at risk per bill" },
  { value: "7", label: "Insurers supported" },
  { value: "95%", label: "Accuracy on IRDAI exclusions" },
  { value: "< 30s", label: "Analysis time" },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Select your insurer",
    desc: "Choose from 7 major Indian insurers. We know their specific rules.",
  },
  {
    step: "02",
    title: "Enter policy & bill details",
    desc: "Upload your hospital bill PDF/image, or type items manually.",
  },
  {
    step: "03",
    title: "Get instant analysis",
    desc: "AI + IRDAI rule engine classifies each item with a reason and confidence score.",
  },
  {
    step: "04",
    title: "Take action before discharge",
    desc: "Use our pre-discharge checklist to negotiate with hospital billing and save money.",
  },
];

const EXAMPLE_ITEMS = [
  {
    desc: "Surgeon Fee",
    amount: "₹25,000",
    status: "PAYABLE",
    icon: CheckCircle2,
    color: "text-green-400",
    bg: "bg-green-400/10 border-green-400/20",
  },
  {
    desc: "Surgical Gloves",
    amount: "₹350",
    status: "NOT PAYABLE",
    icon: XCircle,
    color: "text-red-400",
    bg: "bg-red-400/10 border-red-400/20",
  },
  {
    desc: "Laser Machine Usage",
    amount: "₹8,000",
    status: "NOT PAYABLE",
    icon: XCircle,
    color: "text-red-400",
    bg: "bg-red-400/10 border-red-400/20",
  },
  {
    desc: "Room Rent (AC Single)",
    amount: "₹4,500",
    status: "PARTIAL",
    icon: AlertTriangle,
    color: "text-yellow-400",
    bg: "bg-yellow-400/10 border-yellow-400/20",
  },
  {
    desc: "Anaesthesia Charges",
    amount: "₹12,000",
    status: "VERIFY TPA",
    icon: HelpCircle,
    color: "text-purple-400",
    bg: "bg-purple-400/10 border-purple-400/20",
  },
];

export default function LandingPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(false);

  const handleStartAnalysis = async () => {
    setIsChecking(true);
    try {
      const res = await fetch("/api/check-credits");
      if (res.status === 401) {
        router.push("/login?callbackUrl=/analyze");
        return;
      }
      
      if (res.ok) {
        const data = await res.json();
        if (data.credits >= 200) {
          router.push("/analyze");
        } else {
          router.push("/credits");
        }
      } else {
        router.push("/analyze"); // Fallback
      }
    } catch {
      router.push("/analyze"); // Fallback
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <main className="min-h-screen bg-[hsl(222,47%,4%)] overflow-hidden">
      {/* Hero Section */}
      <section className="pt-24 pb-16 px-5 relative">
        {/* Background glow */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Badge className="mb-6 bg-sky-500/10 text-sky-400 border-sky-500/20 text-sm px-4 py-1.5">
              🇮🇳 Built for Indian Health Insurance
            </Badge>

            <h1 className="text-3xl md:text-4xl font-bold text-white leading-tight mb-4">
              Know What Your Insurance{" "}
              <span className="gradient-text">Will Actually Pay</span>
            </h1>

            <p className="text-md text-slate-400 max-w-2xl mx-auto mb-6 leading-relaxed">
              Upload your hospital bill. Our AI + IRDAI rule engine predicts which items
              will be rejected — before you sign the discharge papers. Save ₹5,000–₹50,000.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={handleStartAnalysis}
                disabled={isChecking}
                className="inline-flex items-center justify-center bg-sky-500 hover:bg-sky-400 text-white font-semibold px-5 py-3 text-sm md:text-base rounded-lg shadow-md transition-all hover:shadow-sky-500/30 hover:scale-105"
              >
                {isChecking ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> : <Zap className="w-5 h-5 mr-2" />}
                Analyze My Bill
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="border border-white/10 text-slate-300 hover:bg-white/5 px-5 py-3 text-sm md:text-base rounded-lg"
              >
                <FileSearch className="w-5 h-5 mr-2" />
                See Example Report
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-10 px-5">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass rounded-xl p-5 text-center"
            >
              <div className="text-xl font-bold text-sky-400 mb-1">{stat.value}</div>
              <div className="text-sm text-slate-500">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Example Bill Analysis Preview */}
      <section id="example" className="py-12 px-5 scroll-mt-24">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-xl font-bold text-white mb-2">See It In Action</h2>
            <p className="text-slate-400">
              Real analysis output for a Star Health claim (Appendicitis, Itemized billing)
            </p>
          </div>

          <div className="glass rounded-2xl p-6 space-y-3">
            {/* Summary bar */}
            <div className="flex items-center justify-between py-3 border-b border-white/5 mb-4">
              <div>
                <span className="text-slate-400 text-sm">Total Billed</span>
                <div className="text-white font-bold text-lg">₹49,850</div>
              </div>
              <div>
                <span className="text-slate-400 text-sm">Payable</span>
                <div className="text-green-400 font-bold text-lg">₹41,000</div>
              </div>
              <div>
                <span className="text-slate-400 text-sm">At Risk</span>
                <div className="text-red-400 font-bold text-lg">₹8,850</div>
              </div>
            </div>

            {EXAMPLE_ITEMS.map((item, i) => (
              <motion.div
                key={item.desc}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className={`flex items-center justify-between p-3 rounded-lg border ${item.bg}`}
              >
                <div className="flex items-center gap-3">
                  <item.icon className={`w-4 h-4 ${item.color} flex-shrink-0`} />
                  <span className="text-white text-sm font-medium">{item.desc}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400 text-sm">{item.amount}</span>
                  <span className={`text-xs font-semibold ${item.color}`}>{item.status}</span>
                </div>
              </motion.div>
            ))}

            <div className="pt-3 border-t border-white/5">
              <div className="flex items-start gap-2 text-sm text-yellow-400">
                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>
                  ₹8,850 at risk. Before discharge: Ask billing to bundle gloves into OT charges
                  and request room downgrade.
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-12 px-5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-white mb-3">How It Works</h2>
            <p className="text-slate-400">From hospital bill to actionable advice in under 30 seconds</p>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {HOW_IT_WORKS.map((step, i) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="glass rounded-xl p-5 flex gap-4"
              >
                <div className="text-3xl font-black text-sky-500/20 leading-none">{step.step}</div>
                <div>
                  <h3 className="text-white font-semibold mb-1">{step.title}</h3>
                  <p className="text-slate-400 text-sm">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-5 text-center">
        <div className="max-w-xl mx-auto">
          <TrendingDown className="w-12 h-12 text-sky-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-4">
            Don&apos;t Lose Money on a Preventable Rejection
          </h2>
          <p className="text-slate-400 mb-8">
            Get 200 credits free on sign-up. Each analysis uses 200 credits. Top up anytime for ₹200.
          </p>
          <Button
            size="lg"
            onClick={handleStartAnalysis}
            disabled={isChecking}
            className="bg-sky-500 hover:bg-sky-400 text-white font-semibold px-10 py-6 text-lg rounded-xl shadow-lg shadow-sky-500/25 hover:scale-105 transition-all"
          >
            {isChecking ? "Checking..." : "Start Analysis"}
            {!isChecking && <ArrowRight className="w-5 h-5 ml-2" />}
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-6 px-5 border-t border-white/5 text-center">
        <p className="text-slate-600 text-sm">
          © 2026 ClaimSmart · Not a TPA or insurance intermediary ·
          Analysis based on IRDAI guidelines · Not legal advice
        </p>
      </footer>
    </main>
  );
}
