"use client";

import { useState } from "react";
import { UploadCloud, Loader2 } from "lucide-react";
import { services } from "@/lib/services";
import { useRouter } from "next/navigation";

export function FileUpload({ bidId }: { bidId: string }) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const doc = await services.uploadDocument(bidId, file);
      if (doc) {
        // Trigger a refresh so the page sees the new document status
        router.refresh();
      } else {
        setError("Failed to upload document.");
      }
    } catch (err) {
      setError("An error occurred during upload.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center transition hover:bg-slate-100">
      {isUploading ? (
        <div className="flex flex-col items-center justify-center text-teal">
          <Loader2 className="mb-3 animate-spin" size={32} />
          <p className="font-semibold">Uploading and sealing document...</p>
        </div>
      ) : (
        <label className="flex cursor-pointer flex-col items-center justify-center">
          <UploadCloud className="mb-3 text-slate-400" size={32} />
          <p className="font-semibold text-slate-700">Upload Bidder Document</p>
          <p className="mt-1 text-xs text-slate-500">PDF up to 50MB. Document will be securely hashed upon upload.</p>
          <input
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={handleFileChange}
            disabled={isUploading}
          />
          <span className="btn btn-secondary mt-4 inline-block">Select PDF</span>
        </label>
      )}
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
    </div>
  );
}
