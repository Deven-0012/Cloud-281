import React, { useMemo, useState, useEffect } from "react";
import axios from "axios";
import CarsToolbar from "../components/cars/CarsToolbar";
import CarCard from "../components/cars/CarCard";
import { API_URL } from "../utils/api";

export default function Cars() {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("All");
  const [city, setCity] = useState("All");
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetchVehicles();
    // Refresh every 30 seconds
    const interval = setInterval(fetchVehicles, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchVehicles = async () => {
    try {
      const response = await axios.get(`${API_URL}/v1/vehicles`);
      
      // Transform API data to match component expectations
      const transformed = response.data.vehicles.map(vehicle => ({
        id: vehicle.vehicle_id,
        model: `${vehicle.make || ''} ${vehicle.model || ''}`.trim() || 'Unknown',
        status: vehicle.status || 'active',
        location: vehicle.last_alert_location ? 
          `${vehicle.last_alert_location.lat.toFixed(4)}, ${vehicle.last_alert_location.lng.toFixed(4)}` :
          'Location unknown',
        alertCount: vehicle.alert_count || 0,
        newAlertCount: vehicle.new_alert_count || 0,
        lastAlertLocation: vehicle.last_alert_location
      }));
      
      setVehicles(transformed);
    } catch (error) {
      console.error('Error fetching vehicles:', error);
    } finally {
      setLoading(false);
    }
  };

  const cities = useMemo(() => {
    const set = new Set();
    vehicles.forEach((c) => {
      if (c.location && c.location !== 'Location unknown') {
        // Extract city from coordinates (simplified)
        set.add('All');
      }
    });
    return ["All", ...Array.from(set).sort()];
  }, [vehicles]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return vehicles.filter((c) => {
      const statusOk = status === "All" || c.status === status;
      const cityOk = city === "All"; // Simplified - can enhance later
      const qOk =
        !q ||
        c.id.toLowerCase().includes(q) ||
        c.model.toLowerCase().includes(q) ||
        c.location.toLowerCase().includes(q);
      return statusOk && cityOk && qOk;
    });
  }, [vehicles, status, city, query]);

  if (loading) {
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
        <p className="text-sm text-neutral-600">
          View status, latest alerts, and take actions per vehicle.
        </p>
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
