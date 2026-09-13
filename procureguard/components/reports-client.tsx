"use client";

import { Download, FileText, ShieldCheck, BarChart3 } from "lucide-react";
import { MetricCard } from "@/components/ui";
import { exportToCSV } from "@/lib/export";
import { Bidder, AuditEvent } from "@/lib/types";

interface ReportsClientProps {
  bids: Bidder[];
  auditTrail: AuditEvent[];
}

export function ReportsClient({ bids, auditTrail }: ReportsClientProps) {
  
  const handleExportBids = () => {
    const data = bids.map(b => ({
      ID: b.id,
      TenderID: b.tender_id,
      BidderName: b.bidder_name,
      Status: b.status,
      Risk: b.risk,
      Score: b.score,
      FailedRules: b.failed_rules,
      ReviewRules: b.review_rules
    }));
    exportToCSV("bid_compliance_summary.csv", data);
  };

  const handleExportAudit = () => {
    const data = auditTrail.map(a => ({
      ID: a.id,
      Time: a.time,
      Actor: a.actor,
      Action: a.action,
      Document: a.document || "",
      Rule: a.rule || "",
      Result: a.result || "",
      Source: a.source || "",
      Hash: a.hash || ""
    }));
    exportToCSV("audit_event_export.csv", data);
  };

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Available reports" value="4" detail="Active tender workspace" icon={FileText} />
        <MetricCard label="Evidence records" value={bids.reduce((acc, b) => acc + (b.documents?.length || 0), 0).toString()} detail="Linked to rule outcomes" icon={ShieldCheck} tone="teal" />
        <MetricCard label="Audit events" value={auditTrail.length.toString()} detail="Hash-backed activity" icon={FileText} tone="teal" />
        <MetricCard label="Benchmark status" value="Ready" detail="Offline golden pack" icon={BarChart3} tone="amber" />
      </div>

      <div className="mt-6 panel overflow-hidden">
        <div className="border-b border-line p-5">
          <p className="section-title">Report center</p>
          <h2 className="mt-1 text-lg font-semibold">Golden demo tender exports</h2>
        </div>
        <div className="divide-y divide-line">
          
          <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-semibold">Bid compliance summary</h3>
              <p className="mt-1 text-sm muted">Rule-level PASS, FAIL and REVIEW outcomes for all bidders.</p>
            </div>
            <button onClick={handleExportBids} className="btn btn-secondary shrink-0">
              <Download size={15} />
              Export CSV
            </button>
          </div>

          <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-semibold">Evidence lineage report</h3>
              <p className="mt-1 text-sm muted">Documents, pages, extracted values, sources and model versions.</p>
            </div>
            <button onClick={() => alert("PDF export coming soon!")} className="btn btn-secondary shrink-0 opacity-50">
              <Download size={15} />
              Export PDF
            </button>
          </div>

          <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-semibold">Audit event export</h3>
              <p className="mt-1 text-sm muted">Chronological event ledger with document hashes and actors.</p>
            </div>
            <button onClick={handleExportAudit} className="btn btn-secondary shrink-0">
              <Download size={15} />
              Export CSV
            </button>
          </div>

          <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-semibold">Benchmark snapshot</h3>
              <p className="mt-1 text-sm muted">Retrieval, extraction and end-to-end evaluation metrics.</p>
            </div>
            <button onClick={() => alert("JSON export coming soon!")} className="btn btn-secondary shrink-0 opacity-50">
              <Download size={15} />
              Export JSON
            </button>
          </div>

        </div>
      </div>
    </>
  );
}
