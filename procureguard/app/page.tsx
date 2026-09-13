import Link from "next/link";
import { AlertTriangle, ArrowRight, ClipboardCheck, FileCheck2, FileClock, FileWarning, ShieldAlert, TrendingUp } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/ui";
import { ComplianceChart, RiskChart } from "@/components/charts";
import { ProcessingPipeline } from "@/components/processing-pipeline";
import { AuditTimeline } from "@/components/audit-timeline";
import { RiskBadge, StatusBadge } from "@/components/status-badge";
import { services } from "@/lib/services";

export default async function Dashboard() {
  const tenders = await services.getAllTenders();
  const bidders = await services.getAllBids();
  
  // Keep tender context if there is at least one
  const tender = tenders.length > 0 ? tenders[0] : null;
  
  const auditEvents = await services.getAuditTrail();

  return (
    <AppShell>
      <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="section-title">Procurement control room</p>
          <h1 className="mt-2 page-title">Good morning, Officer</h1>
          <p className="mt-2 text-sm muted">Evidence-backed bid verification for Government e-Marketplace evaluations.</p>
        </div>
        {tender && (
          <Link href={`/tenders/${encodeURIComponent(tender.id)}`} className="btn btn-primary"><ClipboardCheck size={16} /> Open active evaluation</Link>
        )}
      </div>

      <div className="mb-6 rounded-xl border border-cyan-100 bg-cyan-50 p-4 text-sm text-cyan-950">
        <strong>North-star control:</strong> AI finds and explains evidence; deterministic code verifies facts; the Procurement Officer makes the final decision.
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <MetricCard label="Active Tenders" value={tenders.filter(t => t.status === "active").length.toString()} detail="Currently open" icon={FileCheck2} />
        <MetricCard label="Bids Under Evaluation" value={bidders.length.toString()} detail={`Across ${tenders.length} tenders`} icon={ClipboardCheck} tone="teal" />
        <MetricCard label="Passed Bids" value={bidders.filter(b => b.status === "PASS").length.toString()} detail="Strong evidence" icon={TrendingUp} tone="teal" />
        <MetricCard label="Failed Bids" value={bidders.filter(b => b.status === "FAIL").length.toString()} detail="Deterministic failures" icon={FileWarning} tone="red" />
        <MetricCard label="Reviews Required" value={bidders.filter(b => b.status === "REVIEW").length.toString()} detail="Officer attention" icon={FileClock} tone="amber" />
        <MetricCard label="High Risk Bids" value={bidders.filter(b => b.risk === "HIGH").length.toString()} detail="Priority queue" icon={ShieldAlert} tone="red" />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.45fr_.8fr]">
        <div className="panel p-5">
          <div className="flex items-start justify-between">
            <div><p className="section-title">Compliance overview</p><h2 className="mt-1 text-lg font-semibold">Golden demo tender</h2></div>
            <span className="text-xs text-slate-500">{tender?.id || "N/A"}</span>
          </div>
          <p className="mt-2 text-sm muted">{tender?.title || "Demo workspace"}</p>
          <ComplianceChart />
        </div>
        <div className="panel p-5">
          <p className="section-title">Risk distribution</p>
          <h2 className="mt-1 text-lg font-semibold">Current evaluation queue</h2>
          <RiskChart />
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-slate-500">Low risk</span><strong>{bidders.filter(b => b.risk === "LOW").length} bidder</strong></div>
            <div className="flex justify-between"><span className="text-slate-500">Medium risk</span><strong>{bidders.filter(b => b.risk === "MEDIUM").length} bidder</strong></div>
            <div className="flex justify-between"><span className="text-slate-500">High risk</span><strong>{bidders.filter(b => b.risk === "HIGH").length} bidder</strong></div>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <div className="panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-line p-5">
            <div>
              <p className="section-title">Recent evaluations</p>
              <h2 className="mt-1 text-lg font-semibold">Bidder decision support</h2>
            </div>
            <Link href="/evaluations" className="text-xs font-semibold text-teal hover:underline">
              View all
            </Link>
          </div>
          <div className="divide-y divide-line">
            {bidders.map((bidder) => (
              <Link
                key={bidder.id}
                href={`/evaluations/${bidder.id}`}
                className="flex flex-col gap-3 p-5 transition hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold">{bidder.bidder_name}</h3>
                    <RiskBadge risk={bidder.risk as any} />
                    <StatusBadge status={bidder.status as any} />
                  </div>
                  <p className="mt-1 text-sm muted">{bidder.summary}</p>
                </div>
                <div className="flex shrink-0 items-center gap-4">
                  <div className="text-right">
                    <p className="text-2xl font-semibold">{bidder.score}</p>
                    <p className="text-[11px] uppercase tracking-wide text-slate-500">Score</p>
                  </div>
                  <ArrowRight size={17} className="text-slate-400" />
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="panel p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="section-title">Attention queue</p>
              <h2 className="mt-1 text-lg font-semibold">Items requiring officer review</h2>
            </div>
            <AlertTriangle size={19} className="text-amber-600" />
          </div>
          <div className="mt-5 space-y-3">
            {[
              ["MedCore Technologies", "GST certificate is unreadable", "REVIEW"],
              ["MedCore Technologies", "MSME / Udyam evidence conflicts", "REVIEW"],
              ["Apex Industrial Solutions", "Potential debarment match", "REVIEW"],
              ["Apex Industrial Solutions", "OEM authorization identity mismatch", "FAIL"]
            ].map(([name, detail, status]) => (
              <Link
                key={`${name}-${detail}`}
                href="/evaluations"
                className="flex items-start gap-3 rounded-lg border border-line p-3 transition hover:bg-slate-50"
              >
                <div className={`mt-0.5 h-2.5 w-2.5 rounded-full ${status === "FAIL" ? "bg-red-500" : "bg-amber-500"}`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">{name}</p>
                  <p className="mt-1 text-xs text-slate-500">{detail}</p>
                </div>
                <StatusBadge status={status as "FAIL" | "REVIEW"} />
              </Link>
            ))}
          </div>
          <Link href="/verification" className="mt-5 flex items-center gap-2 text-sm font-semibold text-teal hover:underline">
            Open verification center <ArrowRight size={15} />
          </Link>
        </div>
      </div>

      {tender && (
        <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_1.2fr]">
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="section-title">Active tender</p>
                <h2 className="mt-1 text-lg font-semibold">{tender.title}</h2>
              </div>
              <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700 uppercase">
                {tender.status}
              </span>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs text-slate-500">Department</p>
                <p className="mt-1 font-semibold">{tender.department}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Tender ID</p>
                <p className="mt-1 font-mono text-xs font-semibold">{tender.id}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Bid deadline</p>
                <p className="mt-1 font-semibold">{tender.deadline}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Estimated budget</p>
                <p className="mt-1 font-semibold">{tender.budget}</p>
              </div>
            </div>
            <Link href={`/tenders/${encodeURIComponent(tender.id)}`} className="btn btn-secondary mt-5 w-full">
              Inspect tender workspace <ArrowRight size={15} />
            </Link>
          </div>

          <div className="panel overflow-hidden">
            <div className="flex items-center justify-between border-b border-line p-5">
              <div>
                <p className="section-title">Audit activity</p>
                <h2 className="mt-1 text-lg font-semibold">Latest evidence events</h2>
              </div>
              <Link href="/audit" className="text-xs font-semibold text-teal hover:underline">
                Full trail
              </Link>
            </div>
            <div className="p-5">
              <AuditTimeline events={auditEvents} compact />
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
