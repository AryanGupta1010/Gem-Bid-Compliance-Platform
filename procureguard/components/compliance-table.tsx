import Link from "next/link";
import { Bidder } from "@/lib/types";
import { StatusBadge, RiskBadge } from "./status-badge";

export function ComplianceTable({ bidders }: { bidders: Bidder[] }) {
  if (!bidders || bidders.length === 0) {
    return (
      <div className="panel flex min-h-48 items-center justify-center p-8 text-center text-slate-500">
        No bids available to display compliance matrix.
      </div>
    );
  }

  // Assuming all bidders have the same rules, we use the first bidder's rules for the rows
  const rules = bidders[0].rules || [];

  return (
    <div className="panel overflow-hidden">
      <div className="border-b border-line p-5">
        <p className="section-title">Rule matrix</p>
        <h2 className="mt-1 text-lg font-semibold">Tender Bidders</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="data-table min-w-[850px]">
          <thead>
            <tr>
              <th>Rule</th>
              {bidders.map((bidder) => <th key={bidder.id}>{bidder.bidder_name.split(" ")[0]}</th>)}
            </tr>
          </thead>
          <tbody>
            {rules.map((rule, index) => (
              <tr key={rule.id || index}>
                <td>
                  <p className="font-semibold">{rule.rule_name}</p>
                  <p className="mt-1 text-xs text-slate-500">{rule.rule_id}</p>
                </td>
                {bidders.map((bidder) => {
                  const bidderRule = bidder.rules && bidder.rules[index];
                  const result = bidderRule ? bidderRule.result : "UNAVAILABLE";
                  return <td key={bidder.id}><StatusBadge status={result} /></td>;
                })}
              </tr>
            ))}
            <tr className="bg-slate-50">
              <td className="font-semibold">Overall</td>
              {bidders.map((bidder) => (
                <td key={bidder.id}>
                  <Link href={`/evaluations/${bidder.id}`} className="flex flex-col gap-2">
                    <span className="text-lg font-semibold">{bidder.score}/100</span>
                    <div className="flex gap-2"><RiskBadge risk={bidder.risk} /><StatusBadge status={bidder.status} /></div>
                  </Link>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

