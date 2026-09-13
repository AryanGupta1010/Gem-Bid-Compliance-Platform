import Link from "next/link";
import { ArrowLeft, FileCheck2 } from "lucide-react";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { DecisionPanel } from "@/components/decision-panel";
import { EvidenceViewer } from "@/components/evidence-viewer";
import { RiskBadge, StatusBadge } from "@/components/status-badge";
import { FileUpload } from "@/components/file-upload";
import { ProcessingPipeline } from "@/components/processing-pipeline";
import { services } from "@/lib/services";

export default async function EvaluationDetailPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  
  // Fetch real data from backend
  const bidder = await services.getBid(id);
  const statusRes = await services.getBidStatus(id);

  if (!bidder) notFound();

  // Determine current pipeline stage
  let currentStage = undefined;
  let documentHash = undefined;
  
  if (statusRes?.documents && statusRes.documents.length > 0) {
    const doc = statusRes.documents[0];
    currentStage = doc.processing_stage;
    // Assuming we don't have documentHash in ProcessingStage right now, but we can pass undefined or fetch it if needed.
  }

  // A bidder may have uploaded documents but not processed yet.
  const hasDocuments = bidder.documents && bidder.documents.length > 0;
  const hasRules = bidder.rules && bidder.rules.length > 0;

  return (
    <AppShell>
      <Link href="/evaluations" className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-teal hover:underline">
        <ArrowLeft size={15} />
        Back to evaluations
      </Link>

      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="section-title">{bidder.tender_id}</p>
          <h1 className="mt-2 page-title">{bidder.bidder_name}</h1>
          <p className="mt-2 text-sm muted">Tender ID: {bidder.tender_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <RiskBadge risk={bidder.risk} />
          <StatusBadge status={bidder.status} />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="panel p-5">
          <p className="section-title">Compliance score</p>
          <p className="mt-2 text-4xl font-semibold">{bidder.score}<span className="text-lg text-slate-400">/100</span></p>
        </div>
        <div className="panel p-5">
          <p className="section-title">Rules passed</p>
          <p className="mt-2 text-4xl font-semibold text-emerald-700">{hasRules ? bidder.rules.filter((rule) => rule.result === "PASS").length : 0}</p>
        </div>
        <div className="panel p-5">
          <p className="section-title">Officer attention</p>
          <p className="mt-2 text-4xl font-semibold text-amber-700">{bidder.review_rules || 0}</p>
        </div>
      </div>

      {bidder.summary && (
        <div className="mt-6 rounded-xl border border-cyan-100 bg-cyan-50 p-4 text-sm leading-6 text-cyan-950">
          <strong>System recommendation:</strong> {bidder.summary}
        </div>
      )}

      {hasDocuments ? (
         <div className="mt-6">
            <ProcessingPipeline currentStage={currentStage} documentHash={bidder.documents?.[0]?.hash_sha3_512} />
         </div>
      ) : (
         <div className="mt-6">
            <FileUpload bidId={bidder.id} />
         </div>
      )}

      {hasRules && (
        <div className="mt-6">
          <EvidenceViewer bidder={bidder} />
        </div>
      )}

      <div className="mt-6">
        <DecisionPanel bidId={bidder.id} initialDecision={bidder.reviewer_decision} initialNote={bidder.reviewer_note} />
      </div>

      <div className="mt-6 panel p-5">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-cyan-50 p-2.5 text-teal">
            <FileCheck2 size={19} />
          </div>
          <div>
            <p className="section-title">Evidence lineage</p>
            <h2 className="mt-1 text-lg font-semibold">Every result remains traceable</h2>
          </div>
        </div>
        <div className="mt-5 grid gap-4 text-sm md:grid-cols-3">
          <div>
            <p className="text-xs text-slate-500">Bidder GSTIN</p>
            <p className="mt-1 font-mono font-semibold">{bidder.gstin || "N/A"}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Rule version</p>
            <p className="mt-1 font-semibold">GeM-Ruleset 1.4.0</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Evaluation timestamp</p>
            <p className="mt-1 font-semibold">{bidder.reviewed_at ? new Date(bidder.reviewed_at).toLocaleString() : "Pending"}</p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
