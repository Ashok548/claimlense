"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { BedDouble, AlertCircle } from "lucide-react";

interface StayDuration {
  icuDays: number | undefined;
  generalWardDays: number | undefined;
}

interface Props {
  open: boolean;
  onConfirm: (duration: StayDuration) => void;
}

export function StayDurationDialog({ open, onConfirm }: Props) {
  const [icuDays, setIcuDays] = useState<number | undefined>();
  const [generalWardDays, setGeneralWardDays] = useState<number | undefined>();
  const [validationError, setValidationError] = useState<string | null>(null);

  const totalDays = (icuDays ?? 0) + (generalWardDays ?? 0);
  const hasAnyDays = (icuDays ?? 0) > 0 || (generalWardDays ?? 0) > 0;

  const handleConfirm = () => {
    if (!hasAnyDays) {
      setValidationError("Please enter at least one day (ICU or General Ward).");
      return;
    }
    setValidationError(null);
    onConfirm({ icuDays, generalWardDays });
  };

  const handleIcuChange = (val: string) => {
    setValidationError(null);
    setIcuDays(parseInt(val) > 0 ? parseInt(val) : undefined);
  };

  const handleWardChange = (val: string) => {
    setValidationError(null);
    setGeneralWardDays(parseInt(val) > 0 ? parseInt(val) : undefined);
  };

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent
        className="bg-slate-900 border border-white/10 text-white max-w-md"
        showCloseButton={false}
      >
        <DialogHeader>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 bg-amber-500/10 rounded-lg">
              <BedDouble className="w-5 h-5 text-amber-400" />
            </div>
            <DialogTitle className="text-white text-lg">Hospital Stay Details Required</DialogTitle>
          </div>
          <DialogDescription className="text-slate-400 text-sm leading-relaxed">
            We couldn't automatically detect your hospital stay duration from the bill.
            This is needed to accurately calculate your daily room rent rate.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 mt-2">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-slate-300 text-sm">
                ICU / ICCU / HDU Days
              </Label>
              <Input
                type="number"
                min={0}
                className="bg-slate-800 border-white/10 text-white"
                placeholder="0"
                value={icuDays ?? ""}
                onChange={(e) => handleIcuChange(e.target.value)}
              />
              <p className="text-xs text-slate-500">Days in intensive care</p>
            </div>

            <div className="space-y-2">
              <Label className="text-slate-300 text-sm">
                General Ward Days
              </Label>
              <Input
                type="number"
                min={0}
                className="bg-slate-800 border-white/10 text-white"
                placeholder="0"
                value={generalWardDays ?? ""}
                onChange={(e) => handleWardChange(e.target.value)}
              />
              <p className="text-xs text-slate-500">Days in regular room / ward</p>
            </div>
          </div>

          {totalDays > 0 && (
            <div className="bg-sky-500/10 border border-sky-500/20 rounded-lg px-4 py-2 text-sm text-sky-300">
              Total stay: <span className="font-semibold">{totalDays} day{totalDays !== 1 ? "s" : ""}</span>
              {(icuDays ?? 0) > 0 && (generalWardDays ?? 0) > 0 && (
                <span className="text-slate-400 ml-1">
                  ({icuDays} ICU + {generalWardDays} ward)
                </span>
              )}
            </div>
          )}

          {validationError && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {validationError}
            </div>
          )}

          <Button
            onClick={handleConfirm}
            className="w-full bg-sky-500 hover:bg-sky-400 text-white font-semibold"
          >
            Confirm & Continue
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
