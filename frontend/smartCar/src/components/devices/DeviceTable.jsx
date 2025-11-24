import React from "react";
import Card from "../ui/Card";
import DeviceStatusDot from "./DeviceStatusDot";

export default function DeviceTable({ devices }) {
  return (
    <Card className="rounded-2xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50">
            <tr className="text-left text-neutral-600 border-b border-neutral-200">
              <Th>Device ID</Th>
              <Th>Type</Th>
              <Th>Model</Th>
              <Th>Firmware</Th>
              <Th>Connected Car</Th>
              <Th>Signal (RSSI)</Th>
              <Th>Last Seen</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d, i) => (
              <tr
                key={d.id}
                className={`border-b border-neutral-100 ${
                  i % 2 ? "bg-white" : "bg-neutral-50/40"
                }`}
              >
                <Td className="font-medium">{d.id}</Td>
                <Td>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs ${typeTone(
                      d.type
                    )}`}
                  >
                    {d.type}
                  </span>
                </Td>
                <Td>{d.model}</Td>
                <Td>
                  {d.firmware}
                  {d.outdated && (
                    <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                      update
                    </span>
                  )}
                </Td>
                <Td>{d.carId}</Td>
                <Td>{d.rssi ?? "—"}</Td>
                <Td className="whitespace-nowrap">
                  {new Date(d.lastSeen).toLocaleString()}
                </Td>
                <Td>
                  <span className="inline-flex items-center gap-2">
                    <DeviceStatusDot status={d.status} />
                    <span
                      className={
                        d.status === "Online"
                          ? "text-emerald-700"
                          : "text-red-600"
                      }
                    >
                      {d.status}
                    </span>
                  </span>
                </Td>
              </tr>
            ))}
            {devices.length === 0 && (
              <tr>
                <td colSpan={8} className="py-10 text-center text-neutral-500">
                  No devices match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function Th({ children }) {
  return (
    <th className="px-3 py-3 text-xs uppercase tracking-wide">{children}</th>
  );
}
function Td({ children, className = "" }) {
  return <td className={`px-3 py-3 ${className}`}>{children}</td>;
}
function typeTone(t) {
  if (t === "Microphone") return "bg-blue-100 text-blue-700";
  if (t === "Camera") return "bg-violet-100 text-violet-700";
  return "bg-neutral-100 text-neutral-700";
}
