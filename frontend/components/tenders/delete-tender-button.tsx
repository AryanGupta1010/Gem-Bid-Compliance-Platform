"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import { services } from "@/lib/services";

interface DeleteTenderButtonProps {
  tenderId: string;
  tenderTitle: string;
}

export function DeleteTenderButton({ tenderId, tenderTitle }: DeleteTenderButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete tender "${tenderTitle}" (${tenderId})? All associated bids, documents, and compliance records will be permanently deleted.`)) {
      return;
    }

    setLoading(true);
    try {
      await services.deleteTender(tenderId);
      router.push("/tenders");
      router.refresh();
    } catch (err: any) {
      alert(err?.message || "Failed to delete tender.");
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDelete}
      disabled={loading}
      className="flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-100 transition-colors disabled:opacity-50"
    >
      <Trash2 size={15} />
      {loading ? "Deleting..." : "Delete Tender"}
    </button>
  );
}
