import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Legend, Tooltip } from "recharts";

const COLORS = ["#10b981", "#ef4444"]; // Online, Offline

export default function FleetStatusDonut({ data }) {
  const pieData = [
    { name: "Online", value: data.online },
    { name: "Offline", value: data.offline },
  ];
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={pieData}
          dataKey="value"
          nameKey="name"
          innerRadius={70}
          outerRadius={100}
          paddingAngle={2}
        >
          {pieData.map((entry, idx) => (
            <Cell key={entry.name} fill={COLORS[idx % COLORS.length]} />
          ))}
        </Pie>
        <Legend verticalAlign="bottom" height={24} />
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}
