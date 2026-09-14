"use client";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { services } from "@/lib/services";
export function CreateTenderModal() {
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  return <><button className="btn btn-primary" onClick={() => { setError(""); dialog.current?.showModal(); }}>Create tender</button><dialog ref={dialog} aria-labelledby="create-tender-title" className="w-[calc(100%-2rem)] max-w-lg rounded-lg p-6 backdrop:bg-slate-900/50" onCancel={event => { if (busy) event.preventDefault(); }}><h2 id="create-tender-title" className="text-xl font-semibold">Create tender</h2><form className="mt-4 space-y-4" onSubmit={async event => {
    event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true); setError("");
    try { const tender = await services.createTender({ title: String(data.get("title")), department: String(data.get("department")), deadline: String(data.get("deadline")), budget: String(data.get("budget")) }); dialog.current?.close(); router.push(`/tenders/${encodeURIComponent(tender.id)}`); router.refresh(); }
    catch (error) { setError(error instanceof Error ? error.message : "Tender could not be created"); }
    finally { setBusy(false); }
  }}>{[["title", "Tender title", "text"], ["department", "Department", "text"], ["deadline", "Deadline", "date"], ["budget", "Budget (include currency)", "text"]].map(([name, label, type]) => <label className="block text-sm font-semibold" key={name}>{label}<input required maxLength={name === "budget" ? 100 : 250} name={name} type={type} disabled={busy} className="mt-1 block w-full rounded border border-line p-2 font-normal"/></label>)}{error && <p role="alert" className="text-sm text-red-700">{error}</p>}<div className="flex justify-end gap-3"><button type="button" className="btn btn-secondary" disabled={busy} onClick={() => dialog.current?.close()}>Cancel</button><button className="btn btn-primary" disabled={busy}>{busy ? "Creating…" : "Create tender"}</button></div></form></dialog></>;
}
