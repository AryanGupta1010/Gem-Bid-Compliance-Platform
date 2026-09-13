"use client";

import { FileText, Focus, MapPin, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Bidder } from "@/lib/types";
import { formatPercent } from "@/lib/utils";
import { StatusBadge } from "./status-badge";

export function EvidenceViewer({ bidder }: { bidder: Bidder }) {
  const [selected, setSelected] = useState(0);
  const rule = bidder.rules?.[selected];

  if (!rule) {
    return (
      <div className="panel p-10 text-center text-slate-500">
        No evidence available yet. Upload documents to begin automated extraction.
      </div>
    );
  }

  return (
    <div className="panel overflow-hidden">
      <div className="grid lg:grid-cols-[180px_minmax(320px,1fr)_330px]">
        <div className="border-b border-line bg-slate-50 p-3 lg:border-b-0 lg:border-r">
          <p className="mb-3 px-2 text-[11px] font-bold uppercase tracking-wide text-slate-500">Evidence index</p>
          <div className="space-y-1">
            {bidder.rules.map((item, index) => (
              <button
                key={item.id}
                onClick={() => setSelected(index)}
                className={`w-full rounded-lg px-3 py-2 text-left text-xs transition ${selected === index ? "bg-white font-semibold text-navy shadow-sm" : "text-slate-600 hover:bg-white"}`}
              >
                <span className="block">{item.rule_name}</span>
                <span className="mt-1 block text-[10px] text-slate-400">{item.document_name || "Unknown Document"}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="min-h-[520px] bg-[#e8edef] p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="section-title">Document preview</p>
              <p className="mt-1 text-sm font-semibold">{rule.document_name || "Unknown Document"}</p>
            </div>
            <span className="rounded bg-white px-2 py-1 text-xs text-slate-500">Page {rule.page || 1}</span>
          </div>
          <div className="relative mx-auto min-h-[410px] max-w-[470px] overflow-hidden rounded border border-slate-300 bg-white p-8 shadow-md">
            <div className="absolute right-6 top-6 rounded border border-slate-200 p-2 text-slate-300"><FileText size={26} /></div>
            <div className="mb-8 text-center">
              <div className="mx-auto h-6 w-36 rounded bg-slate-200" />
              <div className="mx-auto mt-2 h-2 w-52 rounded bg-slate-100" />
              <div className="mx-auto mt-1 h-2 w-40 rounded bg-slate-100" />
            </div>
            <div className="space-y-3">
              {[1, 2, 3, 4, 5, 6].map((line) => <div key={line} className="h-2 rounded bg-slate-100" style={{ width: `${55 + line * 6}%` }} />)}
            </div>
            
            {rule.bounding_box && rule.bounding_box.length === 4 && rule.bounding_box[2] > rule.bounding_box[0] ? (
              <div 
                className="absolute border-2 border-amber-500 bg-amber-100/45 p-3 shadow-[0_0_0_4px_rgba(245,158,11,0.12)] transition-all"
                style={{
                  left: `${(rule.bounding_box[0] / 600) * 100}%`,
                  top: `${(rule.bounding_box[1] / 800) * 100}%`,
                  width: `${((rule.bounding_box[2] - rule.bounding_box[0]) / 600) * 100}%`,
                  height: `${((rule.bounding_box[3] - rule.bounding_box[1]) / 800) * 100}%`,
                  minHeight: "40px",
                  minWidth: "100px",
                }}
              >
                <div className="flex items-center gap-2 text-xs font-bold text-amber-800"><Focus size={14} /> Evidence region</div>
                <p className="mt-2 font-mono text-xs text-amber-900 line-clamp-2">{rule.extracted_value}</p>
              </div>
            ) : (
               <div className="absolute left-[14%] top-[48%] w-[72%] rounded border border-slate-200 bg-slate-50/80 p-3 text-center text-sm text-slate-500">
                 No visual region available for this evidence.
               </div>
            )}
            
            <div className="absolute bottom-5 right-6 text-[10px] text-slate-400">Scanned government document</div>
          </div>
        </div>

        <div className="border-t border-line bg-white p-5 lg:border-l lg:border-t-0">
          <div className="flex items-center justify-between">
            <p className="section-title">Rule analysis</p>
            <StatusBadge status={rule.result} />
          </div>
          <h3 className="mt-3 text-xl font-semibold">{rule.rule_name}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">{rule.description}</p>

          <div className="mt-5 space-y-3">
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Extracted value</p>
              <p className="mt-1 font-mono text-sm font-semibold">{rule.extracted_value}</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Expected requirement</p>
              <p className="mt-1 text-sm font-semibold">{rule.expected_value}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Confidence</p><p className="mt-1 text-sm font-semibold">{rule.confidence ? formatPercent(rule.confidence) : "N/A"}</p></div>
              <div><p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Page</p><p className="mt-1 text-sm font-semibold">{rule.page || "N/A"}</p></div>
            </div>
          </div>

          <div className="mt-5 rounded-lg border border-cyan-100 bg-cyan-50 p-3 text-xs leading-5 text-cyan-900">
            <div className="flex gap-2 font-semibold"><ShieldCheck size={15} /> Explainability note</div>
            <p className="mt-1">AI located the relevant evidence. Deterministic verification evaluated the requirement.</p>
          </div>

          <div className="mt-5 border-t border-line pt-4 text-xs text-slate-500">
            <p><MapPin size={13} className="mr-1 inline" /> Source: {rule.source || "Unknown"}</p>
            <p className="mt-2">Model: {rule.model_version || "N/A"}</p>
            <p className="mt-1">Rule: {rule.rule_version || "N/A"}</p>
            <p className="mt-1">Timestamp: {rule.timestamp ? new Date(rule.timestamp).toLocaleString() : "N/A"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
