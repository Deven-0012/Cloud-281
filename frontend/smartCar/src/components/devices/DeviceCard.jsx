import React from "react";
import Card from "../ui/Card";
import DeviceStatusDot from "./DeviceStatusDot";

export default function DeviceCard({ device }) {
  const badgeTone =
    device.status === "Online"
      ? "bg-emerald-100 text-emerald-700"
      : "bg-red-100 text-red-700";
  return (
    <Card className="rounded-2xl border border-neutral-200 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="font-semibold tracking-wide">{device.id}</div>
        <span className={`px-2 py-0.5 rounded-full text-xs ${badgeTone}`}>
          {device.status}
        </span>
      </div>
      <div className="mt-2 text-sm text-neutral-700">
        <div>
          <span className="font-semibold">Type:</span> {device.type}
        </div>
        <div>
          <span className="font-semibold">Model:</span> {device.model}
        </div>
        <div>
          <span className="font-semibold">Firmware:</span> {device.firmware}{" "}
          {device.outdated && (
            <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
              update
            </span>
          )}
        </div>
        <div>
          <span className="font-semibold">Connected:</span> {device.carId}
        </div>
        <div>
          <span className="font-semibold">Signal:</span> {device.rssi ?? "—"}
        </div>
        <div className="text-xs text-neutral-500 mt-1">
          Last seen: {new Date(device.lastSeen).toLocaleString()}
        </div>
      </div>
    </Card>
  );
}
