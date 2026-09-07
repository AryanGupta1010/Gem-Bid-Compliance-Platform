"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function DemoRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    async function findDemoTender() {
      try {
        const tenders = await api.getTenders();
        if (tenders && tenders.length > 0) {
          router.replace(`/tenders/${tenders[0].id}`);
        } else {
          router.replace("/dashboard");
        }
      } catch {
        router.replace("/dashboard");
      }
    }
    findDemoTender();
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh] text-xs text-slate-500">
      <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2" />
      Loading Live Demo Evaluation...
    </div>
  );
}
