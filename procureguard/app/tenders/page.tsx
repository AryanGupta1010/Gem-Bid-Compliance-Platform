import Link from "next/link";
import { ArrowRight, CalendarDays, FileText, Plus, Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { MetricCard, PageHeader } from "@/components/ui";
import { CreateTenderModal } from "@/components/create-tender-modal";
import { TendersClient } from "@/components/tenders-client";
import { services } from "@/lib/services";

export default async function TendersPage() {
  const tenders = await services.getAllTenders();

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
        <MetricCard label="Active tenders" value={tenders.length.toString()} detail="Across procurement departments" icon={FileText} />
        <MetricCard label="Total bids" value="26" detail="Awaiting or under evaluation" icon={FileText} tone="teal" />
        <MetricCard label="Deadlines this month" value="7" detail="Requires active monitoring" icon={CalendarDays} tone="amber" />
        <MetricCard label="Documents processing" value="18" detail="In ingestion pipeline" icon={FileText} tone="teal" />
      </div>

      <TendersClient tenders={tenders} />
    </AppShell>
  );
}
