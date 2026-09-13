import { AlertCircle, CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import { Status, Risk } from "@/lib/types";
import { riskClass, statusClass } from "@/lib/utils";

export function StatusBadge({ status }: { status: Status }) {
  const Icon = {
    PASS: CheckCircle2,
    FAIL: XCircle,
    REVIEW: AlertCircle,
    UNAVAILABLE: CircleDashed
  }[status];

  return (
    <span className={`status-badge ${statusClass(status)}`}>
      <Icon size={13} />
      {status}
    </span>
  );
}

export function RiskBadge({ risk }: { risk: Risk }) {
  return <span className={`risk-badge ${riskClass(risk)}`}>{risk} RISK</span>;
}
