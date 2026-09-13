import { AppShell } from "@/components/app-shell";
import { MetricCard, PageHeader } from "@/components/ui";
import { StatusBadge } from "@/components/status-badge";
import { ConnectorState, Status } from "@/lib/types";
import { Database, Globe, AlertTriangle, CheckCircle2, CircleDashed, ShieldCheck, XCircle, RefreshCw } from "lucide-react";

type Connector = {
  name: string;
  source: string;
  state: ConnectorState;
  lastCheck: string;
  description: string;
  decisionImpact: string;
};

const connectors: Connector[] = [
  {
    name: "GST Verification",
    source: "Sandbox GST Public API",
    state: "CONNECTED",
    lastCheck: "08 Sep 2026, 10:42 IST",
    description: "Live sandbox verification of GSTIN validity, registration status and identity match.",
    decisionImpact: "PASS or FAIL based on API response"
  },
  {
    name: "CPPP Debarment",
    source: "Local debarment fixture",
    state: "CONNECTED",
    lastCheck: "08 Sep 2026, 10:42 IST",
    description: "Normalized bidder identity checked against public debarment records from CPPP.",
    decisionImpact: "PASS or REVIEW if potential match found"
  },
  {
    name: "Udyam / MSME",
    source: "Mock adapter",
    state: "UNAVAILABLE",
    lastCheck: "08 Sep 2026, 10:41 IST",
    description: "Udyam registration verification for MSME status claims. Currently using adapter-compatible fixture.",
    decisionImpact: "UNAVAILABLE → REVIEW (never auto-FAIL)"
  },
  {
    name: "BIS Certification",
    source: "Mock adapter",
    state: "PENDING",
    lastCheck: "—",
    description: "Bureau of Indian Standards product certification verification. Planned for future integration.",
    decisionImpact: "UNAVAILABLE → REVIEW (never auto-FAIL)"
  },
  {
    name: "MCA21 / Company Registry",
    source: "Mock adapter",
    state: "UNAVAILABLE",
    lastCheck: "—",
    description: "Ministry of Corporate Affairs company registration and director verification.",
    decisionImpact: "UNAVAILABLE → REVIEW (never auto-FAIL)"
  }
];

const stateConfig: Record<ConnectorState, { icon: typeof CheckCircle2; className: string; label: string }> = {
  CONNECTED: { icon: CheckCircle2, className: "bg-emerald-50 text-emerald-700", label: "Connected" },
  UNAVAILABLE: { icon: CircleDashed, className: "bg-slate-100 text-slate-600", label: "Unavailable" },
  FAILED: { icon: XCircle, className: "bg-red-50 text-red-700", label: "Failed" },
  PENDING: { icon: CircleDashed, className: "bg-amber-50 text-amber-700", label: "Pending" }
};

const verificationRules: Array<{ rule: string; method: string; type: "deterministic" | "ai-assisted" | "external"; status: Status }> = [
  { rule: "R-001 Turnover", method: "OCR extraction → Python arithmetic comparison", type: "deterministic", status: "PASS" },
  { rule: "R-002 GST validity", method: "OCR extraction → GST sandbox API → identity match", type: "external", status: "PASS" },
  { rule: "R-003 MSME / Udyam", method: "OCR extraction → Udyam adapter (currently mock)", type: "external", status: "REVIEW" },
  { rule: "R-004 Local content", method: "NLI / VLM contextual evidence analysis", type: "ai-assisted", status: "REVIEW" },
  { rule: "R-005 OEM authorization", method: "OCR extraction → entity name match → deterministic", type: "deterministic", status: "PASS" },
  { rule: "R-006 Debarment", method: "Identity normalization → CPPP fixture query", type: "external", status: "PASS" },
  { rule: "R-007 Document completeness", method: "Document classifier → count check", type: "deterministic", status: "PASS" }
];

export default function VerificationPage() {
  const connected = connectors.filter((c) => c.state === "CONNECTED").length;
  const unavailable = connectors.filter((c) => c.state === "UNAVAILABLE" || c.state === "PENDING").length;

  return (
    <AppShell>
      <PageHeader
        eyebrow="External verification"
        title="Verification Center"
        description="Monitor connector health, verification sources and the decision impact of each external adapter."
        action={
          <button className="btn btn-secondary">
            <RefreshCw size={16} />
            Refresh connectors
          </button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Total connectors" value={String(connectors.length)} detail="Verification adapters" icon={Database} />
        <MetricCard label="Connected" value={String(connected)} detail="Live or fixture-backed" icon={Globe} tone="teal" />
        <MetricCard label="Unavailable" value={String(unavailable)} detail="Mock adapters in use" icon={AlertTriangle} tone="amber" />
        <MetricCard label="Decision policy" value="Safe" detail="UNAVAILABLE → REVIEW" icon={ShieldCheck} tone="teal" />
      </div>

      <div className="mt-6 rounded-xl border border-cyan-100 bg-cyan-50 p-4 text-sm leading-6 text-cyan-950">
        <strong>Critical SIH26100 principle:</strong> when an external verification connector is unavailable, the rule outcome becomes
        <strong> REVIEW</strong>, never <strong>FAIL</strong>. AI confidence cannot override a deterministic rule failure. Numeric and date comparisons are always deterministic.
      </div>

      <div className="mt-6 panel overflow-hidden">
        <div className="border-b border-line p-5">
          <p className="section-title">Adapter status</p>
          <h2 className="mt-1 text-lg font-semibold">VerificationAdapter connectors</h2>
        </div>
        <div className="divide-y divide-line">
          {connectors.map((connector) => {
            const config = stateConfig[connector.state];
            const StateIcon = config.icon;
            return (
              <div key={connector.name} className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex items-start gap-4">
                  <div className={`rounded-lg p-2.5 ${config.className}`}>
                    <Database size={18} />
                  </div>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{connector.name}</h3>
                      <span className={`status-badge ${config.className}`}>
                        <StateIcon size={13} />
                        {config.label}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-slate-600">{connector.description}</p>
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                      <span>Source: {connector.source}</span>
                      <span>Last check: {connector.lastCheck}</span>
                    </div>
                  </div>
                </div>
                <div className="shrink-0 rounded-lg bg-slate-50 px-4 py-2 text-xs">
                  <p className="font-semibold text-slate-700">Decision impact</p>
                  <p className="mt-1 text-slate-600">{connector.decisionImpact}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-6 panel overflow-hidden">
        <div className="border-b border-line p-5">
          <p className="section-title">Verification methods</p>
          <h2 className="mt-1 text-lg font-semibold">Rule verification type matrix</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table min-w-[700px]">
            <thead>
              <tr>
                <th>Rule</th>
                <th>Verification method</th>
                <th>Type</th>
                <th>Demo status</th>
              </tr>
            </thead>
            <tbody>
              {verificationRules.map((item) => (
                <tr key={item.rule}>
                  <td className="font-semibold">{item.rule}</td>
                  <td className="text-slate-600">{item.method}</td>
                  <td>
                    <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${
                      item.type === "deterministic" ? "bg-emerald-50 text-emerald-700" :
                      item.type === "external" ? "bg-cyan-50 text-cyan-700" :
                      "bg-purple-50 text-purple-700"
                    }`}>
                      {item.type === "deterministic" ? "Deterministic" :
                       item.type === "external" ? "External API" :
                       "AI-assisted"}
                    </span>
                  </td>
                  <td><StatusBadge status={item.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
