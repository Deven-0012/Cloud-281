import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import Card from "../components/ui/Card";
import Badge from "../components/ui/Badge";
import { fmtTime } from "../utils/format";
import { mockAlerts } from "../data/mockData";
import AlertLocationMap from "../components/maps/AlertLocationMap";

function InfoItem({ label, value }) {
  return (
    <div className="p-3 rounded-xl bg-neutral-50 border border-neutral-200">
      <div className="text-xs text-neutral-500">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}

export default function AlertDetails() {
  const { id } = useParams();
  const nav = useNavigate();
  const alert = mockAlerts.find((a) => String(a.id) === String(id));

  if (!alert) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <button className="btn-secondary" onClick={() => nav(-1)}>
            ← Back
          </button>
          <h1 className="text-xl font-semibold">Alert Not Found</h1>
        </div>
        <Card>We couldn't find alert #{id}. It may have been removed.</Card>
      </div>
    );
  }

  const tone =
    alert.type === "Emergency" ? "red" : alert.type === "High priority" ? "amber" : "blue";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <button className="btn-secondary" onClick={() => nav(-1)}>
          ← Back
        </button>
        <h1 className="text-xl font-semibold">Alert Details</h1>
        <Badge tone={tone}>{alert.type}</Badge>
        <span className="text-xs text-neutral-500">Status: Under Review</span>
      </div>

      {/* Content */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left column: info */}
        <Card className="lg:col-span-2">
          <h2 className="font-medium mb-3">Information</h2>

          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <InfoItem label="# Alert ID" value={`#${alert.id}`} />
            <InfoItem label="Timestamp" value={fmtTime(alert.ts)} />
            <InfoItem label="Sound Detected" value={alert.sound} />
            <InfoItem label="Vehicle ID" value={alert.vehicleId} />
            <InfoItem
              label="Confidence"
              value={`${Math.round(alert.confidence * 100)}%`}
            />
            <InfoItem
              label="Passenger Detected"
              value={alert.passengerDetected ? "Yes" : "No"}
            />
            <InfoItem
              label="Location (lat, lng)"
              value={`${alert.location.lat}, ${alert.location.lng}`}
            />
          </div>

          <div className="mt-4">
            <h3 className="font-medium mb-2">Notes / Description</h3>
            <div className="p-3 rounded-xl bg-neutral-50 border border-neutral-200 text-sm text-neutral-700">
              {alert.notes || "Detected unusual audio event. Model confidence high."}
            </div>
          </div>

          {/* Actions */}
          <div className="mt-5 flex flex-wrap gap-2">
            <button className="btn-primary">Acknowledge</button>
            <button className="btn-outline">Assign to Staff</button>
          </div>
        </Card>

        {/* Right column: map – now guaranteed visible */}
        <Card>
          <h2 className="font-medium mb-3">Alert Location</h2>
          <AlertLocationMap lat={alert.location.lat} lng={alert.location.lng} />
        </Card>
      </div>
    </div>
  );
}
