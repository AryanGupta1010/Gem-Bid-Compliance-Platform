import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { ReportsClient } from "@/components/reports-client";
import { services } from "@/lib/services";

export default async function ReportsPage() {
  const bids = await services.getAllBids();
  const auditTrail = await services.getAuditTrail();

  return (
    <AppShell>
      <PageHeader
        eyebrow="Outputs"
        title="Reports & Exports"
        description="Generate evidence-backed reports for review meetings, audit requests and downstream procurement records."
      />

      <ReportsClient bids={bids} auditTrail={auditTrail} />
    </AppShell>
  );
}
