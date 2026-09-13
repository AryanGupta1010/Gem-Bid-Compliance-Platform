"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bell,
  ClipboardCheck,
  FileBarChart,
  FileCheck2,
  FileText,
  Gavel,
  LayoutDashboard,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  X
} from "lucide-react";
import { useState } from "react";

const nav = [
  ["/", "Dashboard", LayoutDashboard],
  ["/tenders", "Tenders", FileText],
  ["/evaluations", "Evaluations", ClipboardCheck],
  ["/compliance", "Compliance Matrix", FileCheck2],
  ["/verification", "Verification Center", ShieldCheck],
  ["/audit", "Audit Trail", Gavel],
  ["/reports", "Reports & Exports", FileBarChart],
  ["/settings", "Settings", Settings]
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen">
      {/* Mobile overlay */}
      {open && (
        <div 
          className="fixed inset-0 z-20 bg-slate-900/50 backdrop-blur-sm lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      
      <aside className={`fixed inset-y-0 left-0 z-30 w-64 border-r border-slate-800 bg-[#102b40] text-white transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex h-20 items-center justify-between border-b border-white/10 px-6">
          <div>
            <div className="flex items-center gap-2 font-semibold tracking-tight">
              <div className="rounded-lg bg-[#f1b44c] p-1.5 text-[#102b40]">
                <ShieldCheck size={18} />
              </div>
              ProcureGuard
            </div>
            <p className="mt-1 text-[10px] uppercase tracking-[0.16em] text-slate-300">GeM compliance intelligence</p>
          </div>
          <button className="lg:hidden" onClick={() => setOpen(false)}><X size={18} /></button>
        </div>

        <nav className="space-y-1 px-3 py-5">
          {nav.map(([href, label, Icon]) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${active ? "bg-white/[.12] font-semibold text-white" : "text-slate-300 hover:bg-white/[.08] hover:text-white"}`}
              >
                <Icon size={17} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="absolute bottom-5 left-4 right-4 rounded-lg border border-white/10 bg-white/5 p-3">
          <p className="text-xs font-semibold">Decision-support mode</p>
          <p className="mt-1 text-[11px] leading-4 text-slate-300">AI explains evidence. Rules verify facts. The officer decides.</p>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-line bg-white/95 px-5 backdrop-blur lg:px-8">
          <button className="rounded-lg border border-line p-2 lg:hidden" onClick={() => setOpen(true)}><Menu size={18} /></button>
          <div className="hidden items-center gap-2 text-sm text-slate-500 lg:flex">
            <Activity size={16} className="text-teal" />
            <span>GeM Evaluation Workspace</span>
            <span className="text-slate-300">/</span>
            <span className="font-medium text-ink">Procurement Officer</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm text-slate-500 md:flex">
              <Search size={15} />
              Search tenders, bidders, rules
            </div>
            <button className="relative rounded-lg border border-line p-2 text-slate-600"><Bell size={17} /><span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-amber-500" /></button>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-navy text-sm font-bold text-white">PO</div>
          </div>
        </header>
        <main className="mx-auto max-w-[1600px] p-5 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
