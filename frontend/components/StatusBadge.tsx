import React from "react";
import { CheckCircle2, XCircle, AlertTriangle, HelpCircle, Clock } from "lucide-react";
import { RuleStatus } from "@/types";

interface StatusBadgeProps {
  status: RuleStatus | string;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = "md",
  showIcon = true,
}) => {
  const s = (status || "").toUpperCase();

  let colorClasses = "bg-slate-100 text-slate-700 border-slate-300";
  let icon = <HelpCircle className="w-3.5 h-3.5" />;
  let label = s;

  if (s === "PASS") {
    colorClasses = "bg-emerald-50 text-emerald-700 border-emerald-300";
    icon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />;
    label = "PASS";
  } else if (s === "FAIL") {
    colorClasses = "bg-rose-50 text-rose-700 border-rose-300";
    icon = <XCircle className="w-3.5 h-3.5 text-rose-600" />;
    label = "FAIL";
  } else if (s === "REVIEW") {
    colorClasses = "bg-amber-50 text-amber-800 border-amber-300";
    icon = <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
    label = "REVIEW";
  } else if (s === "UNAVAILABLE") {
    colorClasses = "bg-purple-50 text-purple-700 border-purple-300";
    icon = <Clock className="w-3.5 h-3.5 text-purple-600" />;
    label = "UNAVAILABLE";
  }

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5 gap-1",
    md: "text-xs px-2.5 py-1 gap-1.5 font-semibold",
    lg: "text-sm px-3.5 py-1.5 gap-2 font-bold",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-sm transition-all ${colorClasses} ${sizeClasses}`}
    >
      {showIcon && icon}
      <span>{label}</span>
    </span>
  );
};
