import React from "react";
import Card from "../ui/Card";
import CarOverviewCard from "./CarOverviewCard";
import { mockCars } from "../../data/mockData";

export default function FleetOverview() {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-medium text-lg">Fleet Overview</h2>
        <a href="/car" className="text-sm text-blue-600 hover:underline">
          View All Cars →
        </a>
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockCars.slice(0, 3).map((car) => (
          <CarOverviewCard key={car.id} car={car} />
        ))}
      </div>
    </section>
  );
}
