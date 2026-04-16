"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ListTodo, CheckCircle2, ChevronDown } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useState } from "react";
import { Button } from "@/components/ui/button";

interface ActionItem {
  type: string;
  item_name?: string;
  instruction: string;
}

interface Props {
  actionItems: ActionItem[];
}

export function ActionChecklist({ actionItems }: Props) {
  const [expanded, setExpanded] = useState(true);

  if (!actionItems || actionItems.length === 0) {
    return (
      <Alert className="bg-green-500/10 border-green-500/20 text-green-400">
        <CheckCircle2 className="w-5 h-5 text-green-400" />
        <AlertTitle>All Good!</AlertTitle>
        <AlertDescription>
          We didn't detect any high-risk items requiring your immediate action before discharge.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className="glass border-sky-500/30 shadow-lg shadow-sky-500/5">
      <CardHeader className="bg-sky-500/10 cursor-pointer flex flex-row items-center justify-between" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-2">
          <ListTodo className="w-5 h-5 text-sky-400" />
          <CardTitle className="text-lg text-white">Pre-Discharge Action Checklist</CardTitle>
        </div>
        <Button variant="ghost" size="icon" className="text-sky-400 hover:text-sky-300 hover:bg-sky-400/20">
          <ChevronDown className={`w-5 h-5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </Button>
      </CardHeader>
      
      {expanded && (
        <CardContent className="p-6">
          <p className="text-sm text-slate-300 mb-6">
            Complete these recommended actions with the hospital billing department <strong>before</strong> signing the final discharge summary to minimize out-of-pocket expenses.
          </p>
          
          <ul className="space-y-4">
            {actionItems.map((action, idx) => (
              <li key={idx} className="flex gap-4 p-4 rounded-lg bg-slate-900/50 border border-white/5">
                <div className="flex-shrink-0 mt-0.5">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 font-bold text-xs ring-1 ring-sky-500/30">
                    {idx + 1}
                  </div>
                </div>
                <div>
                  <h4 className="text-white font-medium capitalize mb-1">
                    {(action.type || 'Action Item').replace(/_/g, ' ')}
                  </h4>
                  <p className="text-slate-400 text-sm">{action.instruction}</p>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      )}
    </Card>
  );
}
