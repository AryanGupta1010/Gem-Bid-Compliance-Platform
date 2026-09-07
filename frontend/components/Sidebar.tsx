"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  FileText, 
  CheckSquare, 
  History, 
  ShieldAlert, 
  ExternalLink,
  Layers,
  Database
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    { label: "Executive Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Active Tenders", href: "/tenders", icon: FileText },
    { label: "Live Evaluation Demo", href: "/tenders/demo", icon: CheckSquare, highlight: true },
    { label: "External Verification", href: "/verification", icon: ShieldAlert },
    { label: "Audit Trail", href: "/audit", icon: History },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-200 min-h-[calc(100vh-4rem)] flex flex-col justify-between border-r border-slate-800 p-4">
      <div className="space-y-6">
        <div>
          <div className="px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase mb-2">
            Navigation Menu
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? "bg-blue-600 text-white shadow-md font-semibold"
                      : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                  } ${item.highlight ? "border border-amber-500/40 bg-amber-950/20 text-amber-300" : ""}`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-white" : item.highlight ? "text-amber-400" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                  {item.highlight && (
                    <span className="ml-auto text-[10px] bg-amber-500/30 text-amber-300 px-1.5 py-0.5 rounded font-bold">
                      DEMO
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* System & Architecture Info */}
        <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800 text-[11px] space-y-2">
          <div className="flex items-center gap-1.5 font-bold text-slate-300">
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            <span>SIH26100 Architecture</span>
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            Deterministic Rule Engine + Explainable Scoring + Traceable Evidence + Human Officer Final Decision.
          </p>
          <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-400">
            <span>Engine: Deterministic</span>
            <span className="text-emerald-400 font-semibold">● v1.0.0</span>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
        <p className="font-semibold text-slate-300">GeM Procurement Sandbox</p>
        <p>© 2026 Government e-Marketplace</p>
      </div>
    </aside>
  );
};
