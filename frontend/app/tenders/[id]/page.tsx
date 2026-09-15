import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { RiskBadge, StatusBadge } from "@/components/ui/status-badge";
import { UploadModal } from "@/components/ui/upload-modal";
import { TenderUploadModal } from "@/components/ui/tender-upload-modal";
import { AddBidder } from "@/components/ui/add-bidder";
import { DeleteTenderButton } from "@/components/tenders/delete-tender-button";
import { services } from "@/lib/services";
export default async function TenderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tender = await services.getTender(id);
  if (!tender) notFound();
  return <AppShell>
    <Link href="/tenders" className="text-teal underline">← Tenders</Link>
    <div className="my-6 flex flex-wrap justify-between gap-4"><div><p className="section-title break-all">{tender.id}</p><h1 className="page-title mt-2">{tender.title}</h1><p className="mt-2 muted">{tender.department} · {tender.status}</p></div><div className="flex items-center gap-2">{!tender.documents?.length && <TenderUploadModal tender={tender} />}{tender.bids.length > 0 && <UploadModal tender={tender} tenderBids={tender.bids}/>}<DeleteTenderButton tenderId={tender.id} tenderTitle={tender.title}/></div></div>
    <dl className="panel grid gap-4 p-5 sm:grid-cols-2 md:grid-cols-4">
      <div><dt className="muted">Tender No.</dt><dd>{tender.tender_number || "Not Extracted"}</dd></div>
      <div><dt className="muted">Deadline</dt><dd>{tender.deadline}</dd></div>
      <div><dt className="muted">Budget</dt><dd>{tender.budget}</dd></div>
      <div><dt className="muted">Quantity</dt><dd>{tender.quantity || "Not Extracted"}</dd></div>
      <div><dt className="muted">EMD</dt><dd>{tender.emd || "Not Extracted"}</dd></div>
      <div><dt className="muted">Warranty</dt><dd>{tender.warranty || "Not Extracted"}</dd></div>
      <div><dt className="muted">Delivery Period</dt><dd>{tender.delivery_period || "Not Extracted"}</dd></div>
      <div><dt className="muted">Registered Bidders</dt><dd>{tender.bids.length}</dd></div>
    </dl>
    
    <section className="panel overflow-hidden my-6">
      <h2 className="border-b border-line p-5 text-lg font-semibold">Tender Requirements</h2>
      {tender.requirements && tender.requirements.length > 0 ? (
        <div className="overflow-x-auto"><table className="data-table min-w-[600px]">
          <thead><tr><th>Rule</th><th>Expected</th><th>Mandatory</th><th>Status</th></tr></thead>
          <tbody>
            {tender.requirements.map(req => (
              <tr key={req.id}>
                <td>
                  <p className="font-semibold">{req.name}</p>
                  <p className="text-xs muted">{req.description}</p>
                  {req.source_text && (
                    <p className="text-xs mt-2 p-2 bg-surface rounded border border-line text-muted">
                      Source: <i>"{req.source_text}"</i>
                    </p>
                  )}
                </td>
                <td>{req.operator} {req.expected_value} {req.unit || ""}</td>
                <td>{req.mandatory ? "Yes" : "No"}</td>
                <td><StatusBadge status={req.status === "approved" ? "PASS" : req.status === "rejected" ? "FAIL" : "REVIEW"} /></td>
              </tr>
            ))}
          </tbody>
        </table></div>
      ) : (
        <p className="p-6 muted">No requirements extracted yet. Upload a Tender PDF to automatically extract structural rules.</p>
      )}
    </section>

    <div className="my-6"><AddBidder tenderId={tender.id}/></div>
    <section className="panel overflow-hidden"><h2 className="border-b border-line p-5 text-lg font-semibold">Review bidders</h2><div className="overflow-x-auto"><table className="data-table min-w-[600px]"><thead><tr><th>Bidder</th><th>Result</th><th>Risk</th><th>Packages</th><th>Officer decision</th></tr></thead><tbody>{tender.bids.map(b => <tr key={b.id}><td><Link href={`/evaluations/${encodeURIComponent(b.id)}`} className="font-semibold text-teal underline">{b.bidder_name}</Link><p className="text-xs muted">{b.gstin || "GSTIN not supplied"}</p></td><td><StatusBadge status={b.status}/></td><td><RiskBadge risk={b.risk}/></td><td>{b.documents.length}</td><td>{b.reviewer_decision || "Pending"}</td></tr>)}</tbody></table></div>{!tender.bids.length && <p className="p-6 muted">Register a bidder above, then upload their consolidated PDF package.</p>}</section>
  </AppShell>;
}
