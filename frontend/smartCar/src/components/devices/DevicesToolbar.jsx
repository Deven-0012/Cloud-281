import React from "react";
import { List, Grid3X3, Search, RefreshCcw } from "lucide-react";

export default function DevicesToolbar({
  view,
  onViewChange,
  status,
  onStatusChange,
  type,
  onTypeChange,
  sortBy,
  onSortByChange,
  query,
  onQueryChange,
  onRefresh,
}) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap items-center gap-3">
        <Segmented
          value={view}
          onChange={onViewChange}
          options={[
            {
              label: (
                <>
                  <List className="w-4 h-4" />{" "}
                  <span className="ml-1">Table</span>
                </>
              ),
              value: "table",
            },
            {
              label: (
                <>
                  <Grid3X3 className="w-4 h-4" />{" "}
                  <span className="ml-1">Grid</span>
                </>
              ),
              value: "grid",
            },
          ]}
        />
        <div className="text-sm font-medium ml-2">Status</div>
        <select
          className="input"
          value={status}
          onChange={(e) => onStatusChange(e.target.value)}
        >
          {["All", "Online", "Offline"].map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>

        <div className="text-sm font-medium ml-2">Type</div>
        <select
          className="input"
          value={type}
          onChange={(e) => onTypeChange(e.target.value)}
        >
          {["All", "Microphone", "Camera", "Other"].map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>

        <div className="text-sm font-medium ml-2">Sort</div>
        <select
          className="input"
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value)}
        >
          <option value="id">Device ID</option>
          <option value="car">Connected Car</option>
          <option value="type">Type</option>
          <option value="status">Status</option>
          <option value="rssi">Signal (RSSI)</option>
          <option value="lastSeen">Last Seen</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
          <input
            className="input pl-9 w-[260px]"
            placeholder="Search by id, car, model, firmware..."
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
          />
        </div>
        <button className="btn-secondary" onClick={onRefresh} title="Refresh">
          <RefreshCcw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function Segmented({ value, onChange, options }) {
  return (
    <div className="inline-flex rounded-xl border border-neutral-200 bg-white p-1">
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`px-3 py-1.5 rounded-lg text-sm ${
              active
                ? "bg-neutral-900 text-white"
                : "text-neutral-700 hover:bg-neutral-100"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
