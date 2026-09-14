import { AppShell } from "@/components/layout/app-shell";
import { EvaluationsClient } from "@/components/evaluations/evaluations-client";
import { services } from "@/lib/services";
export default async function EvaluationsPage() {
  const bids = await services.getAllBids();
  return <AppShell><h1 className="page-title">Evaluations</h1><p className="mt-2 muted">PASS: requirements met. FAIL: deterministic failure. REVIEW: unclear or unavailable evidence. All outcomes require a human decision.</p><EvaluationsClient bidders={bids} tenderTitle="All tenders"/></AppShell>;
}
