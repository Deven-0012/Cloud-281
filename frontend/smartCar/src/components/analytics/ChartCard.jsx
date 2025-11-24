import React from "react";
import Card from "../ui/Card";

export default function ChartCard({ title, toolbar, className = "", children }) {
  return (
    <Card className={`rounded-2xl border border-neutral-200 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-medium">{title}</h2>
        {toolbar}
      </div>
      {/* Fixed height so ResponsiveContainer can size properly */}
      <div className="h-80">{children}</div>
    </Card>
  );
}
