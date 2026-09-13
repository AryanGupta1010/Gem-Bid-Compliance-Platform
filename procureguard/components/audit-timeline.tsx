import { ShieldCheck } from "lucide-react";
import { AuditEvent, Status } from "@/lib/types";
import { StatusBadge } from "./status-badge";

export function AuditTimeline({ events, compact = false }: { events: AuditEvent[], compact?: boolean }) {
  const displayEvents = compact ? events.slice(0, 4) : events;
  
  if (displayEvents.length === 0) {
    return (
      <div className="text-center text-sm text-slate-500 py-6">
        No audit events recorded yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {displayEvents.map((event, index) => (
        <div key={`${event.id}-${index}`} className="relative flex gap-3">
          {index < displayEvents.length - 1 && <div className="absolute left-4 top-8 h-full w-px bg-slate-200" />}
          <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-teal/20 bg-cyan-50 text-teal">
            <ShieldCheck size={15} />
          </div>
          <div className="min-w-0 flex-1 rounded-lg border border-line bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold">{event.action}</p>
              <span className="text-[11px] text-slate-500">
                {new Date(event.time).toLocaleString(undefined, {
                  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
                })}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-600">{event.actor} {event.document ? `· ${event.document}` : ""}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
              {event.rule && <span className="rounded bg-slate-100 px-2 py-1">Rule: {event.rule}</span>}
              {event.result && (
                ["PASS", "FAIL", "REVIEW"].includes(event.result) 
                  ? <StatusBadge status={event.result as Status} /> 
                  : <span className="rounded bg-slate-100 px-2 py-1">{event.result}</span>
              )}
              {event.hash && <span className="font-mono text-slate-500">hash {event.hash.substring(0, 12)}...</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
