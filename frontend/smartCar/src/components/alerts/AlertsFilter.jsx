import React from "react";
import Card from "../ui/Card";

export default function AlertsFilter({ value, onChange, onReset }) {
  const set = (k, v) => onChange({ ...value, [k]: v });
  return (
    <Card className="rounded-2xl">
      <div className="font-medium mb-3">Filters</div>
      <div className="space-y-3">
        <LabeledSelect
          label="Sound Type"
          value={value.type}
          onChange={(v) => set("type", v)}
          options={["All", "Emergency", "High priority", "Low risk"]}
        />
        <LabeledSelect
          label="Confidence"
          value={value.conf}
          onChange={(v) => set("conf", v)}
          options={["All", "≥50%", "≥70%", "≥90%"]}
        />
        <LabeledSelect
          label="Time Range"
          value={value.time}
          onChange={(v) => set("time", v)}
          options={["All Time", "Last 15 Min", "Last Hour", "Today"]}
        />
        <button className="btn-secondary w-full" onClick={onReset}>
          ✕ Reset
        </button>
      </div>
    </Card>
  );
}

function LabeledSelect({ label, value, onChange, options }) {
  return (
    <label className="block">
      <div className="text-sm text-neutral-600 mb-1">{label}</div>
      <select
        className="input w-full"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((o) => (
          <option key={o}>{o}</option>
        ))}
      </select>
    </label>
  );
}
