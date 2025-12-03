import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Car, User, Cpu, AlertTriangle } from "lucide-react";
import Card from "../components/ui/Card";

export default function CarDetails() {
  const { id } = useParams(); // URL param: /car/:id
  const navigate = useNavigate();

  // Hard-coded car details
  const car = {
    id,
    name: "Tesla Model S",
    model: "Model S 2024",
    owner: "John Doe",
    location: "San Francisco, CA",
    vin: "5YJSA1E26JF123456",
    status: "Active",
    lastUpdate: "2 hours ago",
  };

  const devices = [
    { id: "DEV-001", type: "Microphone", status: "online", firmware: "v1.2.0" },
    { id: "DEV-002", type: "Camera", status: "offline", firmware: "v1.0.3" },
  ];

  const alerts = [
    {
      id: "ALT-001",
      type: "Emergency",
      sound: "Glass Break",
      severity: "critical",
      time: "2025-02-18 12:45 PM",
      status: "new",
    },
    {
      id: "ALT-002",
      type: "Mechanical",
      sound: "Engine Knock",
      severity: "high",
      time: "2025-02-16 04:20 PM",
      status: "acknowledged",
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center text-sm text-neutral-600 hover:text-neutral-900"
      >
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back
      </button>

      {/* Car Header */}
      <Card className="p-5 rounded-2xl shadow-sm border border-neutral-200">
        <div className="flex flex-col md:flex-row justify-between">
          <div>
            <h1 className="text-xl font-semibold">{car.name}</h1>
            <p className="text-neutral-600 mt-1">{car.model}</p>

            <div className="mt-2 text-sm space-y-1">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-neutral-500" />
                <span>{car.owner}</span>
              </div>
              <div className="flex items-center gap-2">
                <Car className="w-4 h-4 text-neutral-500" />
                <span>VIN: {car.vin}</span>
              </div>
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-neutral-500" />
                <span>Status: {car.status}</span>
              </div>
              <p className="text-neutral-500 text-xs">
                Last update: {car.lastUpdate}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Devices Section */}
      <Card className="p-5 rounded-2xl border shadow-sm">
        <h2 className="text-md font-semibold mb-3">Devices</h2>
        <table className="w-full text-sm">
          <thead className="bg-neutral-100 text-neutral-600 text-xs uppercase">
            <tr>
              <th className="px-3 py-2 text-left">ID</th>
              <th className="px-3 py-2 text-left">Type</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Firmware</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {devices.map((d) => (
              <tr key={d.id}>
                <td className="px-3 py-2 font-mono">{d.id}</td>
                <td className="px-3 py-2">{d.type}</td>
                <td className="px-3 py-2">{d.status}</td>
                <td className="px-3 py-2">{d.firmware}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Alerts Section */}
      <Card className="p-5 rounded-2xl border shadow-sm">
        <h2 className="text-md font-semibold mb-3">Alerts</h2>

        {alerts.map((a) => (
          <div
            key={a.id}
            className="flex items-center justify-between p-3 border rounded-xl mb-3"
          >
            <div>
              <p className="font-medium">
                {a.type} – {a.sound}
              </p>
              <p className="text-xs text-neutral-500">{a.time}</p>
            </div>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <span className="text-sm capitalize text-red-600">
                {a.severity}
              </span>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
