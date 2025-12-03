import React, { useMemo, useState, useEffect } from "react";
import axios from "axios";
import CarsToolbar from "../components/cars/CarsToolbar";
import CarCard from "../components/cars/CarCard";
import { API_URL } from "../utils/api";
import { useAuth } from "../contexts/AuthContext";

export default function Cars() {
  const { user } = useAuth();

  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("All");
  const [city, setCity] = useState("All");
  const [query, setQuery] = useState("");

  // 🔹 Same three hard-coded demo cars you see on the admin dashboard
  const adminDemoCars = useMemo(
    () => [
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
        latestAlert: {
          type: "Low risk",
          title: "No unusual sounds detected",
        },
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
    ],
    []
  );

  useEffect(() => {
    fetchVehicles();
    // Refresh every 30 seconds
    const interval = setInterval(fetchVehicles, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchVehicles = async () => {
    try {
      const response = await axios.get(`${API_URL}/v1/vehicles`);

      const transformed = (response.data.vehicles || []).map((vehicle) => {
        // 🔹 Clean / default model (BMW X5 if missing/unknown)
        const rawMake = (vehicle.make || "").trim();
        const rawModel = (vehicle.model || "").trim();

        const makeClean =
          !rawMake ||
          rawMake.toLowerCase() === "unknown" ||
          rawMake.toLowerCase() === "none"
            ? "BMW"
            : rawMake;

        const modelClean =
          !rawModel ||
          rawModel.toLowerCase() === "unknown" ||
          rawModel.toLowerCase() === "none"
            ? "X5"
            : rawModel;

        const model = `${makeClean} ${modelClean}`;

        // 🔹 Clean / default location (San Jose, CA if nothing else)
        let location = "San Jose, CA";
        if (vehicle.location) {
          // if backend already saves a nice string
          location = vehicle.location;
        } else if (vehicle.last_alert_location) {
          // fallback to coordinates
          location = `${vehicle.last_alert_location.lat.toFixed(
            4
          )}, ${vehicle.last_alert_location.lng.toFixed(4)}`;
        }

        // 🔹 Default driver
        const driver =
          vehicle.owner_name ||
          vehicle.owner ||
          vehicle.driver_name ||
          "John Doe";

        // 🔹 Default last update
        const lastUpdate = vehicle.updated_at
          ? new Date(vehicle.updated_at).toLocaleString()
          : "Just now";

        return {
          id: vehicle.vehicle_id,
          model,
          status: vehicle.status || "Active",
          location,
          driver,
          lastUpdate,
          alertCount: vehicle.alert_count || 0,
          newAlertCount: vehicle.new_alert_count || 0,
          lastAlertLocation: vehicle.last_alert_location,
          // latestAlert: could be wired later if backend exposes it
        };
      });

      setVehicles(transformed);
    } catch (error) {
      console.error("Error fetching vehicles:", error);
    } finally {
      setLoading(false);
    }
  };

  // 🔹 If admin → show demo cars + real cars
  //    If user  → only real cars
  const allVehicles = useMemo(
    () => (user?.role === "admin" ? [...adminDemoCars, ...vehicles] : vehicles),
    [user?.role, adminDemoCars, vehicles]
  );

  const cities = useMemo(() => {
    const set = new Set();
    allVehicles.forEach((c) => {
      if (c.location && c.location !== "Location unknown") {
        // In future you can parse true city names; for now just "All"
        set.add("All");
      }
    });
    return ["All", ...Array.from(set).sort()];
  }, [allVehicles]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return allVehicles.filter((c) => {
      const statusOk =
        status === "All" ||
        c.status.toLowerCase() === status.toLowerCase() ||
        (status === "Active" && c.status.toLowerCase() === "active") ||
        (status === "Inactive" && c.status.toLowerCase() !== "active");

      const cityOk = city === "All"; // still simplified
      const qOk =
        !q ||
        c.id.toLowerCase().includes(q) ||
        (c.model || "").toLowerCase().includes(q) ||
        (c.location || "").toLowerCase().includes(q);

      return statusOk && cityOk && qOk;
    });
  }, [allVehicles, status, city, query]);

  if (loading && vehicles.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-neutral-600">Loading vehicles...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-xl font-semibold">Car Monitoring & Control</h1>
      </div>

      <CarsToolbar
        status={status}
        onStatusChange={setStatus}
        city={city}
        onCityChange={setCity}
        cities={cities}
        query={query}
        onQueryChange={setQuery}
        onRefresh={fetchVehicles}
      />

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((car) => (
          <CarCard key={car.id} car={car} />
        ))}
        {filtered.length === 0 && (
          <div className="col-span-full text-center text-neutral-500 py-16">
            No cars match your filters.
          </div>
        )}
      </div>
    </div>
  );
}
