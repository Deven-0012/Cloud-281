import React from "react";
import Card from "../ui/Card";
import { AlertTriangle, Info } from "lucide-react";

export default function CarOverviewCard({ car }) {
  const statusTone =
    car.status === "Active"
      ? "bg-emerald-100 text-emerald-700"
      : "bg-neutral-100 text-neutral-600";
  return (
    <Card className="rounded-2xl border border-neutral-200 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="font-semibold tracking-wide">{car.id}</div>
        <span className={`px-2 py-0.5 rounded-full text-xs ${statusTone}`}>
          {car.status}
        </span>
      </div>

      <div className="mt-3 space-y-1 text-sm">
        <div>
          <span className="font-semibold">Driver:</span> {car.driver}
        </div>
        <div>
          <span className="font-semibold">Location:</span> {car.location}
        </div>
        <div>
          <span className="font-semibold">Model:</span> {car.model}
        </div>
        <div>
          <span className="font-semibold">Last update:</span> {car.lastUpdate}
        </div>
      </div>

      {/* alert chip */}
      {car.latestAlert && (
        <div className="mt-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5" /> {car.latestAlert.type}{" "}
            {car.latestAlert.title}
          </div>
        </div>
      )}

      <div className="mt-3">
        <button className="w-full btn-dark">
          <Info className="w-4 h-4" /> View Details
        </button>
      </div>
    </Card>
  );
}
