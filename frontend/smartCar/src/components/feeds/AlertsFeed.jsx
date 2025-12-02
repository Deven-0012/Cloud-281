import React, { useMemo, useState, useEffect } from "react";
import axios from "axios";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import Tabs from "../ui/Tabs";
import { MapPin } from "lucide-react";
import { fmtTime } from "../../utils/format";
import { API_URL } from "../../utils/api";

export default function AlertsFeed() {
  const [filter, setFilter] = useState("All");
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API_URL}/v1/alerts`, {
        params: { limit: 10 }
      });
      
      const transformed = response.data.alerts.map(alert => {
        let type;
        if (alert.alert_type === 'emergency') {
          type = 'Emergency';
        } else {
          const priority = alert.priority || (alert.severity === 'critical' ? 'high' : 
                          alert.severity === 'high' ? 'high' : 
                          alert.severity === 'medium' ? 'medium' : 'low');
          type = (priority === 'high') ? 'High priority' : 'Low risk';
        }
        
        return {
          id: alert.alert_id,
          type: type,
          vehicleId: alert.vehicle_id,
          title: alert.sound_label || 'Unknown sound',
          ts: new Date(alert.created_at).getTime(),
          confidence: alert.confidence || 0
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
    return alerts.filter((a) => filter === "All" || a.type === filter);
  }, [alerts, filter]);

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
          options={["All", "Emergency", "High priority", "Low risk"]}
        />
      </div>

      <div className="divide-y divide-neutral-200">
        {loading ? (
          <div className="py-3 text-center text-neutral-500">Loading alerts...</div>
        ) : filtered.length === 0 ? (
          <div className="py-3 text-center text-neutral-500">No alerts found</div>
        ) : (
          filtered.map((a) => (
          <div key={a.id} className="py-3 flex items-start gap-3">
            <div className="w-28 flex flex-col gap-1">
              <Badge
                tone={
                  a.type === "Emergency"
                    ? "red"
                    : a.type === "High priority"
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
        ))
        )}
      </div>
    </Card>
  );
}
