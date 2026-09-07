"use client";

import React, { useState } from "react";
import { ShieldCheck, Search, ArrowRight, CheckCircle2, XCircle, AlertTriangle, Clock } from "lucide-react";
import { api } from "@/lib/api";

export default function VerificationToolsPage() {
  const [source, setSource] = useState("GST");
  const [identifier, setIdentifier] = useState("07AAAAA0000A1Z5");
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const presets = [
    { label: "GST: Valid (07AAAAA0000A1Z5)", source: "GST", id: "07AAAAA0000A1Z5" },
    { label: "GST: Invalid / Cancelled", source: "GST", id: "GST123INVALID" },
    { label: "GST: Expired Registration", source: "GST", id: "GST123EXPIRED" },
    { label: "GST: Service Unavailable (Down)", source: "GST", id: "GST123DOWN" },
    { label: "Debarment: Clean Vendor", source: "Debarment", id: "ALPHA_TECH_001" },
    { label: "Debarment: Blacklisted Entity", source: "Debarment", id: "DEBARRED_VENDOR_99" },
    { label: "Udyam: MSME Valid", source: "Udyam", id: "UDYAM-DL-01-008912" },
  ];

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.queryVerification(source, identifier);
      setResult(res);
    } catch (err: any) {
      alert(err.message || "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          External Verification Adapter Sandbox
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Directly execute queries against government registry adapters (GST, Udyam/MSME, Debarment, UDIN, BIS). In Phase 3, these mock endpoints connect to production live gateways.
        </p>
      </div>

      {/* Quick Presets */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
          Demo Test Scenarios:
        </span>
        <div className="flex flex-wrap gap-2">
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setSource(p.source);
                setIdentifier(p.id);
              }}
              className="text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 font-semibold px-2.5 py-1.5 rounded-lg border border-slate-200 transition"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Query Form */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <form onSubmit={handleVerify} className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end">
          <div className="sm:col-span-4">
            <label className="text-xs font-bold text-slate-700 block mb-1">Verification Source</label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full p-2.5 border border-slate-300 rounded-lg text-xs outline-none bg-white font-semibold"
            >
              <option value="GST">GSTIN Registry (GSTN)</option>
              <option value="Debarment">Central Debarment & Blacklist (CPPP/GeM)</option>
              <option value="Udyam">Ministry of MSME (Udyam)</option>
              <option value="UDIN">ICAI UDIN CA Verification</option>
              <option value="BIS">Bureau of Indian Standards (CRS)</option>
            </select>
          </div>

          <div className="sm:col-span-6">
            <label className="text-xs font-bold text-slate-700 block mb-1">Query Identifier</label>
            <input
              type="text"
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="e.g. 07AAAAA0000A1Z5"
              className="w-full p-2.5 border border-slate-300 rounded-lg text-xs outline-none focus:border-blue-600 font-mono"
            />
          </div>

          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded-lg text-xs transition shadow-sm"
            >
              {loading ? "Querying..." : "Execute"}
            </button>
          </div>
        </form>
      </div>

      {/* Result Display */}
      {result && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Query Response</span>
              <h3 className="text-base font-bold text-slate-900">{result.source} Adapter Result</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                result.status === "VALID" ? "bg-emerald-50 text-emerald-800 border-emerald-300" :
                result.status === "UNAVAILABLE" ? "bg-purple-50 text-purple-800 border-purple-300" :
                "bg-rose-50 text-rose-800 border-rose-300"
              }`}>
                {result.status}
              </span>
            </div>
          </div>

          <pre className="p-4 bg-slate-900 text-emerald-400 rounded-xl text-xs font-mono overflow-x-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
