"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Search, Download } from "lucide-react";
import { Tender } from "@/lib/types";
import { exportToCSV } from "@/lib/export";

interface TendersClientProps {
  tenders: Tender[];
}

export function TendersClient({ tenders }: TendersClientProps) {
  const [search, setSearch] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const departments = Array.from(new Set(tenders.map(t => t.department)));

  const filteredTenders = tenders.filter(tender => {
    const matchesSearch = tender.title.toLowerCase().includes(search.toLowerCase()) || 
                          tender.id.toLowerCase().includes(search.toLowerCase());
    const matchesDepartment = departmentFilter === "ALL" || tender.department === departmentFilter;
    const matchesStatus = statusFilter === "ALL" || tender.status === statusFilter;
    
    return matchesSearch && matchesDepartment && matchesStatus;
  });

  const handleExport = () => {
    const data = filteredTenders.map(t => ({
      ID: t.id,
      Title: t.title,
      Department: t.department,
      Status: t.status,
      Budget: t.budget,
      Deadline: t.deadline,
      Published: t.published,
      BidsCount: t.bids?.length || 0
    }));
    exportToCSV("tenders_register.csv", data);
  };

  return (
    <div className="mt-6 panel overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-line p-5 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="section-title">Tender register</p>
          <h2 className="mt-1 text-lg font-semibold">All evaluation workspaces</h2>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <select 
            className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:border-teal"
            aria-label="Filter by department"
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
          >
            <option value="ALL">All Departments</option>
            {departments.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>

          <select 
            className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:border-teal"
            aria-label="Filter by tender status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Status</option>
            {Array.from(new Set(tenders.map(t => t.status))).sort().map(status => <option key={status} value={status}>{status}</option>)}
          </select>
          
          <div className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm text-slate-500 focus-within:border-teal">
            <Search size={15} />
            <input 
              type="text" 
              placeholder="Search register"
              aria-label="Search tender register"
              className="bg-transparent focus:outline-none w-32"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <button onClick={handleExport} className="btn bg-white border border-line hover:bg-slate-50">
            <Download size={16} /> Export
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="data-table min-w-[900px]">
          <thead>
            <tr>
              <th>Tender</th>
              <th>Department</th>
              <th>Published</th>
              <th>Deadline</th>
              <th>Budget</th>
              <th>Bids</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filteredTenders.map((item) => (
              <tr key={item.id} className="transition hover:bg-slate-50">
                <td>
                  <Link href={`/tenders/${encodeURIComponent(item.id)}`} className="block">
                    <p className="font-semibold">{item.title}</p>
                    <p className="mt-1 font-mono text-xs text-slate-500">{item.id}</p>
                  </Link>
                </td>
                <td>{item.department}</td>
                <td>{item.published}</td>
                <td>{item.deadline}</td>
                <td className="font-semibold">{item.budget}</td>
                <td>{item.bids?.length || 0}</td>
                <td>
                  <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-bold text-amber-700 uppercase">
                    {item.status}
                  </span>
                </td>
                <td>
                  <Link href={`/tenders/${encodeURIComponent(item.id)}`} className="text-teal">
                    <ArrowRight size={17} />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredTenders.length === 0 && (
          <div className="p-10 text-center text-slate-500">No tenders match your filters.</div>
        )}
      </div>
    </div>
  );
}
