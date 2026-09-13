import { Download, FileClock, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { AuditTimeline } from "@/components/audit-timeline";
import { MetricCard, PageHeader } from "@/components/ui";
import { services } from "@/lib/services";

export default async function AuditPage() {
  const events = await services.getAuditTrail();

  return (
    <AppShell>
      <PageHeader
        eyebrow="Governance"
        title="Audit Trail"
        description="Immutable evidence lineage for ingestion, verification, rule evaluation and human review."
        action={
          <button className="btn btn-secondary">
            <Download size={16} />
            Export audit log
          </button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Audit events" value={events.length.toString()} detail="Across system" icon={FileClock} />
        <MetricCard label="Documents sealed" value={events.filter(e => e.action === "UPLOAD").length.toString()} detail="SHA-3-512 integrity records" icon={ShieldCheck} tone="teal" />
        <MetricCard label="Evidence links" value={events.filter(e => e.action === "EVALUATE").length.toString()} detail="Rule-level provenance records" icon={FileClock} tone="teal" />
        <MetricCard label="Human actions" value={events.filter(e => e.action === "HUMAN_REVIEW").length.toString()} detail="Officer review events" icon={ShieldCheck} tone="amber" />
      </div>

      <div className="mt-6 panel p-5">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="section-title">Event ledger</p>
            <h2 className="mt-1 text-lg font-semibold">System activity</h2>
          </div>
          <div className="flex gap-2">
            <select className="rounded-lg border border-line bg-white px-3 py-2 text-sm">
              <option>All actors</option>
              <option>System services</option>
              <option>Procurement Officer</option>
            </select>
            <select className="rounded-lg border border-line bg-white px-3 py-2 text-sm">
              <option>All event types</option>
              <option>Verification</option>
              <option>Rule evaluation</option>
              <option>Human review</option>
            </select>
          </div>
        </div>
        <AuditTimeline events={events} />
      </div>
    </AppShell>
  );
}
