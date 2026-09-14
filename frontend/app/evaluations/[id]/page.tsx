import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { DecisionPanel } from "@/components/evaluations/decision-panel";
import { EvidenceViewer } from "@/components/evidence/evidence-viewer";
import { RiskBadge, StatusBadge } from "@/components/ui/status-badge";
import { FileUpload } from "@/components/ui/file-upload";
import { ProcessingPipeline } from "@/components/evaluations/processing-pipeline";
import { AuditTimeline } from "@/components/audit/audit-timeline";
import { services } from "@/lib/services";
export default async function EvaluationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const bidder = await services.getBid(id);
  if (!bidder) notFound();
  const events = await services.getAuditTrail(id);
  const latest = bidder.documents[0];
  const busy = latest && ["uploaded", "processing"].includes(latest.status);
  const evaluated = latest?.status === "completed" && bidder.rules.length > 0;
  return <AppShell>
    <nav aria-label="Breadcrumb" className="mb-5 flex flex-wrap gap-2 text-sm text-teal"><Link href="/tenders">Tenders</Link><span>→</span><Link href={`/tenders/${encodeURIComponent(bidder.tender_id)}`}>{bidder.tender_id}</Link><span>→ Evaluation</span></nav>
    <header className="mb-6 flex flex-wrap justify-between gap-3"><div><h1 className="page-title">{bidder.bidder_name}</h1><p className="mt-2 muted">GSTIN: {bidder.gstin || "Not supplied"}</p></div><div className="flex items-center gap-2"><StatusBadge status={bidder.status}/><RiskBadge risk={bidder.risk}/></div></header>
    <p className="panel mb-5 p-4">{bidder.summary || "No evaluation summary available."}</p>
    {!evaluated && <p role="status" className="mb-5 border-l-4 border-amber-500 bg-amber-50 p-4 text-sm">No completed evaluation for the latest package. Any existing results below belong to a previous evaluation or seeded demo preset, not this upload.</p>}
    <dl className="panel mb-5 grid grid-cols-2 gap-4 p-5 sm:grid-cols-4">{[["Score", bidder.score], ["Failed rules", bidder.failed_rules], ["Review rules", bidder.review_rules], ["Passed rules", bidder.rules.filter(r => r.result === "PASS").length]].map(([label, value]) => <div key={label}><dt className="muted text-sm">{label}</dt><dd className="mt-1 text-xl font-semibold">{value}</dd></div>)}</dl>
    <ProcessingPipeline key={latest?.id || "empty"} bidId={bidder.id} currentStage={latest?.processing_stage} documentStatus={latest?.status} documentHash={latest?.hash_sha3_512} reviewerDecision={bidder.reviewer_decision}/>
    {!busy && <div className="my-5"><FileUpload bidId={bidder.id}/></div>}
    {bidder.rules.length > 0 && <section className="my-5"><EvidenceViewer bidder={bidder}/></section>}
    <DecisionPanel key={`${bidder.id}:${bidder.reviewed_at || "pending"}`} bidId={bidder.id} initialDecision={bidder.reviewer_decision} initialNote={bidder.reviewer_note} disabled={!evaluated}/>
    <section className="panel mt-5 p-5"><h2 className="mb-4 text-lg font-semibold">Bidder audit history</h2><p className="mb-4 text-sm muted">Explicitly linked events only. Older unlinked records remain in the <Link href="/audit" className="underline">global audit trail</Link>.</p><AuditTimeline events={events}/></section>
  </AppShell>;
}
