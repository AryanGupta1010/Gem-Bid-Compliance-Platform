"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { services } from "@/lib/services";

export function CreateTenderModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    const formData = new FormData(e.currentTarget);
    const data = {
      title: formData.get("title") as string,
      department: formData.get("department") as string,
      deadline: formData.get("deadline") as string,
      budget: formData.get("budget") as string,
    };
    
    await services.createTender(data);
    setIsSubmitting(false);
    setIsOpen(false);
    router.refresh();
  };

  return (
    <>
      <button onClick={() => setIsOpen(true)} className="btn btn-primary">
        <Plus size={16} />
        Create tender
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Create New Tender</h2>
              <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div>
                <label className="mb-1 block text-sm font-semibold">Tender Title</label>
                <input required name="title" className="w-full rounded-md border border-line px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="e.g. Procurement of IT Infrastructure" />
              </div>
              
              <div>
                <label className="mb-1 block text-sm font-semibold">Department</label>
                <input required name="department" className="w-full rounded-md border border-line px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="e.g. Ministry of Education" />
              </div>

              <div>
                <label className="mb-1 block text-sm font-semibold">Deadline</label>
                <input required type="date" name="deadline" className="w-full rounded-md border border-line px-3 py-2 text-sm focus:border-teal focus:outline-none" />
              </div>

              <div>
                <label className="mb-1 block text-sm font-semibold">Budget</label>
                <input required name="budget" className="w-full rounded-md border border-line px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="e.g. ₹15,00,00,000" />
              </div>
              
              <div className="mt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setIsOpen(false)} className="btn bg-white border border-line text-slate-700 hover:bg-slate-50">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="btn btn-primary">
                  {isSubmitting ? "Creating..." : "Create Tender"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
