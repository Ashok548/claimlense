"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getFirebaseIdToken } from "@/lib/firebase";

interface Props {
  analysisId: string;
}

export function DownloadReportButton({ analysisId }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setLoading(true);
    setError(null);
    try {
      const firebaseToken = await getFirebaseIdToken();
      const res = await fetch(`/api/reports/${analysisId}/pdf`, {
        headers: {
          Authorization: `Bearer ${firebaseToken}`,
        },
      });
      if (!res.ok) {
        throw new Error("Failed to formulate report");
      }
      
      const { download_url } = await res.json();
      
      // Perform the download
      const a = document.createElement("a");
      a.href = download_url;
      a.download = `ClaimLense_Analysis_${analysisId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An error occurred";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex w-full flex-col items-stretch sm:w-auto sm:items-center">
      <Button 
        variant="outline" 
        onClick={handleDownload}
        disabled={loading}
        className="h-9 w-full border-white/10 px-3 text-sm text-slate-300 hover:text-white glass sm:w-auto"
      >
        {loading ? (
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        ) : (
          <Download className="w-4 h-4 mr-2" />
        )}
        {loading ? "Generating..." : "Get PDF Report"}
      </Button>
      {error && <span className="text-red-400 text-xs mt-2">{error}</span>}
    </div>
  );
}
