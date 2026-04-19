"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, FileText, Loader2, Sparkles, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

import { ParseResponse } from "@/types/analyze";

interface Props {
  onItemsParsed: (items: any[]) => void;
  onStayDetected?: (icu_days: number | null, general_ward_days: number | null) => void;
  onError: (error: string) => void;
}

export function UploadZone({ onItemsParsed, onStayDetected, onError }: Props) {
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [mismatchWarning, setMismatchWarning] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];

    try {
      setUploading(true);
      setProgress(20);

      // Step 1: Upload file to Next.js server, which proxies to R2
      // (server-to-server avoids all CORS issues)
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await fetch("/api/upload", {
        method: "POST",
        body: formData, // No Content-Type header — browser sets it with the boundary
      });

      if (!uploadRes.ok) {
        const err = await uploadRes.json();
        throw new Error(err.error || "File upload failed");
      }

      const { key, jobId } = await uploadRes.json();
      setProgress(60);
      setUploading(false);
      setParsing(true);

      // Step 2: Trigger Parse (OCR + GPT-4o) — unchanged
      const fileType = file.type === "application/pdf" ? "PDF" : "IMAGE";
      const parseRes = await fetch("/api/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jobId, key, fileType: fileType.toLowerCase() }),
      });

      if (!parseRes.ok) {
        const errorData = await parseRes.json();
        throw new Error(errorData.error || "Parsing failed");
      }

      const parseData: ParseResponse = await parseRes.json();
      setParsing(false);

      if (parseData.items) {
        onItemsParsed(parseData.items);
      }

      // Pass stay duration info up so the wizard can skip the popup if detected
      if (onStayDetected) {
        onStayDetected(
          parseData.icu_days ?? null,
          parseData.general_ward_days ?? null,
        );
      }

      // Warn when extracted total differs from item sum after cleanup
      if (parseData.total_mismatch && parseData.extracted_total != null) {
        setMismatchWarning(
          `Parsed items sum to ₹${(parseData.calculated_total ?? 0).toLocaleString("en-IN")} ` +
          `but the bill shows ₹${parseData.extracted_total.toLocaleString("en-IN")}. ` +
          `Review the pre-filled items — some may be missing or need adjustment.`
        );
      } else {
        setMismatchWarning(null);
      }
    } catch (err: any) {
      setUploading(false);
      setParsing(false);
      onError(err.message || "An unexpected error occurred");
    }
  }, [onItemsParsed, onError]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  if (uploading || parsing) {
    return (
      <div className="border-2 border-dashed border-sky-500/50 rounded-2xl p-12 text-center bg-sky-500/5 flex flex-col items-center justify-center">
        <Loader2 className="w-12 h-12 animate-spin text-sky-400 mb-4" />
        <h3 className="text-xl font-bold text-white mb-2">
          {uploading ? "Uploading Bill..." : "AI is extracting items..."}
        </h3>
        <p className="text-slate-400 max-w-sm mb-6">
          {uploading
            ? "Securely transferring your file to our processing servers."
            : "Running OCR and GPT-4o Vision to structure your hospital bill. This may take up to 20 seconds."}
        </p>

        {uploading && (
          <div className="w-64 h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-sky-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>
    );
  }

  return (
    <>
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors ${isDragReject
          ? "border-red-500/50 bg-red-500/5"
          : isDragActive
            ? "border-sky-500 bg-sky-500/10"
            : "border-white/20 hover:border-sky-500/50 hover:bg-white/5 glass"
        }`}
    >
      <input {...getInputProps()} />

      <div className="flex justify-center mb-4">
        <div className="w-16 h-16 rounded-full bg-sky-500/20 flex items-center justify-center">
          <UploadCloud className="w-8 h-8 text-sky-400" />
        </div>
      </div>

      <h3 className="text-xl font-bold text-white mb-2">
        Drag & Drop your Hospital Bill
      </h3>
      <p className="text-slate-400 mb-6">
        Supports PDF, JPG, and PNG up to 10MB.
      </p>

      <Button type="button" className="bg-slate-800 hover:bg-slate-700 text-white border border-white/10">
        <FileText className="w-4 h-4 mr-2" />
        Browse Files
      </Button>

      <div className="mt-8 flex items-center justify-center gap-2 text-sm text-sky-400 bg-sky-500/10 inline-flex px-3 py-1.5 rounded-full mx-auto">
        <Sparkles className="w-4 h-4" />
        <span>Our AI will automatically extract all line items</span>
      </div>
    </div>

    {mismatchWarning && (
      <div className="mt-3 flex items-start gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-sm text-amber-300">
        <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
        <span>{mismatchWarning}</span>
      </div>
    )}
  </>
  );
}
