import React, { useMemo, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import ChartCard from "../components/analytics/ChartCard";
import AlertTrendsChart from "../components/analytics/AlertTrendsChart";
import FleetStatusDonut from "../components/analytics/FleetStatusDonut";
import SystemPerfChart from "../components/analytics/SystemPerfChart";
import SoundMixBar from "../components/analytics/SoundMixBar";
import { alertTrends, fleetStatus, systemPerf, soundMix } from "../data/mockData";

function Segmented({ value, onChange, options }) {
  return (
    <div className="inline-flex rounded-xl border border-neutral-200 bg-white p-1">
      {options.map((opt) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className={`px-3 py-1.5 rounded-lg text-sm ${
            value === opt ? "bg-neutral-900 text-white" : "text-neutral-700 hover:bg-neutral-100"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

export default function Analytics() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [view, setView] = useState("All"); // All | Emergency | Safety | Anomaly

  useEffect(() => {
    // Redirect owners away from Analytics page
    if (user && user.role !== 'admin') {
      navigate('/');
    }
  }, [user, navigate]);

  // Don't render if user is not admin
  if (!user || user.role !== 'admin') {
    return null;
  }

  const trends = useMemo(() => {
    if (view === "All") return alertTrends;
    // keep other keys but zero out non-selected so the scale stays consistent
    return alertTrends.map((d) => ({
      date: d.date,
      Emergency: view === "Emergency" ? d.Emergency : 0,
      Safety: view === "Safety" ? d.Safety : 0,
      Anomaly: view === "Anomaly" ? d.Anomaly : 0,
    }));
  }, [view]);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-xl font-semibold">Analytics</h1>
        <p className="text-sm text-neutral-600">Trends, fleet health, and model performance.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <ChartCard title="Alert Trends" className="lg:col-span-2" toolbar={
          <Segmented value={view} onChange={setView} options={["All", "Emergency", "Safety", "Anomaly"]} />
        }>
          <AlertTrendsChart data={trends} />
        </ChartCard>

        <ChartCard title="Fleet Status">
          <FleetStatusDonut data={fleetStatus} />
        </ChartCard>

        <ChartCard title="System Performance" className="lg:col-span-2">
          <SystemPerfChart data={systemPerf} />
        </ChartCard>

        <ChartCard title="Sound Classification Mix">
          <SoundMixBar data={soundMix} />
        </ChartCard>
      </div>
    </div>
  );
}
