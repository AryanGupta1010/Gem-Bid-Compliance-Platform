"use client";
import { useEffect, useState } from "react";
import type { Bidder } from "@/lib/types";
import { apiUrl } from "@/lib/services";
import { formatPercent } from "@/lib/utils";
import { StatusBadge } from "../ui/status-badge";
export function EvidenceViewer({ bidder }: { bidder: Bidder }) {
  const [selected, setSelected] = useState("");
  const rule = bidder.rules.find(r => r.id === selected) || bidder.rules[0];
  const docId = rule?.document_id;
  const [preview, setPreview] = useState<{ id: string; url: string } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setPreview(null); setError("");
    if (!docId) return;
    const controller = new AbortController();
    let url: string | undefined;
    let cancelled = false;
    const timer = setTimeout(() => controller.abort(), 30000);
    async function loadPreview(id: string) {
      try {
        const response = await fetch(apiUrl(`/documents/${encodeURIComponent(id)}/content`), { signal: controller.signal });
        if (!response.ok) throw new Error("Document storage unavailable");
        const blob = await response.blob();
        if (cancelled) return;
        url = URL.createObjectURL(blob); setPreview({ id, url });
      } catch {
        if (!cancelled) setError("Document preview unavailable or timed out. Check storage or open the source PDF.");
      } finally { clearTimeout(timer); }
    }
    void loadPreview(docId);
    return () => { cancelled = true; controller.abort(); clearTimeout(timer); if (url) URL.revokeObjectURL(url); };
  }, [docId]);
  if (!rule) return <p className="panel p-5">No rule evidence available.</p>;
  const source = docId ? `/api/documents/${encodeURIComponent(docId)}/content` : null;
  return <div className="panel overflow-hidden">
    <h2 className="border-b border-line p-5 text-lg font-semibold">Rule results and evidence</h2>
    <div className="overflow-x-auto"><table className="data-table min-w-[650px]"><thead><tr><th>Rule</th><th>Actual value</th><th>Required value</th><th>Result</th><th>Evidence</th></tr></thead><tbody>{bidder.rules.map(r => <tr key={r.id}><td className="font-semibold">{r.rule_name}</td><td>{r.extracted_value ?? "Not available"}</td><td>{r.expected_value ?? "Not specified"}</td><td><StatusBadge status={r.result}/></td><td><button aria-pressed={rule.id === r.id} className="btn btn-secondary" onClick={() => setSelected(r.id)}>Inspect</button></td></tr>)}</tbody></table></div>
    <div className="grid gap-5 p-5 xl:grid-cols-[minmax(0,1fr)_320px]">
      <section className="min-w-0">
        <h3 className="font-semibold">{rule.document_name || "No source document"}</h3>
        <p className="my-2 text-sm muted">{rule.page ? `Page ${rule.page}` : "Page not recorded"}</p>
        
        {source && <a className="mb-3 inline-block text-teal underline" href={`${source}#page=${rule.page || 1}`} target="_blank" rel="noreferrer">Download original PDF</a>}
        
        {docId && rule.page ? (
          <div className="relative w-full overflow-hidden rounded border border-line bg-slate-50 shadow-inner" style={{ minHeight: '600px' }}>
            <img 
              src={apiUrl(`/api/documents/${docId}/pages/${rule.page}`)} 
              alt={`Page ${rule.page} of ${rule.document_name}`}
              className="block h-auto w-full object-contain"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.nextElementSibling?.classList.remove('hidden');
              }}
            />
            <div className="hidden absolute inset-0 flex items-center justify-center p-6 text-sm muted">
              Page preview unavailable from storage.
            </div>
            
            {rule.bounding_box && rule.bounding_box.length === 4 && (
              <div 
                className="absolute border-2 border-red-500 bg-red-500/20 mix-blend-multiply"
                style={{
                  left: `${rule.bounding_box[0]}%`,
                  top: `${rule.bounding_box[1]}%`,
                  width: `${rule.bounding_box[2] - rule.bounding_box[0]}%`,
                  height: `${rule.bounding_box[3] - rule.bounding_box[1]}%`,
                }}
                title="AI Evidence Location"
              />
            )}
          </div>
        ) : (
          <p className="border border-line bg-slate-50 p-6 text-sm muted">No page preview available for this evidence.</p>
        )}
      </section>
      <section>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-semibold">{rule.rule_name}</h3>
          <StatusBadge status={rule.result}/>
        </div>
        <p className="my-3 text-sm muted">{rule.description}</p>
        <dl className="space-y-3 text-sm">
          {[
            ["Extracted value", rule.extracted_value],
            ["Requirement", rule.expected_value],
            ["Confidence", rule.confidence == null ? "Not recorded" : formatPercent(rule.confidence)],
            ["Method / source", rule.source],
            ["Extractor / retriever", rule.model_version],
            ["Evidence", rule.evidence],
            ["Bounding box", rule.bounding_box ? "Mapped to image" : "None"],
            ["Rule version", rule.rule_version],
            ["Evaluated at", rule.timestamp ? new Date(rule.timestamp).toLocaleString() : "Not recorded"]
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt>
              <dd className="mt-1 break-words">{value || "Not recorded"}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  </div>;
}
