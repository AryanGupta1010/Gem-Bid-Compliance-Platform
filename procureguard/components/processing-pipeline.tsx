import { Check, CircleDashed, Loader2 } from "lucide-react";

type PipelineProps = {
  currentStage?: string;
  documentHash?: string;
};

const ALL_STAGES = [
  { id: "UPLOAD", name: "Upload", method: "Ingestion" },
  { id: "HASH", name: "SHA-3-512 Hash", method: "Deterministic" },
  { id: "RENDER", name: "Render Pages", method: "Processing" },
  { id: "RETRIEVE", name: "Evidence Retrieval", method: "AI-assisted" },
  { id: "OCR", name: "Targeted OCR", method: "AI-assisted" },
  { id: "VERIFY", name: "Verify", method: "External / Deterministic" },
  { id: "EVALUATE", name: "Rule Evaluation", method: "Deterministic" },
  { id: "AGGREGATE", name: "Aggregate", method: "Deterministic" },
  { id: "HUMAN_REVIEW", name: "Human Review", method: "Officer decision" }
];

export function ProcessingPipeline({ currentStage, documentHash }: PipelineProps) {
  // Find current stage index. If not found, default to -1
  const currentIndex = currentStage ? ALL_STAGES.findIndex(s => s.id === currentStage) : -1;
  const isComplete = currentStage === "HUMAN_REVIEW" || currentStage === "ERROR";

  return (
    <div className="panel p-5">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="section-title">Processing pipeline</p>
          <h2 className="mt-1 text-lg font-semibold">Document Pipeline Status</h2>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${isComplete ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
          {isComplete ? "Processing Complete" : "Processing Active"}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-5 lg:grid-cols-9">
        {ALL_STAGES.map((stage, index) => {
          const status = index < currentIndex || isComplete ? "Complete" : index === currentIndex ? "In Progress" : "Pending";
          
          return (
            <div key={stage.id} className="relative">
              {index < ALL_STAGES.length - 1 && <div className="absolute left-[58%] top-4 hidden h-px w-full bg-slate-200 lg:block" />}
              <div className="relative flex flex-col items-center text-center">
                <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  status === "Complete" ? "bg-emerald-100 text-emerald-700" : 
                  status === "In Progress" ? "bg-amber-100 text-amber-700 animate-pulse" : 
                  "bg-slate-100 text-slate-400"
                }`}>
                  {status === "Complete" ? <Check size={15} /> : 
                   status === "In Progress" ? <Loader2 size={15} className="animate-spin" /> : 
                   <CircleDashed size={15} />}
                </div>
                <p className={`mt-2 text-[11px] font-semibold ${status === 'Pending' ? 'text-slate-400' : ''}`}>{stage.name}</p>
                <p className="mt-0.5 text-[10px] text-slate-500">{status}</p>
                <p className={`mt-0.5 text-[9px] font-medium ${
                  status === 'Pending' ? 'text-slate-300' :
                  stage.method.startsWith("AI") ? "text-purple-600" : 
                  stage.method === "Officer decision" ? "text-amber-600" : "text-teal"
                }`}>{stage.method}</p>
              </div>
            </div>
          );
        })}
      </div>
      
      {documentHash && (
        <div className="mt-5 rounded-lg bg-slate-50 p-3 text-xs text-slate-600 flex items-center justify-between">
          <span>Document integrity sealed at ingestion using <strong>SHA-3-512</strong>. Hash: <code className="font-mono text-slate-800">{documentHash.substring(0, 16)}...{documentHash.slice(-4)}</code></span>
        </div>
      )}
    </div>
  );
}
