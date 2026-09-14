"use client";
import { exportToCSV } from "@/lib/export";
import type { Bidder, AuditEvent } from "@/lib/types";
export function ReportsClient({ bids, auditTrail }: { bids: Bidder[]; auditTrail: AuditEvent[] }) {
  const rules = bids.flatMap(b => b.rules.map(r => ({ Bidder: b.bidder_name, Tender: b.tender_id, Rule: r.rule_name, Result: r.result, Actual: r.extracted_value, Required: r.expected_value, Document: r.document_name, Page: r.page, Confidence: r.confidence, Source: r.source, Method: r.model_version, Evidence: r.evidence, BoundingBox: r.bounding_box?.join(", "), EvaluatedAt: r.timestamp })));
  const reports = [
    { title: "Bid compliance summary", description: `${bids.length} bidders; includes system outcome and separate officer decision.`, count: bids.length, run: () => exportToCSV("bid-compliance.csv", bids.map(b => ({ ID: b.id, Tender: b.tender_id, Bidder: b.bidder_name, Result: b.status, Risk: b.risk, Score: b.score, FailedRules: b.failed_rules, ReviewRules: b.review_rules, OfficerDecision: b.reviewer_decision, Rationale: b.reviewer_note, ReviewedAt: b.reviewed_at }))) },
    { title: "Rule evidence lineage", description: `${rules.length} rule records with extracted values, source documents, pages and methods.`, count: rules.length, run: () => exportToCSV("rule-evidence.csv", rules) },
    { title: "Audit event ledger", description: `${auditTrail.length} persisted events. No silent 50-event truncation.`, count: auditTrail.length, run: () => exportToCSV("audit-events.csv", auditTrail.map(e => ({ ...e }))) },
  ];
  return <div className="panel divide-y divide-line">{reports.map(report => <section key={report.title} className="flex flex-wrap items-center justify-between gap-4 p-5"><div><h2 className="font-semibold">{report.title}</h2><p className="mt-1 text-sm muted">{report.description}</p></div><button className="btn btn-secondary" disabled={!report.count} onClick={report.run}>Export CSV</button></section>)}</div>;
}
