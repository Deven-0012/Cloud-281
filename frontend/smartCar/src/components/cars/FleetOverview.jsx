import React, { useState, useEffect } from "react";
import axios from "axios";
import Card from "../ui/Card";
import CarOverviewCard from "./CarOverviewCard";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

export default function FleetOverview() {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVehicles();
    const interval = setInterval(fetchVehicles, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchVehicles = async () => {
    try {
      const response = await axios.get(`${API_URL}/v1/vehicles`);
      
      const transformed = response.data.vehicles.slice(0, 3).map(vehicle => ({
        id: vehicle.vehicle_id,
        model: `${vehicle.make || ''} ${vehicle.model || ''}`.trim() || 'Unknown',
        status: vehicle.status || 'active',
        alertCount: vehicle.alert_count || 0,
        newAlertCount: vehicle.new_alert_count || 0
      }));
      
      setVehicles(transformed);
    } catch (error) {
      console.error('Error fetching vehicles:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-medium text-lg">Fleet Overview</h2>
        <a href="/cars" className="text-sm text-blue-600 hover:underline">
          View All Cars →
        </a>
      </div>
      {loading ? (
        <div className="text-center text-neutral-500 py-4">Loading vehicles...</div>
      ) : vehicles.length === 0 ? (
        <div className="text-center text-neutral-500 py-4">No vehicles found</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vehicles.map((car) => (
            <CarOverviewCard key={car.id} car={car} />
          ))}
        </div>
      )}
    </section>
  );
}
