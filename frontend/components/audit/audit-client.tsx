"use client";
import { useState } from "react";
import type { AuditEvent } from "@/lib/types";
import { exportToCSV } from "@/lib/export";
import { AuditTimeline } from "./audit-timeline";
export function AuditClient({ events }: { events: AuditEvent[] }) {
  const [search, setSearch] = useState("");
  const [actor, setActor] = useState("");
  const [result, setResult] = useState("");
  const filtered = events.filter(e => (!actor || e.actor === actor) && (!result || e.result === result) && [e.action, e.document, e.rule, e.source, e.hash].some(value => value?.toLowerCase().includes(search.toLowerCase())));
  return <section className="panel p-5"><div className="mb-5 flex flex-wrap items-end gap-3"><label className="text-sm">Search events<input value={search} onChange={e => setSearch(e.target.value)} className="mt-1 block rounded border border-line p-2"/></label><label className="text-sm">Actor<select className="mt-1 block rounded border border-line p-2" value={actor} onChange={e => setActor(e.target.value)}><option value="">All actors</option>{Array.from(new Set(events.map(e => e.actor))).sort().map(a => <option key={a}>{a}</option>)}</select></label><label className="text-sm">Result<select className="mt-1 block rounded border border-line p-2" value={result} onChange={e => setResult(e.target.value)}><option value="">All results</option>{Array.from(new Set(events.map(e => e.result).filter((r): r is string => !!r))).sort().map(r => <option key={r}>{r}</option>)}</select></label><button className="btn btn-secondary" disabled={!filtered.length} onClick={() => exportToCSV("audit-events.csv", filtered.map(e => ({ ...e })))}>Export filtered CSV</button></div><p className="mb-4 text-sm muted">{filtered.length} of {events.length} recorded events</p><AuditTimeline events={filtered}/></section>;
}
