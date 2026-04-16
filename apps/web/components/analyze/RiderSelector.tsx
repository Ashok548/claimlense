"use client";

import { RiderDetail } from "@/types/analyze";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { CheckCircle2, FlaskConical, Stethoscope, Baby } from "lucide-react";

interface Props {
  riders: RiderDetail[];
  selectedRiderCodes: string[];
  onChange: (codes: string[]) => void;
}

export function RiderSelector({ riders, selectedRiderCodes, onChange }: Props) {
  if (!riders || riders.length === 0) {
    return (
      <div className="bg-slate-800/50 p-6 rounded-xl border border-white/5 text-center">
        <p className="text-slate-400">No add-on riders available for this plan.</p>
        <p className="text-sm text-slate-500 mt-2">You can un-check and skip this step.</p>
      </div>
    );
  }

  const toggleRider = (code: string) => {
    if (selectedRiderCodes.includes(code)) {
      onChange(selectedRiderCodes.filter(c => c !== code));
    } else {
      onChange([...selectedRiderCodes, code]);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {riders.map((rider) => {
          const isSelected = selectedRiderCodes.includes(rider.code);
          return (
            <Card
              key={rider.code}
              className={`cursor-pointer transition-all ${
                isSelected
                  ? "border-sky-500 bg-sky-500/10 ring-1 ring-sky-500"
                  : "border-white/10 hover:border-white/30 glass"
              }`}
              onClick={() => toggleRider(rider.code)}
            >
              <CardContent className="p-4 flex items-start gap-4 h-full">
                <div className="pt-1">
                  <Checkbox 
                    checked={isSelected}
                    onCheckedChange={() => toggleRider(rider.code)}
                    className="data-[state=checked]:bg-sky-500 data-[state=checked]:border-sky-500"
                  />
                </div>
                <div className="flex-grow">
                  <h3 className="font-medium text-white mb-1">{rider.name}</h3>
                  <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-300 mt-2">
                    {rider.covers_consumables && (
                      <span className="flex items-center text-sky-300 bg-sky-500/10 px-2 py-1 rounded">
                        <FlaskConical className="w-3 h-3 mr-1" /> Consumables
                      </span>
                    )}
                    {rider.covers_opd && (
                      <span className="flex items-center text-emerald-300 bg-emerald-500/10 px-2 py-1 rounded">
                        <Stethoscope className="w-3 h-3 mr-1" /> OPD
                      </span>
                    )}
                    {rider.covers_maternity && (
                      <span className="flex items-center text-pink-300 bg-pink-500/10 px-2 py-1 rounded">
                        <Baby className="w-3 h-3 mr-1" /> Maternity
                      </span>
                    )}
                    {(rider.covers_dental || rider.covers_critical_illness) && (
                      <span className="flex items-center text-indigo-300 bg-indigo-500/10 px-2 py-1 rounded">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Extended Cov.
                      </span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
