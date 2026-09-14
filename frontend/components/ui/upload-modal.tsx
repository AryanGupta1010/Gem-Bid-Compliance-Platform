"use client";
import { useRef, useState } from "react";
import type { Bidder, Tender } from "@/lib/types";
import { FileUpload } from "./file-upload";
export function UploadModal({ tender, tenderBids }: { tender: Tender; tenderBids: Bidder[] }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [id, setId] = useState("");
  const selected = tenderBids.find(b => b.id === id);
  const busy = selected?.documents.some(d => ["uploaded", "processing"].includes(d.status));
  return <><button className="btn btn-primary" onClick={() => dialog.current?.showModal()}>Upload package</button><dialog ref={dialog} aria-labelledby="upload-title" className="w-[calc(100%-2rem)] max-w-xl rounded-lg p-6 backdrop:bg-slate-900/50"><h2 id="upload-title" className="text-xl font-semibold">Upload to {tender.title}</h2><label className="my-4 block text-sm font-semibold">Bidder<select className="mt-2 block w-full rounded border border-line p-2" value={id} onChange={e => setId(e.target.value)}><option value="">Select a registered bidder</option>{tenderBids.map(b => <option key={b.id} value={b.id}>{b.bidder_name}</option>)}</select></label>{selected && (busy ? <p role="status" className="my-4">A package is queued or processing. Review its progress in the bidder evaluation.</p> : <FileUpload key={id} bidId={id}/>)}<button className="btn btn-secondary mt-4" onClick={() => dialog.current?.close()}>Close</button></dialog></>;
}
