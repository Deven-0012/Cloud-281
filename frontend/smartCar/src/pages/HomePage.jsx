// import React, { useState, useEffect } from "react";
// import { Car, AlertTriangle, Plug, Cog } from "lucide-react";
// import axios from "axios";
// import StatCard from "../components/ui/StatCard";
// import AlertsFeed from "../components/feeds/AlertsFeed";
// import MapPreview from "../components/maps/MapPreview";
// import FleetOverview from "../components/cars/FleetOverview";
// import { useAuth } from "../contexts/AuthContext";
// import { API_URL } from "../utils/api";

// export default function HomePage() {
//   const { user } = useAuth();
//   const [stats, setStats] = useState({
//     connectedCars: { total: 0, online: 0, offline: 0 },
//     activeAlerts: { total: 0, emergency: 0, safety: 0, anomaly: 0 },
//     priorityAlerts: { high: 0, medium: 0, low: 0 },
//     devices: { total: 0, mic: 0, camera: 0, other: 0 },
//     modelHealth: { accuracy: 0, model: 'YAMNet' }
//   });
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     fetchDashboardData();
//     // Refresh every 5 seconds for real-time updates
//     const interval = setInterval(fetchDashboardData, 5000);
//     return () => clearInterval(interval);
//   }, []);

//   const fetchDashboardData = async () => {
//     try {
//       const response = await axios.get(`${API_URL}/v1/dashboard/stats`);
//       const data = response.data;

//       setStats({
//         connectedCars: {
//           total: data.connectedCars || 0,
//           online: data.onlineCars || 0,
//           offline: data.offlineCars || 0
//         },
//         activeAlerts: {
//           total: data.activeAlerts || 0,
//           emergency: data.emergencyAlerts || 0,
//           safety: data.safetyAlerts || 0,
//           anomaly: data.anomalyAlerts || 0
//         },
//         priorityAlerts: {
//           high: data.highPriorityAlerts || 0,
//           medium: data.mediumPriorityAlerts || 0,
//           low: data.lowPriorityAlerts || 0
//         },
//         devices: {
//           total: data.iotDevices || 0,
//           mic: data.microphones || 0,
//           camera: data.cameras || 0,
//           other: (data.iotDevices || 0) - (data.microphones || 0) - (data.cameras || 0)
//         },
//         modelHealth: {
//           accuracy: 95, // Could be fetched from API if available
//           model: 'YAMNet'
//         }
//       });
//     } catch (error) {
//       console.error('Error fetching dashboard stats:', error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   if (loading) {
//     return (
//       <div className="flex items-center justify-center py-12">
//         <div className="text-neutral-600">Loading dashboard...</div>
//       </div>
//     );
//   }

//   return (
//     <div className="space-y-8">
//       <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
//         <StatCard
//           title="Connected Cars"
//           value={stats.connectedCars.total}
//           sub={`Online: ${stats.connectedCars.online} · Offline: ${stats.connectedCars.offline}`}
//           icon={<Car className="w-5 h-5" />}
//         />
//         <StatCard
//           title="Active Alerts"
//           value={stats.activeAlerts.total}
//           sub={`High: ${stats.priorityAlerts.high} · Medium: ${stats.priorityAlerts.medium} · Low: ${stats.priorityAlerts.low}`}
//           icon={<AlertTriangle className="w-5 h-5" />}
//         />
//         {user?.role === 'admin' && (
//           <>
//             <StatCard
//               title="IoT Devices"
//               value={stats.devices.total}
//               sub={`Mic: ${stats.devices.mic} · Camera: ${stats.devices.camera} · Other: ${stats.devices.other}`}
//               icon={<Plug className="w-5 h-5" />}
//             />
//             <StatCard
//               title="Model Health"
//               value={`${stats.modelHealth.accuracy}%`}
//               sub={stats.modelHealth.model}
//               icon={<Cog className="w-5 h-5" />}
//             />
//           </>
//         )}
//       </div>

//       <FleetOverview />

//       <div className="grid lg:grid-cols-3 gap-6">
//         <div className="lg:col-span-2 space-y-6">
//           <div>
//             <div className="text-sm font-medium mb-2">Live Safety Feed</div>
//             <AlertsFeed />
//           </div>
//         </div>
//         <div>
//           <MapPreview />
//         </div>
//       </div>
//     </div>
//   );
// }

