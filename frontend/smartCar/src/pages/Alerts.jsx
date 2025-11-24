import React, { useMemo, useState } from "react";
import AlertsFilter from "../components/alerts/AlertsFilter";
import AlertsMap from "../components/maps/AlertsMap";
import AlertsTable from "../components/alerts/AlertsTable";
import Card from "../components/ui/Card";
import { mockAlerts } from "../data/mockData";

function Pill({ tone = "red", children }) {
  const tones = {
    red: "bg-red-50 text-red-700 border-red-200",
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
  };
  return (
    <div className={`text-center py-2 rounded-xl border ${tones[tone]}`}>
      {children}
    </div>
  );
}

export default function Alerts() {
  const [filters, setFilters] = useState({
    type: "All",
    conf: "All",
    time: "All Time",
  });

  const filtered = useMemo(() => {
    const now = Date.now();

    const inRange = (ts) => {
      const t = new Date(ts).getTime();
      switch (filters.time) {
        case "Last 15 Min":
          return now - t <= 15 * 60 * 1000;
        case "Last Hour":
          return now - t <= 60 * 60 * 1000;
        case "Today": {
          const d = new Date();
          d.setHours(0, 0, 0, 0);
          return t >= d.getTime();
        }
        default:
          return true;
      }
    };

    const meetsConf = (c) => {
      const pct = c * 100;
      if (filters.conf === "≥90%") return pct >= 90;
      if (filters.conf === "≥70%") return pct >= 70;
      if (filters.conf === "≥50%") return pct >= 50;
      return true;
    };

    return mockAlerts.filter(
      (a) =>
        (filters.type === "All" || a.type === filters.type) &&
        meetsConf(a.confidence) &&
        inRange(a.ts)
    );
  }, [filters]);

  const counts = useMemo(
    () => ({
      Emergency: filtered.filter((a) => a.type === "Emergency").length,
      Safety: filtered.filter((a) => a.type === "Safety").length,
      Anomaly: filtered.filter((a) => a.type === "Anomaly").length,
    }),
    [filtered]
  );

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-xl font-semibold">Live Map</h1>
        <p className="text-sm text-neutral-600">
          Use filters to refine the feed. Click a pin for alert details.
        </p>
      </div>

      {/* Sidebar layout */}
      {/* <div className="grid lg:grid-cols-[320px,1fr] gap-6 items-start"> */}
      {/* <div className="grid grid-cols-[320px,1fr] gap-6 items-start">

        <AlertsFilter
          value={filters}
          onChange={setFilters}
          onReset={() =>
            setFilters({ type: "All", conf: "All", time: "All Time" })
          }
        />

        <div className="space-y-4">
          <div className="grid sm:grid-cols-3 gap-3">
            <Pill tone="red">Emergency: {counts.Emergency}</Pill>
            <Pill tone="amber">Safety: {counts.Safety}</Pill>
            <Pill tone="blue">Anomaly: {counts.Anomaly}</Pill>
          </div>

          <AlertsMap alerts={filtered} />
        </div>
      </div> */}

<div className="flex flex-col md:flex-row gap-6 items-start">
  {/* Left sidebar: Filters */}
  <div className="w-full md:w-[320px] md:shrink-0">
    <AlertsFilter
      value={filters}
      onChange={setFilters}
      onReset={() => setFilters({ type: "All", conf: "All", time: "All Time" })}
    />
  </div>

  {/* Right column: counters + map */}
  <div className="flex-1 space-y-4">
    <div className="grid sm:grid-cols-3 gap-3">
      <Pill tone="red">Emergency: {counts.Emergency}</Pill>
      <Pill tone="amber">Safety: {counts.Safety}</Pill>
      <Pill tone="blue">Anomaly: {counts.Anomaly}</Pill>
    </div>
    <AlertsMap alerts={filtered} />
  </div>
</div>


      <AlertsTable alerts={filtered} />
    </div>
  );
}
