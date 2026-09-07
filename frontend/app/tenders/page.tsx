"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { FileText, Plus, ArrowRight, Building, Search, Layers } from "lucide-react";
import { api } from "@/lib/api";
import { Tender } from "@/types";

export default function TendersPage() {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form State
  const [tenderNumber, setTenderNumber] = useState("");
  const [title, setTitle] = useState("");
  const [org, setOrg] = useState("Ministry of Electronics & IT");
  const [value, setValue] = useState("");

  useEffect(() => {
    loadTenders();
  }, []);

  async function loadTenders() {
    try {
      const data = await api.getTenders();
      setTenders(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTender(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.createTender({
        tender_number: tenderNumber,
        title,
        procuring_organization: org,
        estimated_value: parseFloat(value) || 5000000,
        currency: "INR"
      });
      setShowCreateModal(false);
      setTenderNumber("");
      setTitle("");
      setValue("");
      loadTenders();
    } catch (err: any) {
      alert(err.message || "Failed to create tender");
    }
  }

  const filtered = tenders.filter(
    (t) =>
      t.tender_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.procuring_organization.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Procurement Tenders & Solicitations
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage tenders, versioned specifications, deterministic rule requirements, and submitted vendor bids.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-lg text-xs transition shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Publish New Tender</span>
        </button>
      </div>

      {/* Search Filter */}
      <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
        <Search className="w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Filter by tender number, title, or ministry..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="bg-transparent border-none outline-none w-full text-xs text-slate-800 placeholder:text-slate-400"
        />
      </div>

      {/* Tenders Grid */}
      <div className="grid grid-cols-1 gap-4">
        {filtered.length === 0 ? (
          <div className="bg-white p-12 text-center rounded-xl border border-slate-200 text-slate-400 text-xs">
            No tenders match your search query.
          </div>
        ) : (
          filtered.map((tender) => (
            <div
              key={tender.id}
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-blue-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 max-w-2xl">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                    {tender.tender_number}
                  </span>
                  <span className="bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded">
                    {tender.status}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 leading-snug">
                  {tender.title}
                </h3>
                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Building className="w-3.5 h-3.5 text-slate-400" />
                    {tender.procuring_organization}
                  </span>
                  <span>•</span>
                  <span>
                    Est. Value: <strong className="text-slate-800">₹{tender.estimated_value ? (tender.estimated_value / 100000).toFixed(2) : 0} Lakhs</strong>
                  </span>
                  <span>•</span>
                  <span>Requirements: <strong className="text-slate-800">{tender.requirements_count ?? 7} Rules</strong></span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Link
                  href={`/tenders/${tender.id}`}
                  className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-bold px-4 py-2 rounded-lg text-xs transition shadow-sm"
                >
                  <span>Open Tender Console</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 border border-slate-200">
            <h2 className="text-lg font-extrabold text-slate-900">Publish New GeM Tender</h2>
            <form onSubmit={handleCreateTender} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Tender Number</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. GEM/2026/B/90123"
                  value={tenderNumber}
                  onChange={(e) => setTenderNumber(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg outline-none focus:border-blue-600"
                />
              </div>
              <div>
                <label className="font-bold text-slate-700 block mb-1">Tender Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Supply of 500 Network Switches"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg outline-none focus:border-blue-600"
                />
              </div>
              <div>
                <label className="font-bold text-slate-700 block mb-1">Procuring Organization / Ministry</label>
                <input
                  type="text"
                  required
                  value={org}
                  onChange={(e) => setOrg(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg outline-none focus:border-blue-600"
                />
              </div>
              <div>
                <label className="font-bold text-slate-700 block mb-1">Estimated Value (INR)</label>
                <input
                  type="number"
                  placeholder="e.g. 5000000"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg outline-none focus:border-blue-600"
                />
              </div>

              <div className="pt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold"
                >
                  Publish Tender
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
