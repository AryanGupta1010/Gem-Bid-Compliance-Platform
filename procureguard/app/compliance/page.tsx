import { FileCheck2, Filter, ShieldAlert } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { ComplianceTable } from "@/components/compliance-table";
import { MetricCard, PageHeader } from "@/components/ui";
import { services } from "@/lib/services";

export default async function CompliancePage() {
  const bidders = await services.getAllBids();

  return (
    <AppShell>
      <PageHeader
        eyebrow="Rule evaluation"
        title="Compliance Matrix"
        description="Compare every bidder against the same deterministic tender requirements."
        action={
          <button className="btn btn-secondary">
            <Filter size={16} />
            Filter matrix
          </button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Rules evaluated" value={bidders.length > 0 && bidders[0].rules ? bidders[0].rules.length.toString() : "0"} detail={`${bidders.length} bidders`} icon={FileCheck2} />
        <MetricCard label="Passed checks" value={bidders.reduce((acc, bidder) => acc + (bidder.rules?.filter(r => r.result === "PASS").length || 0), 0).toString()} detail="Strong evidence available" icon={FileCheck2} tone="teal" />
        <MetricCard label="Failed checks" value={bidders.reduce((acc, bidder) => acc + (bidder.rules?.filter(r => r.result === "FAIL").length || 0), 0).toString()} detail="Deterministic failures" icon={ShieldAlert} tone="red" />
        <MetricCard label="Review checks" value={bidders.reduce((acc, bidder) => acc + (bidder.rules?.filter(r => r.result === "REVIEW").length || 0), 0).toString()} detail="Officer attention required" icon={ShieldAlert} tone="amber" />
      </div>

      <div className="mt-6">
        <ComplianceTable bidders={bidders} />
      </div>

      <div className="mt-6 rounded-xl border border-cyan-100 bg-cyan-50 p-4 text-sm leading-6 text-cyan-950">
        <strong>Decisioning principle:</strong> connector outages and low-confidence evidence produce
        <strong> REVIEW</strong> or <strong>UNAVAILABLE</strong>; they do not become automatic failures.
      </div>
    </AppShell>
  );
}

