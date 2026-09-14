import { AppShell } from "@/components/layout/app-shell";
import { AuditClient } from "@/components/audit/audit-client";
import { services } from "@/lib/services";
export default async function AuditPage() {
  const events = await services.getAuditTrail();
  return <AppShell><h1 className="page-title">Audit trail</h1><p className="mb-5 mt-2 muted">Persisted ingestion, evaluation and officer decision events. Document hashes identify uploaded bytes; this is not a cryptographically immutable ledger.</p><AuditClient events={events}/></AppShell>;
}
