import React from "react";
import { Car, AlertTriangle, Plug, Cog } from "lucide-react";
import StatCard from "../components/ui/StatCard";
import AlertsFeed from "../components/feeds/AlertsFeed";
import MapPreview from "../components/maps/MapPreview";
import FleetOverview from "../components/cars/FleetOverview";
import { mockStats } from "../data/mockData";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Connected Cars"
          value={mockStats.connectedCars.total}
          sub={`Online: ${mockStats.connectedCars.online} · Offline: ${mockStats.connectedCars.offline}`}
          icon={<Car className="w-5 h-5" />}
        />
        <StatCard
          title="Active Alerts"
          value={mockStats.activeAlerts.total}
          sub={`Emergency: ${mockStats.activeAlerts.emergency} · Safety: ${mockStats.activeAlerts.safety} · Anomaly: ${mockStats.activeAlerts.anomaly}`}
          icon={<AlertTriangle className="w-5 h-5" />}
        />
        <StatCard
          title="IoT Devices"
          value={mockStats.devices.total}
          sub={`Mic: ${mockStats.devices.mic} · Camera: ${mockStats.devices.camera} · Other: ${mockStats.devices.other}`}
          icon={<Plug className="w-5 h-5" />}
        />
        <StatCard
          title="Model Health"
          value={`${mockStats.modelHealth.accuracy}%`}
          sub={mockStats.modelHealth.model}
          icon={<Cog className="w-5 h-5" />}
        />
      </div>

      <FleetOverview />

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div>
            <div className="text-sm font-medium mb-2">Live Safety Feed</div>
            <AlertsFeed />
          </div>
        </div>
        <div>
          <MapPreview />
        </div>
      </div>
    </div>
  );
}
