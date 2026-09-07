import React from "react";
import Link from "next/link";
import { Shield, Building2, UserCircle, Bell, Search } from "lucide-react";

export const Navbar: React.FC = () => {
  return (
    <header className="bg-gem-navy text-white shadow-md border-b border-blue-900 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand / Logo */}
          <div className="flex items-center gap-3">
            <div className="bg-white p-1.5 rounded-md shadow flex items-center justify-center">
              <Shield className="w-6 h-6 text-gem-navy" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight text-white">GeM</span>
                <span className="text-xs bg-amber-500 text-slate-950 font-bold px-1.5 py-0.5 rounded">
                  COMPLIANCE AI
                </span>
              </div>
              <p className="text-[10px] text-blue-200 tracking-wider uppercase font-medium">
                Integrated Bid Verification Platform
              </p>
            </div>
          </div>

          {/* Quick Search */}
          <div className="hidden md:flex items-center bg-blue-950/60 border border-blue-800/80 rounded-lg px-3 py-1.5 w-80 text-sm text-slate-300">
            <Search className="w-4 h-4 text-blue-400 mr-2" />
            <input
              type="text"
              placeholder="Search Tender / Bidder / GSTIN..."
              className="bg-transparent border-none outline-none w-full placeholder:text-blue-300/50 text-white text-xs"
              readOnly
            />
          </div>

          {/* User profile & status */}
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-semibold text-white">Col. Rajesh Verma (Retd.)</span>
              <span className="text-[11px] text-blue-300">Procurement Officer • MeitY</span>
            </div>
            <div className="w-9 h-9 rounded-full bg-blue-700/80 border border-blue-400 flex items-center justify-center text-white font-bold text-sm shadow">
              RV
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
