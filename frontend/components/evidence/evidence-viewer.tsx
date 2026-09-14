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
      <section className="min-w-0"><h3 className="font-semibold">{rule.document_name || "No source document"}</h3><p className="my-2 text-sm muted">{rule.page ? `Page ${rule.page}` : "Page not recorded"}</p>
        {error && <p role="alert" className="my-3 text-red-700">{error}</p>}
        {source && <a className="mb-3 inline-block text-teal underline" href={`${source}#page=${rule.page || 1}`} target="_blank" rel="noreferrer">Open original PDF</a>}
        {preview && preview.id === docId ? <object key={`${preview.url}:${rule.page}`} type="application/pdf" aria-label={`Original PDF: ${rule.document_name}, page ${rule.page || 1}`} data={`${preview.url}#page=${rule.page || 1}`} className="h-[560px] w-full rounded border border-line"><p>Inline PDFs are not supported here. Use “Open original PDF”.</p></object> : <p className="border border-line bg-slate-50 p-6 text-sm muted">{docId && !error ? "Loading source PDF…" : "No preview available; no simulated page is shown."}</p>}
      </section>
      <section><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold">{rule.rule_name}</h3><StatusBadge status={rule.result}/></div><p className="my-3 text-sm muted">{rule.description}</p><dl className="space-y-3 text-sm">{[["Extracted value", rule.extracted_value], ["Requirement", rule.expected_value], ["Confidence (heuristic)", rule.confidence == null ? "Not recorded" : formatPercent(rule.confidence)], ["Method / source", rule.source], ["Extractor / retriever", rule.model_version], ["Evidence", rule.evidence], ["Bounding box (PDF points)", rule.bounding_box?.join(", ")], ["Rule version", rule.rule_version], ["Evaluated at", rule.timestamp]].map(([label, value]) => <div key={label}><dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt><dd className="mt-1 break-words">{value || "Not recorded"}</dd></div>)}</dl><p className="mt-4 border-t border-line pt-3 text-xs muted">No model inference is implied by a confidence value. Offline connector results are not live registry verification. Bounding boxes are reported coordinates, not a simulated overlay.</p></section>
    </div>
  </div>;
}
