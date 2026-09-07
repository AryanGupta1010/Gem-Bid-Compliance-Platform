import React from "react";
import { ShieldCheck, ShieldAlert, ShieldX, Shield } from "lucide-react";
import { RiskLevel } from "@/types";

interface RiskBadgeProps {
  level: RiskLevel | string;
  size?: "sm" | "md" | "lg";
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, size = "md" }) => {
  const l = (level || "").toUpperCase();

  let colorClasses = "bg-slate-100 text-slate-700 border-slate-300";
  let icon = <Shield className="w-3.5 h-3.5" />;
  let label = `${l} RISK`;

  if (l === "LOW") {
    colorClasses = "bg-emerald-100 text-emerald-800 border-emerald-300 font-semibold";
    icon = <ShieldCheck className="w-4 h-4 text-emerald-600" />;
  } else if (l === "MEDIUM") {
    colorClasses = "bg-amber-100 text-amber-900 border-amber-300 font-semibold";
    icon = <Shield className="w-4 h-4 text-amber-600" />;
  } else if (l === "HIGH") {
    colorClasses = "bg-orange-100 text-orange-900 border-orange-300 font-semibold";
    icon = <ShieldAlert className="w-4 h-4 text-orange-600" />;
  } else if (l === "CRITICAL") {
    colorClasses = "bg-rose-100 text-rose-900 border-rose-400 font-bold animate-pulse";
    icon = <ShieldX className="w-4 h-4 text-rose-700" />;
  }

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5 gap-1",
    md: "text-xs px-2.5 py-1 gap-1.5",
    lg: "text-sm px-3.5 py-1.5 gap-2",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-md border tracking-wide shadow-sm uppercase ${colorClasses} ${sizeClasses}`}
    >
      {icon}
      <span>{label}</span>
    </span>
  );
};
