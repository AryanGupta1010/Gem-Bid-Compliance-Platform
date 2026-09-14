"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { services } from "@/lib/services";
type Props = { bidId: string; initialDecision?: string | null; initialNote?: string | null; disabled?: boolean };
export function DecisionPanel({ bidId, initialDecision, initialNote, disabled = false }: Props) {
  const [decision, setDecision] = useState(initialDecision || "");
  const [note, setNote] = useState(initialNote || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  return <section className="panel p-5"><h2 className="text-lg font-semibold">Human decision</h2><p className="mt-2 text-sm muted">Your decision does not alter the deterministic rule results. Select an outcome, explain the rationale, then explicitly save.</p><p className="mt-3 text-sm">Recorded decision: <strong>{initialDecision || "None"}</strong></p><form className="mt-4 space-y-4" onSubmit={async event => {
    event.preventDefault(); setBusy(true); setError("");
    try { await services.recordDecision(bidId, decision, note); router.refresh(); }
    catch (error) { setError(error instanceof Error ? error.message : "Decision could not be saved"); }
    finally { setBusy(false); }
  }}><label className="block text-sm font-semibold">Officer outcome<select required className="mt-2 block w-full rounded border border-line p-2" value={decision} onChange={e => setDecision(e.target.value)} disabled={busy || disabled}><option value="">Select an outcome</option>{["Approve", "Reject", "Request Clarification", "Keep Under Review"].map(item => <option key={item}>{item}</option>)}</select></label><label className="block text-sm font-semibold">Rationale<textarea required maxLength={4000} className="mt-2 block min-h-24 w-full rounded border border-line p-3 font-normal" value={note} onChange={e => setNote(e.target.value)} disabled={busy || disabled}/></label><button className="btn btn-primary" disabled={busy || disabled || !decision || !note.trim()}>{busy ? "Saving…" : "Record decision and rationale"}</button>{disabled && <p className="text-sm muted">Complete package processing before recording a decision.</p>}{error && <p role="alert" className="text-sm text-red-700">{error}</p>}</form></section>;
}
