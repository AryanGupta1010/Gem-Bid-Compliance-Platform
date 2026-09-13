"use client";

import { useState } from "react";
import { MessageSquareText, UserRoundCheck, Loader2 } from "lucide-react";
import { services } from "@/lib/services";
import { useRouter } from "next/navigation";

export function DecisionPanel({ bidId, initialDecision, initialNote }: { bidId: string, initialDecision?: string, initialNote?: string }) {
  const [decision, setDecision] = useState(initialDecision || "");
  const [note, setNote] = useState(initialNote || "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleDecision = async (newDecision: string) => {
    setDecision(newDecision);
    await submitDecision(newDecision, note);
  };

  const handleNoteSubmit = async () => {
    if (!decision) return;
    await submitDecision(decision, note);
  };

  const submitDecision = async (d: string, n: string) => {
    setIsSubmitting(true);
    try {
      await services.recordDecision(bidId, d, n);
      router.refresh();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="panel p-5">
      <div className="flex items-start gap-3">
        <div className="rounded-lg bg-amber-50 p-2.5 text-amber-700"><UserRoundCheck size={19} /></div>
        <div className="flex-1 flex justify-between items-start">
          <div>
            <p className="section-title">Human control</p>
            <h2 className="mt-1 text-lg font-semibold">Procurement Officer Decision</h2>
            <p className="mt-1 text-sm muted">The system recommends and explains. The officer remains the final authority.</p>
          </div>
          {isSubmitting && <Loader2 size={18} className="animate-spin text-slate-400" />}
        </div>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-4">
        {["Approve", "Reject", "Request Clarification", "Keep Under Review"].map((item) => (
          <button 
            key={item} 
            onClick={() => handleDecision(item)} 
            disabled={isSubmitting}
            className={`btn ${decision === item ? "btn-primary" : "btn-secondary"}`}
          >
            {item}
          </button>
        ))}
      </div>
      <div className="mt-4">
        <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">Officer note</label>
        <div className="flex gap-2">
          <textarea 
            className="min-h-20 flex-1 rounded-lg border border-line p-3 text-sm outline-none focus:border-teal disabled:opacity-50" 
            placeholder="Record rationale, clarification request, or review notes..." 
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={isSubmitting}
          />
          <button 
            onClick={handleNoteSubmit}
            disabled={isSubmitting || !decision}
            className="btn btn-secondary h-fit disabled:opacity-50"
          >
            <MessageSquareText size={16} /> 
            Save note
          </button>
        </div>
      </div>
      {decision && <p className="mt-3 text-xs text-teal font-semibold">Recorded decision: {decision}. Note saved securely to audit log.</p>}
    </div>
  );
}
