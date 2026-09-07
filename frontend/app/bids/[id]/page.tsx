"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  Building, 
  ArrowLeft, 
  ShieldCheck, 
  ShieldAlert, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  RotateCw, 
  ExternalLink,
  Info,
  Check,
  X,
  MessageSquare,
  Crosshair,
  UserCheck
} from "lucide-react";
import { api } from "@/lib/api";
import { Bid, RuleResult, RuleStatus, ReviewDecision } from "@/types";
import { StatusBadge } from "@/components/StatusBadge";
import { RiskBadge } from "@/components/RiskBadge";
import { EvidenceBoxViewer } from "@/components/EvidenceBoxViewer";

export default function BidEvaluationPage() {
  const params = useParams();
  const bidId = params?.id as string;

  const [bid, setBid] = useState<Bid | null>(null);
  const [ruleResults, setRuleResults] = useState<RuleResult[]>([]);
  const [selectedRule, setSelectedRule] = useState<RuleResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);

  // Officer Review Form State
  const [officerNotes, setOfficerNotes] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewSuccessMessage, setReviewSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!bidId) return;
    loadBidData();
  }, [bidId]);

  async function loadBidData() {
    try {
      const [bidData, rulesData] = await Promise.all([
        api.getBid(bidId),
        api.getBidRules(bidId).catch(() => []),
      ]);
      setBid(bidData);
      setRuleResults(rulesData);
      if (rulesData.length > 0 && !selectedRule) {
        setSelectedRule(rulesData[0]);
      }
    } catch (err) {
      console.error("Failed to load bid evaluation data", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleReEvaluate() {
    setEvaluating(true);
    try {
      await api.verifyBid(bidId);
      await loadBidData();
    } catch (err: any) {
      alert(err.message || "Failed to trigger re-evaluation");
    } finally {
      setEvaluating(false);
    }
  }

  async function handleOfficerDecision(decisionType: "APPROVED" | "REJECTED" | "NEEDS_REVIEW") {
    if (!officerNotes.trim()) {
      alert("Please provide officer justification notes before submitting your decision.");
      return;
    }

    setReviewSubmitting(true);
    try {
      await api.submitReview(bidId, {
        decision: decisionType,
        officer_notes: officerNotes,
      });
      setReviewSuccessMessage(`Officer decision '${decisionType}' recorded successfully in the audit trail.`);
      setOfficerNotes("");
      await loadBidData();
      setTimeout(() => setReviewSuccessMessage(null), 5000);
    } catch (err: any) {
      alert(err.message || "Failed to submit officer decision");
    } finally {
      setReviewSubmitting(false);
    }
  }

  if (loading || !bid) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] text-xs text-slate-500">
        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2" />
        Loading Bid Evaluation Console...
      </div>
    );
  }

  const assessment = bid.compliance_assessment;
  const score = assessment?.compliance_score ?? 0;
  const recommendation = assessment?.recommendation ?? "REVIEW";
  const riskLevel = assessment?.risk_level ?? "MEDIUM";

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between">
        <Link
          href={`/tenders/${bid.tender_id}`}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-blue-600 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Tender Bidders Console</span>
        </Link>

        <button
          onClick={handleReEvaluate}
          disabled={evaluating}
          className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-bold px-3.5 py-1.5 rounded-lg text-xs transition shadow-sm"
        >
          <RotateCw className={`w-3.5 h-3.5 ${evaluating ? "animate-spin" : ""}`} />
          <span>{evaluating ? "Re-Evaluating Pipeline..." : "Re-Run Verification"}</span>
        </button>
      </div>

      {/* Hero Banner: Bidder Summary + Score Gauge + Risk + Recommendation */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Bidder Identification (Cols 1-6) */}
          <div className="lg:col-span-6 space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                {bid.bid_number}
              </span>
              <span className="bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-bold px-2 py-0.5 rounded">
                Reg: {bid.bidder?.registration_number}
              </span>
              {bid.bidder?.is_msme && (
                <span className="bg-purple-50 text-purple-700 text-[10px] font-bold px-2 py-0.5 rounded">
                  MSME Verified
                </span>
              )}
            </div>

            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              {bid.bidder?.name}
            </h1>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 text-xs text-slate-500">
              <div>
                <span className="text-[10px] text-slate-400 block">GSTIN</span>
                <span className="font-mono font-bold text-slate-800">{bid.bidder?.gstin || "N/A"}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">PAN</span>
                <span className="font-mono font-bold text-slate-800">{bid.bidder?.pan || "N/A"}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Quoted Value</span>
                <span className="font-bold text-slate-800">₹{(bid.bid_amount ? bid.bid_amount / 100000 : 80).toFixed(2)} Lakhs</span>
              </div>
            </div>
          </div>

          {/* Score & Automated Recommendation Gauge (Cols 7-12) */}
          <div className="lg:col-span-6 grid grid-cols-3 gap-3 p-4 bg-slate-50 border border-slate-200 rounded-xl">
            {/* Score */}
            <div className="text-center p-2 bg-white rounded-lg border border-slate-200 shadow-sm flex flex-col justify-center items-center">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Compliance Score</span>
              <div className="text-3xl font-black text-slate-900 mt-0.5">
                {score}%
              </div>
              <span className="text-[10px] text-slate-500 font-medium">Weighted Severity</span>
            </div>

            {/* Risk */}
            <div className="text-center p-2 bg-white rounded-lg border border-slate-200 shadow-sm flex flex-col justify-center items-center">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Risk Classification</span>
              <RiskBadge level={riskLevel} size="md" />
              <span className="text-[10px] text-slate-500 mt-1">Deterministic</span>
            </div>

            {/* Recommendation */}
            <div className="text-center p-2 bg-white rounded-lg border border-slate-200 shadow-sm flex flex-col justify-center items-center">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">System Recommendation</span>
              <StatusBadge status={recommendation} size="md" />
              <span className="text-[10px] text-slate-500 mt-1">Non-Autonomous</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Left = Requirements Table, Right = Result Detail & Evidence Flyout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Requirements Grid (Cols 1-7) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Deterministic Rule Evaluations ({ruleResults.length})
              </h2>
              <p className="text-[11px] text-slate-500">
                Click any row to inspect exact arithmetic evaluation and document evidence coordinates.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
                  <th className="py-3 px-4">Requirement Clause</th>
                  <th className="py-3 px-4">Expected</th>
                  <th className="py-3 px-4">Actual</th>
                  <th className="py-3 px-4 text-center">Result</th>
                  <th className="py-3 px-4 text-center">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {ruleResults.map((res) => {
                  const isSelected = selectedRule?.id === res.id;
                  return (
                    <tr
                      key={res.id}
                      onClick={() => setSelectedRule(res)}
                      className={`cursor-pointer transition-all ${
                        isSelected 
                          ? "bg-blue-50/90 font-medium ring-1 ring-blue-500 inset-0" 
                          : "hover:bg-slate-50/80"
                      }`}
                    >
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">{res.requirement_name || "Clause"}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{res.rule_type}</div>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700">
                        {res.expected_value} {res.unit || ""}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        {res.actual_value || "Missing"}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <StatusBadge status={res.status} size="sm" />
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          res.severity === "CRITICAL" ? "bg-rose-100 text-rose-800" :
                          res.severity === "HIGH" ? "bg-orange-100 text-orange-800" : "bg-blue-100 text-blue-800"
                        }`}>
                          {res.severity}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Result Detail & Evidence Panel (Cols 8-12) */}
        <div className="lg:col-span-5 space-y-4">
          {selectedRule ? (
            <div className="bg-white rounded-2xl border-2 border-blue-500/80 p-5 shadow-md space-y-4">
              <div className="flex items-start justify-between border-b border-slate-200 pb-3">
                <div>
                  <span className="text-[10px] font-mono text-blue-700 font-bold uppercase">
                    Evaluation Breakdown
                  </span>
                  <h3 className="text-base font-extrabold text-slate-900 mt-0.5">
                    {selectedRule.requirement_name}
                  </h3>
                </div>
                <StatusBadge status={selectedRule.status} size="md" />
              </div>

              {/* Arithmetic & Rule Logic Step */}
              <div className="bg-slate-900 text-slate-200 p-3.5 rounded-xl text-xs space-y-2 font-mono">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Deterministic Rule Formulation</div>
                <div className="text-emerald-400 font-bold text-xs">
                  {selectedRule.explanation}
                </div>
                <div className="pt-2 border-t border-slate-800 grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                  <div>
                    <span className="text-slate-500 block">Required Threshold:</span>
                    <span>{selectedRule.expected_value} {selectedRule.unit || ""}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Detected Value:</span>
                    <span className="font-bold text-white">{selectedRule.actual_value}</span>
                  </div>
                </div>
              </div>

              {/* Evidence Viewer with Visual Box */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-blue-600" />
                  <span>Document Evidence Grounding</span>
                </h4>
                {selectedRule.evidences && selectedRule.evidences.length > 0 ? (
                  <EvidenceBoxViewer
                    evidence={selectedRule.evidences[0]}
                    documentName="Registered_Bidder_Document.pdf"
                    extractedValue={selectedRule.actual_value || ""}
                  />
                ) : (
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500 text-center">
                    No physical document extract mapped for this clause (Evaluated via external API adapter or direct metadata).
                  </div>
                )}
              </div>

              {/* Verification Adapter Info */}
              {selectedRule.verification_result && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between font-bold text-blue-900 text-[11px]">
                    <span>External Verification Adapter: {selectedRule.verification_result.source}</span>
                    <span className="text-emerald-700 uppercase">{selectedRule.verification_result.status}</span>
                  </div>
                  <div className="text-[11px] text-blue-800 font-mono">
                    Query Identifier: {selectedRule.verification_result.request_identifier}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-xs text-slate-400">
              Select a rule from the table to inspect details.
            </div>
          )}
        </div>
      </div>

      {/* Human Procurement Officer Final Decision Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
          <UserCheck className="w-5 h-5 text-blue-600" />
          <div>
            <h2 className="text-base font-extrabold text-slate-900">Procurement Officer Final Decision Console</h2>
            <p className="text-xs text-slate-500">
              The AI/Rule engine acts strictly as decision support. The authorized Procurement Officer provides the binding human decision.
            </p>
          </div>
        </div>

        {reviewSuccessMessage && (
          <div className="p-3 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded-xl text-xs font-bold flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-600" />
            <span>{reviewSuccessMessage}</span>
          </div>
        )}

        <div className="space-y-3">
          <label className="block text-xs font-bold text-slate-800">
            Officer Justification Notes & Recommendation Override Rationale (Mandatory)
          </label>
          <textarea
            rows={3}
            value={officerNotes}
            onChange={(e) => setOfficerNotes(e.target.value)}
            placeholder="Record formal procurement notes (e.g. All technical clauses confirmed against tender specifications, recommending financial evaluation opening...)"
            className="w-full p-3 border border-slate-300 rounded-xl text-xs outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
          />

          <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
            <button
              type="button"
              disabled={reviewSubmitting}
              onClick={() => handleOfficerDecision("NEEDS_REVIEW")}
              className="inline-flex items-center gap-1.5 bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 font-bold px-4 py-2.5 rounded-lg text-xs transition"
            >
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Mark For Further Committee Review</span>
            </button>

            <button
              type="button"
              disabled={reviewSubmitting}
              onClick={() => handleOfficerDecision("REJECTED")}
              className="inline-flex items-center gap-1.5 bg-rose-600 hover:bg-rose-700 text-white font-bold px-4 py-2.5 rounded-lg text-xs transition shadow-sm"
            >
              <X className="w-4 h-4" />
              <span>Disqualify / Reject Bid</span>
            </button>

            <button
              type="button"
              disabled={reviewSubmitting}
              onClick={() => handleOfficerDecision("APPROVED")}
              className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-5 py-2.5 rounded-lg text-xs transition shadow-sm"
            >
              <Check className="w-4 h-4" />
              <span>Formally Approve Technical Bid</span>
            </button>
          </div>
        </div>

        {/* Existing Decisions Timeline */}
        {bid.review_decisions && bid.review_decisions.length > 0 && (
          <div className="pt-4 border-t border-slate-100 space-y-2">
            <h4 className="text-xs font-bold text-slate-700 uppercase">Recorded Officer Decisions History</h4>
            <div className="space-y-2">
              {bid.review_decisions.map((dec) => (
                <div key={dec.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
                  <div className="flex items-center justify-between font-bold">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${
                      dec.decision === "APPROVED" ? "bg-emerald-100 text-emerald-800" :
                      dec.decision === "REJECTED" ? "bg-rose-100 text-rose-800" : "bg-amber-100 text-amber-800"
                    }`}>
                      {dec.decision}
                    </span>
                    <span className="text-slate-400 text-[11px]">{new Date(dec.reviewed_at).toLocaleString()}</span>
                  </div>
                  <p className="text-slate-700 font-medium">{dec.officer_notes}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
