"use client";

import { useEffect, useState } from "react";
import { InsurerResponse } from "@/types/analyze";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

interface Props {
  selectedInsurerId: string;
  onSelect: (insurer: InsurerResponse) => void;
}

export function InsurerSelector({ selectedInsurerId, onSelect }: Props) {
  const [insurers, setInsurers] = useState<InsurerResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/insurers")
      .then((res) => res.json())
      .then((data) => {
        setInsurers(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-sky-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {insurers.map((insurer) => (
          <Card
            key={insurer.id}
            className={`cursor-pointer transition-all ${
              selectedInsurerId === String(insurer.id)
                ? "border-sky-500 bg-sky-500/10 ring-1 ring-sky-500"
                : "border-white/10 hover:border-white/30 glass"
            }`}
            onClick={() => onSelect(insurer)}
          >
            <CardContent className="p-4 flex flex-col h-full justify-between">
              <div>
                <h3 className="text-base font-medium text-white mb-1 sm:text-lg">{insurer.name}</h3>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {insurer.plans && insurer.plans.length > 0 && (
                  <Badge variant="secondary" className="bg-white/5 text-slate-300">
                    {insurer.plans.length} Plans
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

