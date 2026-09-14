"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { services } from "@/lib/services";
export function AddBidder({ tenderId }: { tenderId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  return <details className="panel p-5"><summary className="cursor-pointer font-semibold">Register a bidder</summary><form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={async event => {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    setBusy(true); setError("");
    try { const bid = await services.createBid(tenderId, String(data.get("name")), String(data.get("gstin"))); router.push(`/evaluations/${encodeURIComponent(bid.id)}`); router.refresh(); }
    catch (error) { setError(error instanceof Error ? error.message : "Could not register bidder"); }
    finally { setBusy(false); }
  }}><label className="flex flex-col gap-1 text-sm">Legal bidder name<input required maxLength={250} name="name" className="rounded border border-line p-2" disabled={busy}/></label><label className="flex flex-col gap-1 text-sm">GSTIN (optional)<input maxLength={15} name="gstin" className="rounded border border-line p-2" disabled={busy}/></label><button className="btn btn-primary" disabled={busy}>{busy ? "Registering…" : "Register and upload"}</button></form>{error && <p role="alert" className="mt-3 text-red-700">{error}</p>}</details>;
}
