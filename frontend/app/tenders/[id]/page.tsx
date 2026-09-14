import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { RiskBadge, StatusBadge } from "@/components/ui/status-badge";
import { UploadModal } from "@/components/ui/upload-modal";
import { AddBidder } from "@/components/ui/add-bidder";
import { services } from "@/lib/services";
export default async function TenderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tender = await services.getTender(id);
  if (!tender) notFound();
  return <AppShell>
    <Link href="/tenders" className="text-teal underline">← Tenders</Link>
    <div className="my-6 flex flex-wrap justify-between gap-4"><div><p className="section-title break-all">{tender.id}</p><h1 className="page-title mt-2">{tender.title}</h1><p className="mt-2 muted">{tender.department} · {tender.status}</p></div>{tender.bids.length > 0 && <UploadModal tender={tender} tenderBids={tender.bids}/>}</div>
    <dl className="panel grid gap-4 p-5 sm:grid-cols-3"><div><dt className="muted">Deadline</dt><dd>{tender.deadline}</dd></div><div><dt className="muted">Budget</dt><dd>{tender.budget}</dd></div><div><dt className="muted">Registered bidders</dt><dd>{tender.bids.length}</dd></div></dl>
    <div className="my-6"><AddBidder tenderId={tender.id}/></div>
    <section className="panel overflow-hidden"><h2 className="border-b border-line p-5 text-lg font-semibold">Review bidders</h2><div className="overflow-x-auto"><table className="data-table min-w-[600px]"><thead><tr><th>Bidder</th><th>Result</th><th>Risk</th><th>Packages</th><th>Officer decision</th></tr></thead><tbody>{tender.bids.map(b => <tr key={b.id}><td><Link href={`/evaluations/${encodeURIComponent(b.id)}`} className="font-semibold text-teal underline">{b.bidder_name}</Link><p className="text-xs muted">{b.gstin || "GSTIN not supplied"}</p></td><td><StatusBadge status={b.status}/></td><td><RiskBadge risk={b.risk}/></td><td>{b.documents.length}</td><td>{b.reviewer_decision || "Pending"}</td></tr>)}</tbody></table></div>{!tender.bids.length && <p className="p-6 muted">Register a bidder above, then upload their consolidated PDF package.</p>}</section>
  </AppShell>;
}
