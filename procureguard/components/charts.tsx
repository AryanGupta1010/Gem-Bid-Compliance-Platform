"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

const compliance = [
  { name: "TechNova", pass: 7, review: 0, fail: 0 },
  { name: "Apex", pass: 1, review: 1, fail: 5 },
  { name: "MedCore", pass: 2, review: 5, fail: 0 }
];

const risk = [
  { name: "Low", value: 1, color: "#18804f" },
  { name: "Medium", value: 1, color: "#c77719" },
  { name: "High", value: 1, color: "#bd3a3a" }
];

export function ComplianceChart() {
  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={compliance} margin={{ left: -20, right: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5ecef" />
          <XAxis dataKey="name" fontSize={12} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} fontSize={12} axisLine={false} tickLine={false} />
          <Tooltip />
          <Bar dataKey="pass" stackId="a" fill="#18804f" name="Pass" />
          <Bar dataKey="review" stackId="a" fill="#c77719" name="Review" />
          <Bar dataKey="fail" stackId="a" fill="#bd3a3a" name="Fail" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RiskChart() {
  return (
    <div className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={risk} dataKey="value" nameKey="name" innerRadius={52} outerRadius={75} paddingAngle={4}>
            {risk.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
