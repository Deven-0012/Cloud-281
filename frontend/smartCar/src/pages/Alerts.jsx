import React, { useMemo, useState, useEffect } from "react";
import axios from "axios";
import AlertsFilter from "../components/alerts/AlertsFilter";
import AlertsMap from "../components/maps/AlertsMap";
import AlertsTable from "../components/alerts/AlertsTable";
import Card from "../components/ui/Card";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

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
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    type: "All",
    conf: "All",
    time: "All Time",
  });

  useEffect(() => {
    fetchAlerts();
    // Refresh every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleAlertDelete = (deletedAlertId) => {
    // Remove deleted alert from state
    setAlerts(alerts.filter(a => a.id !== deletedAlertId));
    // Optionally refresh the list
    fetchAlerts();
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API_URL}/v1/alerts`, {
        params: { limit: 100 }
      });
      
      // Transform API data to match component expectations
      // Map to: Emergency, High priority, Low risk (instead of Emergency, Safety, Anomaly)
      const transformed = response.data.alerts.map(alert => {
        let type;
        if (alert.alert_type === 'emergency') {
          type = 'Emergency';
        } else {
          // Map based on priority: high/critical severity = High priority, else = Low risk
          const priority = alert.priority || (alert.severity === 'critical' ? 'high' : 
                          alert.severity === 'high' ? 'high' : 
                          alert.severity === 'medium' ? 'medium' : 'low');
          type = (priority === 'high') ? 'High priority' : 'Low risk';
        }
        
        return {
          id: alert.alert_id,
          type: type,
          priority: alert.priority || (alert.severity === 'critical' ? 'high' : 
                  alert.severity === 'high' ? 'high' : 
                  alert.severity === 'medium' ? 'medium' : 'low'),
          severity: alert.severity,
          sound: alert.sound_label,
          confidence: alert.confidence || 0,
          ts: new Date(alert.created_at).getTime(),
          vehicle: alert.vehicle_id,
          vehicleId: alert.vehicle_id,  // Add both for compatibility
          location: alert.location,
          message: alert.message,
          status: alert.status
        };
      });
      
      setAlerts(transformed);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

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

    return alerts.filter(
      (a) =>
        (filters.type === "All" || a.type === filters.type) &&
        meetsConf(a.confidence) &&
        inRange(a.ts)
    );
  }, [alerts, filters]);

  const counts = useMemo(
    () => ({
      Emergency: filtered.filter((a) => a.type === "Emergency").length,
      "High priority": filtered.filter((a) => a.type === "High priority").length,
      "Low risk": filtered.filter((a) => a.type === "Low risk").length,
    }),
    [filtered]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-neutral-600">Loading alerts...</div>
      </div>
    );
  }

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
      <Pill tone="amber">High priority: {counts["High priority"]}</Pill>
      <Pill tone="blue">Low risk: {counts["Low risk"]}</Pill>
    </div>
    <AlertsMap alerts={filtered} />
  </div>
</div>


      <AlertsTable alerts={filtered} onDelete={handleAlertDelete} />
    </div>
  );
}
