import React, { useMemo, useState } from "react";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import Tabs from "../ui/Tabs";
import { MapPin } from "lucide-react";
import { fmtTime } from "../../utils/format";
import { mockAlerts } from "../../data/mockData";

export default function AlertsFeed() {
  const [filter, setFilter] = useState("All");

  const filtered = useMemo(() => {
    return mockAlerts.filter((a) => filter === "All" || a.type === filter);
  }, [filter]);

  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="font-medium">Alerts</h2>
          <div className="text-xs text-neutral-500">
            Newest AI detections across your fleet
          </div>
        </div>
        <Tabs
          value={filter}
          onChange={setFilter}
          options={["All", "Emergency", "Safety", "Anomaly"]}
        />
      </div>

      <div className="divide-y divide-neutral-200">
        {filtered.map((a) => (
          <div key={a.id} className="py-3 flex items-start gap-3">
            <div className="w-28 flex flex-col gap-1">
              <Badge
                tone={
                  a.type === "Emergency"
                    ? "red"
                    : a.type === "Safety"
                    ? "amber"
                    : "violet"
                }
              >
                {a.type}
              </Badge>
              <div className="text-[11px] text-neutral-500">
                #{a.id} · {a.vehicleId}
              </div>
            </div>
            <div className="flex-1">
              <div className="font-medium">{a.title}</div>
              <div className="text-xs text-neutral-500">{fmtTime(a.ts)}</div>
              <div className="mt-2 h-2 rounded-full bg-neutral-100">
                <div
                  className="h-2 rounded-full bg-neutral-900"
                  style={{ width: `${Math.round(a.confidence * 100)}%` }}
                />
              </div>
            </div>
            <button className="btn-secondary shrink-0">
              <MapPin className="w-4 h-4" /> Map
            </button>
          </div>
        ))}
      </div>
    </Card>
  );
}
