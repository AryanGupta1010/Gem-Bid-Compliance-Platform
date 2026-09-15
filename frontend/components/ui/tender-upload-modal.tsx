"use client";
import { useRef } from "react";
import type { Tender } from "@/lib/types";
import { FileUpload } from "./file-upload";

export function TenderUploadModal({ tender }: { tender: Tender }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const busy = tender.documents?.some(d => ["uploaded", "processing"].includes(d.status));
  
  return (
    <>
      <button className="btn btn-primary" onClick={() => dialog.current?.showModal()}>
        Upload Tender Document
      </button>
      <dialog ref={dialog} aria-labelledby="upload-tender-title" className="w-[calc(100%-2rem)] max-w-xl rounded-lg p-6 backdrop:bg-slate-900/50">
        <h2 id="upload-tender-title" className="text-xl font-semibold">Upload Tender Document for {tender.title}</h2>
        
        {busy ? (
          <p role="status" className="my-4">A document is queued or processing. Review its progress.</p>
        ) : (
          <FileUpload tenderId={tender.id} />
        )}
        
        <button className="btn btn-secondary mt-4" onClick={() => dialog.current?.close()}>Close</button>
      </dialog>
    </>
  );
}
