"use client";

import { useState } from "react";
import { Upload, X, File, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { services } from "@/lib/services";
import { Bidder, Tender } from "@/lib/types";

interface UploadModalProps {
  tender: Tender;
  tenderBids: Bidder[];
}

export function UploadModal({ tender, tenderBids }: UploadModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedBidId, setSelectedBidId] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");
  
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadStatus("idle");
      setErrorMessage("");
    }
  };

  const handleUpload = async () => {
    if (!selectedBidId || !selectedFile) return;
    
    setIsUploading(true);
    setUploadStatus("idle");
    setErrorMessage("");
    
    try {
      const result = await services.uploadDocument(selectedBidId, selectedFile);
      if (result) {
        setUploadStatus("success");
        setTimeout(() => {
          setIsOpen(false);
          setSelectedFile(null);
          setSelectedBidId("");
          setUploadStatus("idle");
          router.refresh();
        }, 1500);
      } else {
        setUploadStatus("error");
        setErrorMessage("Failed to upload document. Please try again.");
      }
    } catch (e) {
      setUploadStatus("error");
      setErrorMessage("An unexpected error occurred during upload.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <>
      <button onClick={() => setIsOpen(true)} className="btn btn-primary">
        <Upload size={16} /> 
        Upload documents
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Upload Bid Document</h2>
              <button 
                onClick={() => !isUploading && setIsOpen(false)} 
                disabled={isUploading}
                className="text-slate-400 hover:text-slate-600 disabled:opacity-50"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="flex flex-col gap-5">
              {/* Bidder Selection */}
              <div>
                <label className="mb-2 block text-sm font-semibold">Select Bidder</label>
                <select 
                  className="w-full rounded-md border border-line p-3 text-sm focus:border-teal focus:outline-none"
                  value={selectedBidId}
                  onChange={(e) => setSelectedBidId(e.target.value)}
                  disabled={isUploading}
                >
                  <option value="" disabled>-- Select a bidder --</option>
                  {tenderBids.map(bid => (
                    <option key={bid.id} value={bid.id}>
                      {bid.bidder_name} ({bid.id}) - Status: {bid.status}
                    </option>
                  ))}
                </select>
                {tenderBids.length === 0 && (
                  <p className="mt-2 text-xs text-amber-600 flex items-center gap-1">
                    <AlertCircle size={14}/> No bids registered for this tender yet.
                  </p>
                )}
              </div>

              {/* File Selection */}
              <div>
                <label className="mb-2 block text-sm font-semibold">Document (PDF)</label>
                
                {!selectedFile ? (
                  <div className="relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-line bg-slate-50 p-8 text-center transition-colors hover:bg-slate-100">
                    <Upload size={24} className="mb-2 text-slate-400" />
                    <p className="text-sm font-medium text-slate-700">Click to select PDF</p>
                    <p className="text-xs text-slate-500 mt-1">PDFs up to 50MB</p>
                    <input 
                      type="file" 
                      accept=".pdf,application/pdf" 
                      className="absolute inset-0 cursor-pointer opacity-0"
                      onChange={handleFileChange}
                      disabled={isUploading || !selectedBidId}
                    />
                  </div>
                ) : (
                  <div className="flex items-center justify-between rounded-lg border border-line bg-slate-50 p-4">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <File size={24} className="text-teal shrink-0" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-slate-700">{selectedFile.name}</p>
                        <p className="text-xs text-slate-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    {!isUploading && (
                      <button onClick={() => setSelectedFile(null)} className="p-2 text-slate-400 hover:text-red-500">
                        <X size={16} />
                      </button>
                    )}
                  </div>
                )}
              </div>
              
              {uploadStatus === "error" && (
                <div className="rounded-md bg-red-50 p-3 text-sm text-red-600 flex items-center gap-2">
                  <AlertCircle size={16} />
                  {errorMessage}
                </div>
              )}
              
              {uploadStatus === "success" && (
                <div className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-700 flex items-center gap-2">
                  <CheckCircle2 size={16} />
                  Document uploaded and processing queued!
                </div>
              )}

              <div className="mt-2 flex justify-end gap-3 pt-4 border-t border-line">
                <button 
                  type="button" 
                  onClick={() => setIsOpen(false)} 
                  disabled={isUploading}
                  className="btn bg-white border border-line text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleUpload} 
                  disabled={!selectedFile || !selectedBidId || isUploading || uploadStatus === "success"} 
                  className="btn btn-primary min-w-[120px]"
                >
                  {isUploading ? (
                    <><Loader2 size={16} className="animate-spin" /> Uploading...</>
                  ) : "Upload File"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
