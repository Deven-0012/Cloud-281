import React from "react";
import Card from "../ui/Card";
import { Info, ShieldAlert, CheckCircle2, AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";

export default function CarCard({ car }) {
  const statusTone =
    car.status === "Active"
      ? "bg-emerald-100 text-emerald-700"
      : "bg-neutral-100 text-neutral-700";

  const alert = car.latestAlert; // { type: 'Emergency'|'High priority'|'Low risk', title: string } or null

  const banner = (() => {
    if (!alert) {
      return (
        <Banner tone="green" icon={<CheckCircle2 className="w-4 h-4" />}>
          No unusual sounds detected
        </Banner>
      );
    }
    if (alert.type === "Emergency") {
      return (
        <Banner tone="red" icon={<ShieldAlert className="w-4 h-4" />}>
          <span className="font-medium">Emergency</span>
          <span className="ml-2 opacity-90">{alert.title}</span>
        </Banner>
      );
    }
    if (alert.type === "High priority") {
      return (
        <Banner tone="amber" icon={<AlertTriangle className="w-4 h-4" />}>
          <span className="font-medium">High priority</span>
          <span className="ml-2 opacity-90">{alert.title}</span>
        </Banner>
      );
    }
    return (
      <Banner tone="green" icon={<CheckCircle2 className="w-4 h-4" />}>
        <span className="font-medium">Low risk</span>
        <span className="ml-2 opacity-90">{alert.title}</span>
      </Banner>
    );
  })();

  return (
    <Card className="rounded-2xl border border-neutral-200 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="font-semibold tracking-wide">{car.id}</div>
        <span className={`px-2 py-0.5 rounded-full text-xs ${statusTone}`}>
          {car.status}
        </span>
      </div>

      <div className="mt-3 space-y-1 text-sm">
        <Row label="Driver" value={car.driver} />
        <Row label="Location" value={car.location} />
        <Row label="Model" value={car.model} />
        <Row label="Last update" value={car.lastUpdate} />
      </div>

      <div className="mt-3">{banner}</div>

      <div className="mt-3">
        <Link to={`/car/${car.id}`} className="btn-dark w-full inline-flex items-center justify-center">
          <Info className="w-4 h-4" /> <span className="ml-1">Details</span>
        </Link>
      </div>
    </Card>
  );
}

function Row({ label, value }) {
  return (
    <div>
      <span className="font-semibold">{label}:</span>{" "}
      <span className="text-neutral-700">{value}</span>
    </div>
  );
}

function Banner({ tone, icon, children }) {
  const palette = {
    red: "bg-red-50 text-red-700 border-red-200",
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    green: "bg-emerald-50 text-emerald-700 border-emerald-200",
  };
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm border ${palette[tone]}`}>
      {icon}
      <div className="truncate">{children}</div>
    </div>
  );
}
