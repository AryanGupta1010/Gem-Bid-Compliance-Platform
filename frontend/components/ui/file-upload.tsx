"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { services } from "@/lib/services";
export function FileUpload({ bidId, tenderId }: { bidId?: string; tenderId?: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  
  if (!bidId && !tenderId) return null;
  
  return <section className="panel p-5"><h2 className="font-semibold">{tenderId ? "Upload tender document" : "Upload bidder package"}</h2><p className="my-2 text-sm muted">One consolidated PDF, up to 50 MB and 200 pages. A new upload replaces the current evaluation when processing completes; previous packages remain stored.</p><label className="block text-sm">Select PDF<input type="file" accept=".pdf,application/pdf" disabled={busy} className="mt-2 block w-full" onChange={async event => {
    const file = event.currentTarget.files?.[0]; event.currentTarget.value = "";
    if (!file) return;
    setBusy(true); setError("");
    try { 
      if (tenderId) {
        await services.uploadTenderDocument(tenderId, file);
      } else if (bidId) {
        await services.uploadDocument(bidId, file); 
      }
      router.refresh(); 
    }
    catch (error) { setError(error instanceof Error ? error.message : "Upload failed"); router.refresh(); }
    finally { setBusy(false); }
  }}/></label>{busy && <p role="status" className="mt-2">Uploading package…</p>}{error && <p role="alert" className="mt-3 text-red-700">{error}</p>}</section>;
}
