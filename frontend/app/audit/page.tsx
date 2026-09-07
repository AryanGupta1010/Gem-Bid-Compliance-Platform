"use client";

import React, { useState, useEffect } from "react";
import { History, Shield, Search, RefreshCw, Filter, FileText } from "lucide-react";
import { api } from "@/lib/api";
import { AuditEvent } from "@/types";

export default function AuditTrailPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadAudit();
  }, []);

  async function loadAudit() {
    setLoading(true);
    try {
      const data = await api.getAllAudit(100);
      setEvents(data);
    } catch (err) {
      console.error("Failed to load audit trail", err);
    } finally {
      setLoading(false);
    }
  }

  const filtered = events.filter(
    (ev) =>
      ev.action.toLowerCase().includes(search.toLowerCase()) ||
      ev.entity_type.toLowerCase().includes(search.toLowerCase()) ||
      ev.entity_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Immutable System Audit Trail
            </h1>
            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-0.5 rounded-full">
              Full Traceability
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Cryptographically sealed and timestamped log of all tender updates, rule evaluations, verification queries, and human officer decisions.
          </p>
        </div>
        <button
          onClick={loadAudit}
          className="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white font-bold px-3.5 py-2 rounded-lg text-xs transition shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Log</span>
        </button>
      </div>

      {/* Filter bar */}
      <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
        <Search className="w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search by action, entity type, or identifier..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent border-none outline-none w-full text-xs text-slate-800 placeholder:text-slate-400"
        />
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider">
                <th className="py-3.5 px-4">Timestamp (UTC)</th>
                <th className="py-3.5 px-4">Action</th>
                <th className="py-3.5 px-4">Entity</th>
                <th className="py-3.5 px-4">Actor</th>
                <th className="py-3.5 px-4">Metadata / Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    No audit records match your query.
                  </td>
                </tr>
              ) : (
                filtered.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                      {new Date(ev.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-blue-700">
                      {ev.action}
                    </td>
                    <td className="py-3 px-4">
                      <span className="bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded mr-1.5">
                        {ev.entity_type}
                      </span>
                      <span className="font-mono text-[10px] text-slate-400">
                        {ev.entity_id.slice(0, 8)}...
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-800">
                      {ev.user_name || "System Automated Engine"}
                    </td>
                    <td className="py-3 px-4 text-slate-600 max-w-md truncate">
                      {ev.metadata_json ? JSON.stringify(ev.metadata_json) : "-"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
