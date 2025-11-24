import React from "react";
import { RefreshCw, Search } from "lucide-react";

export default function CarsToolbar({
  status,
  onStatusChange,
  city,
  onCityChange,
  cities,
  query,
  onQueryChange,
  onRefresh,
}) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      {/* Left: status + city */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="text-sm font-medium">Status</div>
        <Segmented
          value={status}
          onChange={onStatusChange}
          options={["All", "Active", "Idle"]}
        />
        <div className="text-sm font-medium ml-2">City</div>
        <select
          className="input min-w-[140px]"
          value={city}
          onChange={(e) => onCityChange(e.target.value)}
        >
          {cities.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* Right: search + refresh */}
      <div className="flex items-center gap-2  rounded-lg border-2 border-gray-200">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
          <input
            className="input pl-9 w-[260px]"
            placeholder="Search by car, driver, city..."
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
          />
        </div>
        <button className="btn-secondary" onClick={onRefresh} title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function Segmented({ value, onChange, options }) {
  return (
    <div className="inline-flex rounded-xl border border-neutral-200 bg-white p-1">
      {options.map((opt) => {
        const active = value === opt;
        return (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={`px-3 py-1.5 rounded-lg text-sm ${
              active ? "bg-neutral-900 text-white" : "text-neutral-700 hover:bg-neutral-100"
            }`}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}
