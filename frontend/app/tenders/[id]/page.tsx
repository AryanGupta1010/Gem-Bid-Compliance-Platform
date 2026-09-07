"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  Building, 
  FileText, 
  Layers, 
  Users, 
  ShieldCheck, 
  History, 
  Plus, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle,
  Hash,
  Download
} from "lucide-react";
import { api } from "@/lib/api";
import { Tender, Bid, Requirement } from "@/types";
import { StatusBadge } from "@/components/StatusBadge";
import { RiskBadge } from "@/components/RiskBadge";

export default function TenderDetailPage() {
  const params = useParams();
  const tenderId = params?.id as string;

  const [tender, setTender] = useState<Tender | null>(null);
  const [bids, setBids] = useState<Bid[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [auditEvents, setAuditEvents] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "requirements" | "bidders" | "documents" | "audit">("bidders");
  const [loading, setLoading] = useState(true);

  // Add Requirement Modal State
  const [showAddReq, setShowAddReq] = useState(false);
  const [reqName, setReqName] = useState("");
  const [ruleType, setRuleType] = useState("NUMERIC");
  const [operator, setOperator] = useState("GTE");
  const [expectedVal, setExpectedVal] = useState("");
  const [unit, setUnit] = useState("Cr");
  const [severity, setSeverity] = useState("HIGH");
  const [mandatory, setMandatory] = useState(true);

  useEffect(() => {
    if (!tenderId) return;
    loadTenderData();
  }, [tenderId]);

  async function loadTenderData() {
    try {
      const [tData, bData, aData] = await Promise.all([
        api.getTender(tenderId),
        api.getBids(tenderId),
        api.getAllAudit(50).catch(() => []),
      ]);
      setTender(tData);
      setRequirements(tData.requirements || []);
      setBids(bData);
      setAuditEvents(aData);
    } catch (err) {
      console.error("Error loading tender data", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateRequirement(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.createRequirement(tenderId, {
        name: reqName,
        rule_type: ruleType,
        operator,
        expected_value: expectedVal,
        unit,
        severity,
        mandatory,
        enabled: true,
        weight: severity === "CRITICAL" ? 30 : severity === "HIGH" ? 20 : 10
      });
      setShowAddReq(false);
      setReqName("");
      setExpectedVal("");
      loadTenderData();
    } catch (err: any) {
      alert(err.message || "Failed to add requirement");
    }
  }

  if (loading || !tender) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] text-slate-500 text-xs">
        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2" />
        Loading Tender Console...
      </div>
    );
  }

  const tabs = [
    { id: "bidders", label: `Submitted Bids (${bids.length})`, icon: Users },
    { id: "requirements", label: `Deterministic Rules (${requirements.length})`, icon: ShieldCheck },
    { id: "overview", label: "Tender Overview", icon: FileText },
    { id: "audit", label: "Audit Log", icon: History },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-extrabold text-blue-800 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded">
                {tender.tender_number}
              </span>
              <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold px-2 py-0.5 rounded">
                {tender.status}
              </span>
              <span className="bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded">
                Version 1.0 (Locked)
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              {tender.title}
            </h1>
            <p className="text-xs text-slate-500 flex items-center gap-2">
              <Building className="w-3.5 h-3.5 text-slate-400" />
              <span>{tender.procuring_organization}</span>
              <span>•</span>
              <span>Est. Value: <strong>₹{(tender.estimated_value ? tender.estimated_value / 100000 : 85).toFixed(2)} Lakhs</strong></span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddReq(true)}
              className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold px-3.5 py-2 rounded-lg text-xs transition shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Rule Clause</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 gap-6 pt-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`pb-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                  isActive
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab 1: Submitted Bids */}
      {activeTab === "bidders" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Participating Bidder Packages</h2>
              <p className="text-xs text-slate-500">
                Click any bidder to open the evaluation console, inspect rule arithmetic, verify evidence, and submit officer decisions.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {bids.map((bid) => {
              const assessment = bid.compliance_assessment;
              return (
                <div
                  key={bid.id}
                  className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-blue-400 transition-all flex flex-col lg:flex-row lg:items-center justify-between gap-5"
                >
                  <div className="space-y-2 max-w-xl">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-500">{bid.bid_number}</span>
                      <span className="bg-slate-100 text-slate-700 text-[10px] font-semibold px-2 py-0.5 rounded">
                        Reg: {bid.bidder?.registration_number}
                      </span>
                      {bid.bidder?.is_msme && (
                        <span className="bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-bold px-2 py-0.5 rounded">
                          MSME Verified
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-bold text-slate-900">
                      {bid.bidder?.name}
                    </h3>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                      <span>GSTIN: <strong className="text-slate-700">{bid.bidder?.gstin || "N/A"}</strong></span>
                      <span>•</span>
                      <span>Quoted Bid: <strong className="text-slate-700">₹{(bid.bid_amount ? bid.bid_amount / 100000 : 80).toFixed(2)} L</strong></span>
                      <span>•</span>
                      <span>Submitted Documents: <strong className="text-slate-700">{bid.documents?.length || 4} Files</strong></span>
                    </div>
                  </div>

                  {/* Compliance Summary & Jump */}
                  <div className="flex flex-wrap items-center gap-6 pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-100">
                    <div className="text-center">
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Score</span>
                      <span className="text-xl font-extrabold text-slate-900">
                        {assessment?.compliance_score ?? 0}%
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Risk</span>
                      {assessment && <RiskBadge level={assessment.risk_level} size="sm" />}
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Recommendation</span>
                      {assessment && <StatusBadge status={assessment.recommendation} size="sm" />}
                    </div>

                    <Link
                      href={`/bids/${bid.id}`}
                      className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-lg text-xs transition shadow-sm"
                    >
                      <span>Open Evaluation</span>
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 2: Deterministic Requirements */}
      {activeTab === "requirements" && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-800 text-xs uppercase tracking-wider">
                Configured Deterministic Rules (Total: {requirements.length})
              </h3>
              <p className="text-[11px] text-slate-500">These rules are evaluated deterministically with strict arithmetic and adapter checks.</p>
            </div>
          </div>
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
                <th className="py-3 px-4">#</th>
                <th className="py-3 px-4">Requirement Clause</th>
                <th className="py-3 px-4">Rule Type</th>
                <th className="py-3 px-4">Operator</th>
                <th className="py-3 px-4">Expected Value</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Mandatory</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {requirements.map((req, idx) => (
                <tr key={req.id} className="hover:bg-slate-50/80 transition">
                  <td className="py-3 px-4 font-bold text-slate-400">{idx + 1}</td>
                  <td className="py-3 px-4">
                    <div className="font-bold text-slate-900">{req.name}</div>
                    <div className="text-[11px] text-slate-500 line-clamp-1">{req.description}</div>
                  </td>
                  <td className="py-3 px-4 font-mono font-semibold text-slate-700">{req.rule_type}</td>
                  <td className="py-3 px-4 font-mono text-blue-700 font-bold">{req.operator}</td>
                  <td className="py-3 px-4 font-semibold text-slate-800">
                    {req.expected_value} {req.unit || ""}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      req.severity === "CRITICAL" ? "bg-rose-100 text-rose-800" :
                      req.severity === "HIGH" ? "bg-orange-100 text-orange-800" : "bg-blue-100 text-blue-800"
                    }`}>
                      {req.severity} ({req.weight} pts)
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold text-emerald-700">
                    {req.mandatory ? "YES" : "NO"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Overview */}
      {activeTab === "overview" && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 text-xs">
          <h3 className="text-sm font-bold text-slate-900">Tender Scope & Specification</h3>
          <p className="text-slate-600 leading-relaxed">
            {tender.description}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-slate-100">
            <div>
              <span className="text-slate-400 block">Currency</span>
              <span className="font-bold text-slate-800">{tender.currency}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Published Date</span>
              <span className="font-bold text-slate-800">{new Date(tender.created_at).toLocaleDateString()}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Evaluation Mode</span>
              <span className="font-bold text-emerald-700">Hybrid AI / Deterministic</span>
            </div>
            <div>
              <span className="text-slate-400 block">Human Authority</span>
              <span className="font-bold text-blue-700">Procurement Officer</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Audit */}
      {activeTab === "audit" && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
          <h3 className="text-sm font-bold text-slate-900">Tender Audit Trail</h3>
          <div className="space-y-3">
            {auditEvents.slice(0, 10).map((ev) => (
              <div key={ev.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs flex items-center justify-between">
                <div>
                  <span className="font-mono font-bold text-blue-700 mr-2">{ev.action}</span>
                  <span className="text-slate-600">by {ev.user_name || "System"}</span>
                </div>
                <span className="text-slate-400 text-[11px]">{new Date(ev.timestamp).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Requirement Modal */}
      {showAddReq && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 border border-slate-200 text-xs">
            <h2 className="text-lg font-extrabold text-slate-900">Add Deterministic Rule Clause</h2>
            <form onSubmit={handleCreateRequirement} className="space-y-3">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Clause Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Minimum Average Turnover"
                  value={reqName}
                  onChange={(e) => setReqName(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg outline-none focus:border-blue-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Rule Type</label>
                  <select
                    value={ruleType}
                    onChange={(e) => setRuleType(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg outline-none bg-white"
                  >
                    <option value="NUMERIC">NUMERIC</option>
                    <option value="DATE">DATE</option>
                    <option value="VERIFICATION">VERIFICATION</option>
                    <option value="DOCUMENT_PRESENT">DOCUMENT_PRESENT</option>
                    <option value="STATUS">STATUS</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Operator</label>
                  <select
                    value={operator}
                    onChange={(e) => setOperator(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg outline-none bg-white"
                  >
                    <option value="GTE">&gt;= (GTE)</option>
                    <option value="GT">&gt; (GT)</option>
                    <option value="EQ">== (EQ)</option>
                    <option value="LTE">&lt;= (LTE)</option>
                    <option value="EXISTS">EXISTS</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Expected Threshold / Value</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 10"
                    value={expectedVal}
                    onChange={(e) => setExpectedVal(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg outline-none focus:border-blue-600"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Unit (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Cr, %, Years"
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Severity</label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg outline-none bg-white"
                  >
                    <option value="CRITICAL">CRITICAL (30 pts)</option>
                    <option value="HIGH">HIGH (20 pts)</option>
                    <option value="MEDIUM">MEDIUM (10 pts)</option>
                    <option value="LOW">LOW (5 pts)</option>
                  </select>
                </div>

                <div className="flex items-center pt-5">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={mandatory}
                      onChange={(e) => setMandatory(e.target.checked)}
                      className="rounded text-blue-600 w-4 h-4"
                    />
                    <span className="font-bold text-slate-800">Mandatory Clause</span>
                  </label>
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddReq(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold"
                >
                  Save Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
