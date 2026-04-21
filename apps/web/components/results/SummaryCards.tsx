"use client";

import { Card, CardContent } from "@/components/ui/card";
import { ReceiptCent, ShieldAlert, BadgeCheck, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { formatCurrency } from "@/lib/utils";

interface Props {
  totalBilled: number;
  totalPayable: number;
  totalPendingVerification: number;
  totalAtRisk: number;
  rejectionPct: number;
}

export function SummaryCards({ totalBilled, totalPayable, totalPendingVerification, totalAtRisk, rejectionPct }: Props) {
  const cards = [
    {
      title: "Total Billed",
      value: `₹${formatCurrency(totalBilled)}`,
      icon: ReceiptCent,
      color: "text-slate-400",
      bg: "bg-slate-800/50",
    },
    {
      title: "Confirmed Payable",
      value: `₹${formatCurrency(totalPayable)}`,
      icon: BadgeCheck,
      color: "text-green-400",
      bg: "bg-green-500/10 border-green-500/20",
    },
    {
      title: "Pending Verification",
      value: `₹${formatCurrency(totalPendingVerification)}`,
      icon: Activity,
      color: "text-yellow-400",
      bg: "bg-yellow-500/10 border-yellow-500/20",
    },
    {
      title: "At Risk Amount",
      value: `₹${formatCurrency(totalAtRisk)}`,
      icon: ShieldAlert,
      color: "text-red-400",
      bg: "bg-red-500/10 border-red-500/20",
    },
    {
      title: "Rejection Risk",
      value: `${rejectionPct}%`,
      icon: Activity,
      color: "text-orange-400",
      bg: "bg-orange-500/10 border-orange-500/20",
    },
  ];

  return (
    <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-5">
      {cards.map((card, i) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
        >
          <Card className={`glass border-white/10 ${card.bg}`}>
            <CardContent className="p-4 sm:p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-300 sm:text-sm sm:normal-case sm:tracking-normal">{card.title}</p>
                <card.icon className={`h-4 w-4 shrink-0 sm:h-5 sm:w-5 ${card.color}`} />
              </div>
              <h2 className="text-lg font-bold leading-tight text-white tracking-tight sm:text-xl lg:text-2xl">
                {card.value}
              </h2>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
