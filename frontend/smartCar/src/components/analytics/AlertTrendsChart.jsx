import React from "react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";

// Nice, unobtrusive tooltip
function Tt({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="rounded-xl border border-neutral-200 bg-white px-3 py-2 text-xs shadow-sm">
      <div className="font-medium mb-1">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex justify-between gap-6">
          <span>{p.dataKey}</span>
          <span className="font-medium">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function AlertTrendsChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gSafety" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.35}/>
            <stop offset="100%" stopColor="#f59e0b" stopOpacity={0}/>
          </linearGradient>
          <linearGradient id="gEmergency" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3}/>
            <stop offset="100%" stopColor="#ef4444" stopOpacity={0}/>
          </linearGradient>
          <linearGradient id="gAnomaly" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.25}/>
            <stop offset="100%" stopColor="#6366f1" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#eee" vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip content={<Tt />} />
        <Area type="monotone" dataKey="Safety" stroke="#f59e0b" fill="url(#gSafety)" strokeWidth={2} />
        <Area type="monotone" dataKey="Emergency" stroke="#ef4444" fill="url(#gEmergency)" strokeWidth={2} />
        <Area type="monotone" dataKey="Anomaly" stroke="#6366f1" fill="url(#gAnomaly)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
