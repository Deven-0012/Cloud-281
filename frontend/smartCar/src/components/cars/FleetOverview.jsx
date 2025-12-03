import React, { useEffect, useState } from "react";
import axios from "axios";
import CarCard from "./CarCard";
import { Link } from "react-router-dom";
import { API_URL } from "../../utils/api";

export default function FleetOverview({ extraCars = [] }) {
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVehicles = async () => {
      try {
        const res = await axios.get(`${API_URL}/v1/vehicles`);

        const apiCars = (res.data.vehicles || []).map((v) => {
          // -----------------------------
          // MODEL FIX: clean up Unknown values
          // -----------------------------
          const rawModel = `${v.make || ""} ${v.model || ""}`.trim();
          const displayModel =
            !rawModel ||
            rawModel.toLowerCase() === "unknown" ||
            rawModel.toLowerCase() === "unknown unknown"
              ? "BMW X5" // default model fallback
              : rawModel;

          // -----------------------------
          // DRIVER & LOCATION FALLBACKS
          // -----------------------------
          const displayDriver =
            !v.owner || v.owner.toLowerCase() === "unknown"
              ? "John Doe"
              : v.owner;

          const displayLocation =
            !v.location || v.location.toLowerCase() === "unknown"
              ? "San Jose"
              : v.location;

          return {
            id: v.vehicle_id,
            status: v.status === "active" ? "Active" : "Inactive",
            driver: displayDriver,
            location: displayLocation,
            model: displayModel,
            lastUpdate: v.updated_at
              ? new Date(v.updated_at).toLocaleString()
              : "Unknown",
            latestAlert: null,
          };
        });

        setCars(apiCars);
      } catch (err) {
        console.error("Error loading vehicles:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchVehicles();
  }, []);

  // Combine admin hardcoded cars + API cars
  const allCars = [...extraCars, ...cars];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-neutral-800">
          Fleet Overview
        </h2>
        <Link
          to="/cars"
          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          View All Cars →
        </Link>
      </div>

      {loading ? (
        <div className="text-sm text-neutral-500">Loading cars…</div>
      ) : allCars.length === 0 ? (
        <div className="text-sm text-neutral-500">No cars found.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {allCars.map((car) => (
            <CarCard key={car.id} car={car} />
          ))}
        </div>
      )}
    </div>
  );
}
