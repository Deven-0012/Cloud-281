import React, { useMemo, useState } from "react";
import CarsToolbar from "../components/cars/CarsToolbar";
import CarCard from "../components/cars/CarCard";
import { mockCars } from "../data/mockData";

export default function Cars() {
  const [status, setStatus] = useState("All"); // All | Active | Idle
  const [city, setCity] = useState("All");
  const [query, setQuery] = useState("");

  const cities = useMemo(() => {
    const set = new Set();
    mockCars.forEach((c) => set.add(c.location.split(",")[0].trim()));
    return ["All", ...Array.from(set).sort()];
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return mockCars.filter((c) => {
      const statusOk = status === "All" || c.status === status;
      const cityName = c.location.split(",")[0].trim();
      const cityOk = city === "All" || cityName === city;
      const qOk =
        !q ||
        c.id.toLowerCase().includes(q) ||
        c.driver.toLowerCase().includes(q) ||
        c.location.toLowerCase().includes(q) ||
        c.model.toLowerCase().includes(q);
      return statusOk && cityOk && qOk;
    });
  }, [status, city, query]);

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
        onRefresh={() => window.location.reload()}
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
