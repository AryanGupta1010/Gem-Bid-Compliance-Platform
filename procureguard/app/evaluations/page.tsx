import Link from "next/link";
import { ArrowRight, ClipboardCheck, Search, SlidersHorizontal } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { RiskBadge, StatusBadge } from "@/components/status-badge";
import { MetricCard, PageHeader } from "@/components/ui";
import { EvaluationsClient } from "@/components/evaluations-client";
import { services } from "@/lib/services";

export default async function EvaluationsPage() {
  const tender = await services.getTender("tnd-2024-8891");
  const bidders = tender?.bids || [];

  return (
    <AppShell>
      <PageHeader
        eyebrow="Decision support"
        title="Evaluations"
        description="Review bidder-level scores, risks, failed rules and unresolved evidence."
        action={
          <Link href={`/tenders/${encodeURIComponent(tender?.id || "tnd-2024-8891")}`} className="btn btn-primary">
            <ClipboardCheck size={16} />
            Open active tender
          </Link>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Bidders" value={bidders.length.toString()} detail="Golden demo evaluation" icon={ClipboardCheck} />
        <MetricCard label="Average score" value={bidders.length ? Math.round(bidders.reduce((a, b) => a + b.score, 0) / bidders.length).toString() : "0"} detail="Across all bidders" icon={ClipboardCheck} tone="teal" />
        <MetricCard label="Needs review" value={bidders.filter(b => b.status === "REVIEW").length.toString()} detail="Ambiguous evidence package" icon={SlidersHorizontal} tone="amber" />
        <MetricCard label="High risk" value={bidders.filter(b => b.risk === "HIGH" || b.risk === "CRITICAL").length.toString()} detail="Priority officer queue" icon={SlidersHorizontal} tone="red" />
      </div>

      <EvaluationsClient bidders={bidders} tenderTitle={tender?.title || "Tender Loading..."} />
    </AppShell>
  );
}
