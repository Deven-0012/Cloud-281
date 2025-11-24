import React from "react";
import Card from "./Card";

export default function StatCard({ title, value, sub, icon }) {
  return (
    <Card className="flex items-center gap-3">
      <div className="p-2 rounded-xl bg-neutral-900 text-white">{icon}</div>
      <div>
        <div className="text-sm text-neutral-500">{title}</div>
        <div className="text-2xl font-semibold">{value}</div>
        {sub && <div className="text-xs text-neutral-500">{sub}</div>}
      </div>
    </Card>
  );
}
