import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/ui";
import { ReportsClient } from "@/components/reports/reports-client";
import { services } from "@/lib/services";

export default async function ReportsPage() {
  const [bids, auditTrail] = await Promise.all([services.getAllBids(), services.getAuditTrail()]);

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
