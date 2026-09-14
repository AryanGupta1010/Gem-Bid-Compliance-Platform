import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { AuditTimeline } from "@/components/audit/audit-timeline";
import { RiskBadge, StatusBadge } from "@/components/ui/status-badge";
import { services } from "@/lib/services";

export default async function Dashboard() {
  const [tenders, events] = await Promise.all([services.getAllTenders(), services.getAuditTrail()]);
  const bids = tenders.flatMap(t => t.bids);
  const attention = bids.filter(b => !b.reviewer_decision || ["Keep Under Review", "Request Clarification"].includes(b.reviewer_decision));
  const priority = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  attention.sort((a, b) => priority[a.risk] - priority[b.risk]);
  return <AppShell>
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p className="section-title">Procurement workspace</p><h1 className="page-title mt-2">What needs your attention?</h1><p className="mt-2 muted">Review evidence, resolve exceptions, and record your decision.</p></div><Link className="btn btn-primary" href="/tenders">Open tender register</Link></div>
    <p className="mb-6 border-l-4 border-teal bg-white p-4 text-sm">Evidence retrieval supports review; deterministic rules verify requirements. The officer makes the final decision. External verification currently uses offline fixtures, not live government APIs.</p>
    <dl className="panel mb-6 grid grid-cols-2 divide-x divide-line md:grid-cols-4">
      {[["Active tenders", tenders.filter(t => t.status === "active").length], ["Awaiting decision", attention.length], ["Failed evaluations", bids.filter(b => b.status === "FAIL").length], ["Processing packages", bids.flatMap(b => b.documents).filter(d => ["uploaded", "processing"].includes(d.status)).length]].map(([label, value]) => <div className="p-4" key={label}><dt className="text-sm muted">{label}</dt><dd className="mt-2 text-2xl font-semibold">{value}</dd></div>)}
    </dl>
    <section className="panel overflow-hidden"><div className="border-b border-line p-5"><h2 className="text-lg font-semibold">Officer decision queue</h2><p className="text-sm muted">Highest risk first. A PASS still requires an officer decision.</p></div>
      <div className="overflow-x-auto"><table className="data-table min-w-[650px]"><thead><tr><th>Bidder / tender</th><th>Result</th><th>Risk</th><th>Officer decision</th><th>Next step</th></tr></thead><tbody>{attention.map(b => <tr key={b.id}><td><Link className="font-semibold hover:underline" href={`/evaluations/${encodeURIComponent(b.id)}`}>{b.bidder_name}</Link><p className="text-xs muted">{tenders.find(t => t.id === b.tender_id)?.title}</p></td><td><StatusBadge status={b.status}/></td><td><RiskBadge risk={b.risk}/></td><td>{b.reviewer_decision || "Not recorded"}</td><td><Link className="text-teal underline" href={`/evaluations/${encodeURIComponent(b.id)}`}>Review evidence</Link></td></tr>)}</tbody></table></div>
      {!attention.length && <p className="p-6 muted">No outstanding decisions. Open Tenders to register a new procurement.</p>}
    </section>
    <section className="panel mt-6 p-5"><div className="mb-4 flex justify-between"><h2 className="font-semibold">Latest audit activity</h2><Link className="text-teal underline" href="/audit">Full audit trail</Link></div><AuditTimeline events={events} compact/></section>
  </AppShell>;
}
