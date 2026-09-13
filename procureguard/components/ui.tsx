import { LucideIcon } from "lucide-react";

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = "navy"
}: {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone?: "navy" | "teal" | "amber" | "red";
}) {
  const colors = {
    navy: "bg-slate-100 text-navy",
    teal: "bg-cyan-50 text-teal",
    amber: "bg-amber-50 text-amber-700",
    red: "bg-red-50 text-red-700"
  };

  return (
    <div className="panel p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 kpi-number">{value}</p>
          <p className="mt-1 text-xs muted">{detail}</p>
        </div>
        <div className={`rounded-lg p-2.5 ${colors[tone]}`}>
          <Icon size={19} />
        </div>
      </div>
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        {eyebrow && <p className="section-title mb-2">{eyebrow}</p>}
        <h1 className="page-title">{title}</h1>
        {description && <p className="mt-2 max-w-3xl text-sm muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="panel flex min-h-48 items-center justify-center p-8 text-center">
      <div>
        <p className="font-semibold">{title}</p>
        <p className="mt-1 text-sm muted">{description}</p>
      </div>
    </div>
  );
}