// HomePage.jsx
import React, { useState, useEffect } from "react";
import { Car, AlertTriangle, Plug, Cog } from "lucide-react";
import axios from "axios";
import StatCard from "../components/ui/StatCard";
import AlertsFeed from "../components/feeds/AlertsFeed";
import MapPreview from "../components/maps/MapPreview";
import FleetOverview from "../components/cars/FleetOverview";
import { useAuth } from "../contexts/AuthContext";
import { API_URL } from "../utils/api";

export default function HomePage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    connectedCars: { total: 0, online: 0, offline: 0 },
    activeAlerts: { total: 0, emergency: 0, safety: 0, anomaly: 0 },
    priorityAlerts: { high: 0, medium: 0, low: 0 },
    devices: { total: 0, mic: 0, camera: 0, other: 0 },
    modelHealth: { accuracy: 0, model: "YAMNet" },
  });
  const [loading, setLoading] = useState(true);

  // ✅ hardcoded cars that should appear ONLY for admin
  const adminDemoCars = [
    {
      id: "CAR-A1234",
      status: "Active",
      driver: "Alice Johnson",
      location: "San Jose, CA",
      model: "Tesla Model S Plaid",
      lastUpdate: "2 min ago",
      latestAlert: {
        type: "Emergency",
        title: "Glass break detected near driver door",
      },
    },
    {
      id: "CAR-B5678",
      status: "Idle",
      driver: "Bob Martinez",
      location: "Mountain View, CA",
      model: "Tesla Model 3",
      lastUpdate: "5 min ago",
      latestAlert: null,
    },
    {
      id: "CAR-B624",
      status: "Active",
      driver: "Bob Brown",
      location: "Sunnyvale, CA",
      model: "Audi Q5",
      lastUpdate: "Just now",
      latestAlert: {
        type: "High priority",
        title: "Passenger Distress Sound",
      },
    },
  ];

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API_URL}/v1/dashboard/stats`);
      const data = response.data;

      setStats({
        connectedCars: {
          total: data.connectedCars || 0,
          online: data.onlineCars || 0,
          offline: data.offlineCars || 0,
        },
        activeAlerts: {
          total: data.activeAlerts || 0,
          emergency: data.emergencyAlerts || 0,
          safety: data.safetyAlerts || 0,
          anomaly: data.anomalyAlerts || 0,
        },
        priorityAlerts: {
          high: data.highPriorityAlerts || 0,
          medium: data.mediumPriorityAlerts || 0,
          low: data.lowPriorityAlerts || 0,
        },
        devices: {
          total: data.iotDevices || 0,
          mic: data.microphones || 0,
          camera: data.cameras || 0,
          other:
            (data.iotDevices || 0) -
            (data.microphones || 0) -
            (data.cameras || 0),
        },
        modelHealth: {
          accuracy: 95,
          model: "YAMNet",
        },
      });
    } catch (error) {
      console.error("Error fetching dashboard stats:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-neutral-600">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* top stats */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Connected Cars"
          value={stats.connectedCars.total}
          sub={`Online: ${stats.connectedCars.online} · Offline: ${stats.connectedCars.offline}`}
          icon={<Car className="w-5 h-5" />}
        />
        <StatCard
          title="Active Alerts"
          value={stats.activeAlerts.total}
          sub={`High: ${stats.priorityAlerts.high} · Medium: ${stats.priorityAlerts.medium} · Low: ${stats.priorityAlerts.low}`}
          icon={<AlertTriangle className="w-5 h-5" />}
        />
        {user?.role === "admin" && (
          <>
            <StatCard
              title="IoT Devices"
              value={stats.devices.total}
              sub={`Mic: ${stats.devices.mic} · Camera: ${stats.devices.camera} · Other: ${stats.devices.other}`}
              icon={<Plug className="w-5 h-5" />}
            />
            <StatCard
              title="Model Health"
              value={`${stats.modelHealth.accuracy}%`}
              sub={stats.modelHealth.model}
              icon={<Cog className="w-5 h-5" />}
            />
          </>
        )}
      </div>

      {/* ✅ SINGLE Fleet Overview section, same card style for all cars */}
      <FleetOverview extraCars={user?.role === "admin" ? adminDemoCars : []} />

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
