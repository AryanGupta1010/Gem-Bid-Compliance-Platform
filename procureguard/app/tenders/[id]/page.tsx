import Link from "next/link";
import { ArrowLeft, ArrowRight, CalendarDays, ClipboardCheck, FileText, Upload } from "lucide-react";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { ProcessingPipeline } from "@/components/processing-pipeline";
import { RiskBadge, StatusBadge } from "@/components/status-badge";
import { MetricCard } from "@/components/ui";
import { UploadModal } from "@/components/upload-modal";
import { services } from "@/lib/services";

export default async function TenderDetailPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const decodedId = decodeURIComponent(id);
  
  const tender = await services.getTender(decodedId);

  if (!tender) notFound();

  // For the golden demo tender, show associated bidders
  const isGoldenDemo = tender.id === "GEM/2026/B/XXXXXXX";
  const tenderBids = tender.bids || [];

  return (
    <AppShell>
      <Link href="/tenders" className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-teal hover:underline">
        <ArrowLeft size={15} />
        Back to tenders
      </Link>

      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="section-title">{tender.id}</p>
          <h1 className="mt-2 page-title">{tender.title}</h1>
          <p className="mt-2 text-sm muted">{tender.department}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">{tender.status}</span>
          <UploadModal tender={tender} tenderBids={tenderBids} />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Bid deadline" value={tender.deadline} detail={`Published ${tender.published}`} icon={CalendarDays} />
        <MetricCard label="Estimated budget" value={tender.budget} detail={tender.department} icon={FileText} tone="teal" />
        <MetricCard label="Total bids" value={String(tenderBids.length)} detail="Document packages received" icon={ClipboardCheck} tone="teal" />
        <MetricCard label="Status" value={tender.status} detail="Current evaluation phase" icon={FileText} tone="amber" />
      </div>

      <div className="mt-6"><ProcessingPipeline /></div>

      <div className="mt-6 panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-line p-5">
          <div>
            <p className="section-title">Bidder packages</p>
            <h2 className="mt-1 text-lg font-semibold">Received bid submissions</h2>
          </div>
          <Link href="/evaluations" className="text-xs font-semibold text-teal hover:underline">View all evaluations</Link>
        </div>
        {tenderBids.length === 0 ? (
          <div className="flex min-h-48 items-center justify-center p-8 text-center">
            <div>
              <p className="font-semibold">No bids received yet</p>
              <p className="mt-1 text-sm muted">Upload bidder documents to begin the compliance verification pipeline.</p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-line">
            {tenderBids.map((bidder) => (
              <Link
                key={bidder.id}
                href={`/evaluations/${bidder.id}`}
                className="flex flex-col gap-4 p-5 transition hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold">{bidder.bidder_name}</h3>
                    <RiskBadge risk={bidder.risk} />
                    <StatusBadge status={bidder.status} />
                  </div>
                  <p className="mt-1 text-sm muted">{bidder.summary}</p>
                  <p className="mt-2 font-mono text-xs text-slate-400">GSTIN: {bidder.gstin}</p>
                </div>
                <div className="flex shrink-0 items-center gap-4">
                  <div className="text-right">
                    <p className="text-2xl font-semibold">{bidder.score}</p>
                    <p className="text-[10px] uppercase tracking-wide text-slate-500">Score</p>
                  </div>
                  <ArrowRight size={17} className="text-slate-400" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 panel p-5">
        <p className="section-title">Tender workspace</p>
        <h2 className="mt-1 text-lg font-semibold">Source documents</h2>
        <div className="mt-4 divide-y divide-line rounded-lg border border-line">
          {[
            ["Tender_Notice.pdf", "12 Aug 2026", "SHA-3-512: a1b2c3d4...f5e6"],
            ["Technical_Requirements.pdf", "12 Aug 2026", "SHA-3-512: 7e8f9a0b...c1d2"],
            ["Eligibility_Criteria.pdf", "12 Aug 2026", "SHA-3-512: 3d4e5f6a...b7c8"]
          ].map(([name, date, hash]) => (
            <div key={name} className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-slate-100 p-2 text-slate-500"><FileText size={16} /></div>
                <div>
                  <p className="text-sm font-semibold">{name}</p>
                  <p className="mt-0.5 text-xs text-slate-500">Uploaded {date}</p>
                </div>
              </div>
              <p className="font-mono text-xs text-slate-400">{hash}</p>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
