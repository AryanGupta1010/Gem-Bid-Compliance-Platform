"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { services } from "@/lib/services";
type Props = { bidId?: string; currentStage?: string | null; documentStatus?: string | null; documentHash?: string | null; reviewerDecision?: string | null };
export function ProcessingPipeline({ bidId, currentStage, documentStatus, documentHash, reviewerDecision }: Props) {
  const [stage, setStage] = useState(currentStage);
  const [status, setStatus] = useState(documentStatus);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const router = useRouter();
  useEffect(() => {
    if (!bidId || !["uploaded", "processing"].includes(documentStatus || "")) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const started = Date.now();
    async function poll() {
      try {
        if (document.hidden) { timer = setTimeout(poll, 3000); return; }
        const data = await services.getBidStatus(bidId!);
        if (cancelled) return;
        const latest = data.documents[0];
        setStage(latest?.processing_stage); setStatus(latest?.status); setError("");
        if (!latest || !["uploaded", "processing"].includes(latest.status)) { router.refresh(); return; }
        if (Date.now() - started > 15 * 60 * 1000) { setError("Processing is taking longer than expected. Check the RQ worker before retrying status."); return; }
        timer = setTimeout(poll, 3000);
      } catch (error) { if (!cancelled) setError(error instanceof Error ? error.message : "Status unavailable"); }
    }
    timer = setTimeout(poll, 2000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [bidId, documentStatus, router, retry]);
  const failed = status === "error" || stage === "FAILED";
  const label = failed ? "Processing failed — officer review required" : status === "completed" ? (reviewerDecision ? "Evaluation complete — officer decision recorded" : "Evaluation complete — awaiting officer decision") : status === "uploaded" ? "Queued — awaiting worker" : status === "processing" ? "Processing package" : "No package uploaded";
  return <section className="panel p-5" aria-live="polite"><h2 className="font-semibold">Package processing</h2><p className={`mt-2 ${failed ? "text-red-700" : "text-slate-700"}`}>{label}</p>{stage && <p className="mt-1 text-sm muted">Reported stage: {stage}</p>}<p className="mt-2 text-xs muted">Text retrieval → regex extraction → deterministic rules with offline verification fixtures → human decision.</p>{documentHash && <details className="mt-3 text-xs"><summary className="cursor-pointer">SHA-3-512 upload hash</summary><code className="block break-all mt-2">{documentHash}</code></details>}{error && <div role="alert" className="mt-3 text-sm text-red-700">{error}<button className="btn btn-secondary ml-3" onClick={() => setRetry(n => n + 1)}>Retry status</button></div>}</section>;
}
