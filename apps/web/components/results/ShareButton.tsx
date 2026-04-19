"use client";

import { Share2, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

interface Props {
  analysisId: string;
  insurerName: string;
}

export function ShareButton({ analysisId, insurerName }: Props) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    const url = `${window.location.origin}/results/${analysisId}`;
    const title = `ClaimSmart Analysis — ${insurerName}`;

    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title, url });
        return;
      } catch {
        // User dismissed the share sheet — fall through to clipboard copy
      }
    }

    // Fallback: copy link to clipboard
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Button
      onClick={handleShare}
      className="flex-1 sm:flex-none bg-sky-500 hover:bg-sky-400 text-white"
    >
      {copied ? (
        <>
          <Check className="w-4 h-4 mr-2" />
          Copied!
        </>
      ) : (
        <>
          <Share2 className="w-4 h-4 mr-2" />
          Share
        </>
      )}
    </Button>
  );
}
