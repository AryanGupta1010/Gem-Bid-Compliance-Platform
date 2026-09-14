"use client";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return <AppShell><section role="alert" className="panel p-6"><h1 className="page-title">Workspace unavailable</h1><p className="my-4">The request could not complete. Check that the backend and database are running, then retry. No demo data is substituted.</p><button className="btn btn-primary" onClick={reset}>Retry</button><Link href="/tenders" className="btn btn-secondary ml-3">Tenders</Link></section></AppShell>;
}
