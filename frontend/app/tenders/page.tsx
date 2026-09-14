import Link from "next/link";
import { ArrowRight, CalendarDays, FileText, Plus, Search } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { MetricCard, PageHeader } from "@/components/ui/ui";
import { CreateTenderModal } from "@/components/tenders/create-tender-modal";
import { TendersClient } from "@/components/tenders/tenders-client";
import { services } from "@/lib/services";

export default async function TendersPage() {
  const tenders = await services.getAllTenders();
  const now = new Date();
  const month = now.toISOString().slice(0, 7);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Procurement workspace"
        title="Tenders"
        description="Manage tender source documents, evaluation status and bidder packages."
        action={
          <CreateTenderModal />
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Active tenders" value={String(tenders.filter(t => t.status === "active").length)} detail="Across procurement departments" icon={FileText} />
        <MetricCard label="Total bids" value={String(tenders.reduce((n, t) => n + t.bids.length, 0))} detail="Registered bidders" icon={FileText} tone="teal" />
        <MetricCard label="Deadlines this month" value={String(tenders.filter(t => t.deadline.startsWith(month)).length)} detail="UTC calendar month" icon={CalendarDays} tone="amber" />
        <MetricCard label="Documents processing" value={String(tenders.flatMap(t => t.bids).flatMap(b => b.documents).filter(d => ["uploaded", "processing"].includes(d.status)).length)} detail="In ingestion pipeline" icon={FileText} tone="teal" />
      </div>

      <TendersClient tenders={tenders} />
    </AppShell>
  );
}
