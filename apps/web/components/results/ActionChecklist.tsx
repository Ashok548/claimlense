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
      <CardHeader className="flex cursor-pointer flex-row items-center justify-between gap-3 bg-sky-500/10 px-4 py-4 sm:px-5" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-2">
          <ListTodo className="h-5 w-5 text-sky-400" />
          <CardTitle className="text-base text-white sm:text-lg">Pre-Discharge Action Checklist</CardTitle>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-sky-400 hover:bg-sky-400/20 hover:text-sky-300">
          <ChevronDown className={`h-5 w-5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </Button>
      </CardHeader>
      
      {expanded && (
        <CardContent className="p-4 sm:p-5">
          <p className="mb-4 text-sm leading-6 text-slate-300">
            Complete these recommended actions with the hospital billing department <strong>before</strong> signing the final discharge summary to minimize out-of-pocket expenses.
          </p>
          
          <ul className="space-y-1 sm:space-y-2">
            {actionItems.map((action, idx) => (
              <li key={idx} className="flex items-start gap-2 sm:gap-3 rounded-lg border border-white/5 bg-slate-900/50 p-2.5 sm:p-3 !mb-0">
                <div className="mt-0.5 flex-shrink-0">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-sky-500/20 text-xs font-bold text-sky-400 ring-1 ring-sky-500/30">
                    {idx + 1}
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <h4 className="mb-1 text-sm font-medium capitalize text-white sm:text-base">
                    {(action.type || 'Action Item').replace(/_/g, ' ')}
                  </h4>
                  <p className="text-sm leading-6 break-words text-slate-400">{action.instruction}</p>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      )}
    </Card>
  );
}
