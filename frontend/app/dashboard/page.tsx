"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  FileText, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ShieldAlert, 
  TrendingUp, 
  ArrowRight, 
  Building, 
  Layers,
  Sparkles,
  ExternalLink
} from "lucide-react";
import { api } from "@/lib/api";
import { Tender, Bid } from "@/types";
import { StatusBadge } from "@/components/StatusBadge";
import { RiskBadge } from "@/components/RiskBadge";

export default function DashboardPage() {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [bids, setBids] = useState<Bid[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [tendersData, bidsData] = await Promise.all([
          api.getTenders().catch(() => []),
          api.getBids().catch(() => []),
        ]);
        setTenders(tendersData);
        setBids(bidsData);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Compute Metrics
  const activeTendersCount = tenders.length;
  const bidsUnderEvaluationCount = bids.length;
  const passedBids = bids.filter(b => b.compliance_assessment?.recommendation === "PASS").length;
  const failedBids = bids.filter(b => b.compliance_assessment?.recommendation === "FAIL").length;
  const reviewBids = bids.filter(b => b.compliance_assessment?.recommendation === "REVIEW").length;
  const highRiskBids = bids.filter(b => b.compliance_assessment?.risk_level === "HIGH" || b.compliance_assessment?.risk_level === "CRITICAL").length;

  const avgScore = bids.length > 0 
    ? Math.round(bids.reduce((acc, b) => acc + (b.compliance_assessment?.compliance_score || 0), 0) / bids.length)
    : 82;

  return (
    <div className="space-y-8">
      {/* Top Banner / Welcome */}
      <div className="bg-gradient-to-r from-gem-navy via-blue-900 to-indigo-950 text-white p-6 sm:p-8 rounded-2xl shadow-lg border border-blue-900 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 bg-amber-500/20 text-amber-300 border border-amber-500/30 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            Decision Support & Verification Hub
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            GeM Bid Compliance Verification Platform
          </h1>
          <p className="text-sm text-blue-200 leading-relaxed">
            Deterministic rule validation, external government adapter verification (GST, Udyam, Debarment), and explainable risk analysis for government procurement officers.
          </p>
          <div className="pt-2 flex flex-wrap items-center gap-3">
            {tenders.length > 0 && (
              <Link
                href={`/tenders/${tenders[0].id}`}
                className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-4 py-2 rounded-lg text-xs transition shadow"
              >
                <span>Launch Demo Tender Evaluation</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            )}
            <Link
              href="/audit"
              className="inline-flex items-center gap-2 bg-blue-800/80 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg text-xs transition border border-blue-600/50"
            >
              <span>View Audit Trail</span>
            </Link>
          </div>
        </div>

        {/* Decorative background badge */}
        <div className="absolute right-4 -bottom-10 opacity-10 pointer-events-none">
          <Building className="w-80 h-80 text-white" />
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1 */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Tenders</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{activeTendersCount}</h3>
            <p className="text-[11px] text-blue-600 mt-1 flex items-center gap-1 font-medium">
              <Layers className="w-3 h-3" />
              <span>Under Evaluation</span>
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Bids Evaluated</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{bidsUnderEvaluationCount}</h3>
            <div className="flex items-center gap-2 mt-1 text-[11px]">
              <span className="text-emerald-700 font-bold">{passedBids} PASS</span>
              <span className="text-slate-300">•</span>
              <span className="text-rose-700 font-bold">{failedBids} FAIL</span>
            </div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Needs Review</p>
            <h3 className="text-2xl font-bold text-amber-700 mt-1">{reviewBids}</h3>
            <p className="text-[11px] text-amber-700 mt-1 font-medium">
              Officer Discretion Required
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Avg Compliance Score</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{avgScore}%</h3>
            <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1 font-medium">
              <TrendingUp className="w-3 h-3 text-emerald-600" />
              <span>Weighted Severity Model</span>
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* High Risk Alert Banner */}
      {highRiskBids > 0 && (
        <div className="bg-rose-50 border-l-4 border-rose-600 p-4 rounded-r-xl shadow-sm flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-rose-900">
              High Risk / Non-Compliant Bids Flagged ({highRiskBids})
            </h4>
            <p className="text-xs text-rose-800 mt-0.5 leading-relaxed">
              Deterministic rule violations detected (e.g. Turnover threshold failures or external verification unavailability). The system has placed these bids on strict recommendation review.
            </p>
          </div>
        </div>
      )}

      {/* Main Section: Recent Tenders & Bids */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Procurement Tenders Under Evaluation</h2>
            <p className="text-xs text-slate-500">Select a tender to inspect bidders, requirement rules, and evidence verification.</p>
          </div>
          <Link
            href="/tenders"
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <span>View All Tenders</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Tender Number</th>
                  <th className="py-3 px-4">Title & Organization</th>
                  <th className="py-3 px-4">Estimated Value</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-center">Bidders</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {tenders.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No tenders found. Please run seed script or create a tender.
                    </td>
                  </tr>
                ) : (
                  tenders.map((tender) => (
                    <tr key={tender.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                        {tender.tender_number}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-800 line-clamp-1">{tender.title}</div>
                        <div className="text-[11px] text-slate-500">{tender.procuring_organization}</div>
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-700">
                        {tender.estimated_value 
                          ? `₹${(tender.estimated_value / 100000).toFixed(2)} Lakhs` 
                          : "N/A"}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded text-[10px] font-bold">
                          {tender.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="bg-slate-100 text-slate-800 font-bold px-2 py-1 rounded text-xs">
                          {tender.bids_count ?? 3} Bids
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/tenders/${tender.id}`}
                          className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg font-bold text-[11px] transition shadow-sm"
                        >
                          <span>Evaluate Bids</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 3 Benchmark Bidders Preview */}
      {bids.length > 0 && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Quick Bidder Verification Benchmark</h2>
            <p className="text-xs text-slate-500">Live evaluation outcomes for the 3 test scenario bidders</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {bids.map((bid) => {
              const assessment = bid.compliance_assessment;
              const isPass = assessment?.recommendation === "PASS";
              const isFail = assessment?.recommendation === "FAIL";
              const isReview = assessment?.recommendation === "REVIEW";

              return (
                <div 
                  key={bid.id} 
                  className={`bg-white rounded-xl border p-5 shadow-sm space-y-3 transition-all hover:shadow-md ${
                    isPass ? "border-emerald-200" : isFail ? "border-rose-200" : "border-amber-200"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-mono text-[10px] text-slate-400 font-bold">{bid.bid_number}</span>
                      <h3 className="text-sm font-bold text-slate-900 mt-0.5 line-clamp-1">
                        {bid.bidder?.name || "Bidder"}
                      </h3>
                    </div>
                    {assessment && <StatusBadge status={assessment.recommendation} size="sm" />}
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs">
                    <div>
                      <span className="text-slate-400 text-[10px] block">Compliance Score</span>
                      <span className="font-extrabold text-base text-slate-800">
                        {assessment?.compliance_score ?? 0}%
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Risk Level</span>
                      {assessment && <RiskBadge level={assessment.risk_level} size="sm" />}
                    </div>
                  </div>

                  <div className="pt-2">
                    <Link
                      href={`/bids/${bid.id}`}
                      className="w-full flex items-center justify-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white font-bold py-2 rounded-lg text-xs transition"
                    >
                      <span>Inspect Rules & Evidence</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
