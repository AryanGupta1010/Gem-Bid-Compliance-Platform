import React from "react";
import { FileText, ExternalLink, ShieldCheck, Crosshair } from "lucide-react";
import { Evidence } from "@/types";

interface EvidenceBoxViewerProps {
  evidence?: Evidence;
  documentName?: string;
  expectedText?: string;
  extractedValue?: string;
}

export const EvidenceBoxViewer: React.FC<EvidenceBoxViewerProps> = ({
  evidence,
  documentName = "Audited_Turnover_Statement_FY24.pdf",
  expectedText,
  extractedValue,
}) => {
  const pageNumber = evidence?.page_number || 1;
  const bbox = evidence?.bounding_box || [0.15, 0.40, 0.85, 0.55]; // [x1, y1, x2, y2]
  const val = extractedValue || evidence?.extracted_value || "Evidence Data";

  // Calculate box style as percentage
  const boxStyle: React.CSSProperties = {
    left: `${(bbox[0] || 0.1) * 100}%`,
    top: `${(bbox[1] || 0.3) * 100}%`,
    width: `${((bbox[2] || 0.8) - (bbox[0] || 0.1)) * 100}%`,
    height: `${((bbox[3] || 0.5) - (bbox[1] || 0.3)) * 100}%`,
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
      {/* Evidence Header */}
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-600" />
          <span className="font-semibold text-slate-800">{documentName}</span>
          <span className="bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded text-[10px] font-bold">
            Page {pageNumber}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-emerald-700 font-semibold text-[11px]">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Confidence: {((evidence?.confidence || 1.0) * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Simulated Document Canvas with Highlight Box */}
      <div className="relative bg-slate-100 p-6 min-h-[300px] flex items-center justify-center border-b border-slate-200">
        <div className="relative w-full max-w-md bg-white border border-slate-300 shadow-md rounded p-6 min-h-[260px] text-[11px] text-slate-500 font-mono space-y-2 select-none">
          <div className="w-24 h-2 bg-slate-200 rounded mb-4" />
          <div className="w-full h-2 bg-slate-100 rounded" />
          <div className="w-5/6 h-2 bg-slate-100 rounded" />
          <div className="w-4/6 h-2 bg-slate-100 rounded" />
          
          <div className="my-4 p-2.5 bg-slate-50 border border-dashed border-slate-200 rounded text-center">
            <span className="text-[10px] text-slate-400">--- AUDITED FINANCIAL EXTRACT / CLAUSE SECTION ---</span>
          </div>

          <div className="w-full h-2 bg-slate-100 rounded" />
          <div className="w-3/4 h-2 bg-slate-100 rounded" />
          <div className="w-5/6 h-2 bg-slate-100 rounded" />

          {/* Visual Bounding Box Region */}
          <div
            style={boxStyle}
            className="absolute border-2 border-emerald-500 bg-emerald-500/15 rounded shadow-sm flex flex-col justify-between p-1.5 transition-all animate-pulse"
          >
            <div className="flex items-center justify-between">
              <span className="bg-emerald-600 text-white text-[9px] font-bold px-1 py-0.2 rounded shadow">
                VERIFIED REGION
              </span>
              <Crosshair className="w-3 h-3 text-emerald-700" />
            </div>
            <div className="bg-white/90 rounded px-1.5 py-0.5 border border-emerald-400 text-emerald-950 font-bold text-[11px] text-center shadow-sm">
              {val}
            </div>
          </div>
        </div>
      </div>

      {/* Source attribution & metadata */}
      <div className="bg-slate-50 p-3 text-xs text-slate-600 flex items-center justify-between">
        <div>
          <span className="text-slate-400">Source: </span>
          <span className="font-semibold text-slate-700">{evidence?.source || "Registered Bidder Document"}</span>
        </div>
        <div className="text-[11px] text-slate-400">
          Visual coordinate anchor: [{bbox.map((n) => n.toFixed(2)).join(", ")}]
        </div>
      </div>
    </div>
  );
};
