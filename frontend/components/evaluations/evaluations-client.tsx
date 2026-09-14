"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Search, Download } from "lucide-react";
import { RiskBadge, StatusBadge } from "@/components/ui/status-badge";
import { Bidder, Tender } from "@/lib/types";
import { exportToCSV } from "@/lib/export";

interface EvaluationsClientProps {
  bidders: Bidder[];
  tenderTitle: string;
}

export function EvaluationsClient({ bidders, tenderTitle }: EvaluationsClientProps) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");

  const filteredBids = bidders.filter(bid => {
    const matchesSearch = bid.bidder_name.toLowerCase().includes(search.toLowerCase()) || 
                          bid.id.toLowerCase().includes(search.toLowerCase()) || bid.tender_id.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || bid.status === statusFilter;
    const matchesRisk = riskFilter === "ALL" || bid.risk === riskFilter;
    
    return matchesSearch && matchesStatus && matchesRisk;
  });

  const handleExport = () => {
    const data = filteredBids.map(b => ({
      ID: b.id,
      BidderName: b.bidder_name,
      Status: b.status,
      Risk: b.risk,
      Score: b.score,
      FailedRules: b.failed_rules,
      ReviewRules: b.review_rules,
      Summary: b.summary
    }));
    exportToCSV("evaluations_report.csv", data);
  };

  return (
    <div className="mt-6 panel overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-line p-5 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="section-title">Evaluation queue</p>
          <h2 className="mt-1 text-lg font-semibold">{tenderTitle}</h2>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <select 
            className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:border-teal"
            aria-label="Filter by evaluation result"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Status</option>
            <option value="PASS">Pass</option>
            <option value="REVIEW">Review</option>
            <option value="FAIL">Fail</option>
          </select>

          <select 
            className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:border-teal"
            aria-label="Filter by risk"
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
          >
            <option value="ALL">All Risks</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
          
          <div className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm text-slate-500 focus-within:border-teal">
            <Search size={15} />
            <input 
              type="text" 
              placeholder="Search bidders"
              aria-label="Search bidders"
              className="bg-transparent focus:outline-none"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          
          <button onClick={handleExport} className="btn bg-white border border-line hover:bg-slate-50">
            <Download size={16} /> Export
          </button>
        </div>
      </div>

      <div className="divide-y divide-line">
        {filteredBids.map((bidder) => (
          <Link
            key={bidder.id}
            href={`/evaluations/${bidder.id}`}
            className="block p-5 transition hover:bg-slate-50"
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-base font-semibold">{bidder.bidder_name}</h3>
                  <span className="text-xs muted">{bidder.tender_id}</span>
                  <RiskBadge risk={bidder.risk} />
                  <StatusBadge status={bidder.status} />
                </div>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{bidder.summary}</p>
              </div>
              <div className="grid shrink-0 grid-cols-3 gap-6 text-center">
                <div>
                  <p className="text-2xl font-semibold">{bidder.score}</p>
                  <p className="text-[10px] uppercase tracking-wide text-slate-500">Score</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold text-red-600">{bidder.failed_rules}</p>
                  <p className="text-[10px] uppercase tracking-wide text-slate-500">Failed</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold text-amber-600">{bidder.review_rules}</p>
                  <p className="text-[10px] uppercase tracking-wide text-slate-500">Review</p>
                </div>
              </div>
              <ArrowRight className="hidden text-slate-400 lg:block" size={18} />
            </div>
          </Link>
        ))}
        {filteredBids.length === 0 && (
            <div className="p-10 text-center text-slate-500">No bidders match your filters.</div>
        )}
      </div>
    </div>
  );
}
