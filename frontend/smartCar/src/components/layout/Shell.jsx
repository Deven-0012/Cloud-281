import React from "react";
import { NavLink } from "react-router-dom";
import { Cpu, BarChart3, Map, Car, Gauge, LogOut } from "lucide-react";

export default function Shell({ children }) {
  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <TopNav />
      <header className="bg-gradient-to-b from-white to-neutral-50 border-b border-neutral-200">
        <div className="mx-auto max-w-7xl px-4 py-10 text-center">
          <div className="text-xs tracking-widest text-neutral-500 mb-2">
            AUDIO-DRIVEN FLEET SAFETY
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold">
            Audio-Driven Surveillance Cloud
          </h1>
          <p className="text-neutral-600 max-w-2xl mx-auto mt-2">
            Monitor, detect, and respond to sound events across your autonomous
            cars — in real time and at scale.
          </p>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}

function TopNav() {
  return (
    <div className="sticky top-0 z-30 bg-white/90 backdrop-blur border-b border-neutral-200">
      <div className="mx-auto max-w-7xl px-4 h-14 flex items-center gap-4">
        <div className="flex items-center gap-2 font-semibold">
          <Cpu className="w-5 h-5" /> Smart Car Cloud
        </div>
        <nav className="ml-6 flex items-center gap-3 text-sm">
          <TopLink
            to="/"
            label="Dashboard"
            icon={<BarChart3 className="w-4 h-4" />}
          />
          <TopLink
            to="/alerts"
            label="Live Map"
            icon={<Map className="w-4 h-4" />}
          />
          <TopLink to="/cars" label="Cars" icon={<Car className="w-4 h-4" />} />
          <TopLink
            to="/analytics"
            label="Analytics"
            icon={<Gauge className="w-4 h-4" />}
          />
          <TopLink
            to="/devices"
            label="Devices"
            icon={<Cpu className="w-4 h-4" />}
          />
        </nav>
        <button className="ml-auto btn-secondary">
          <LogOut className="w-4 h-4" /> Logout
        </button>
      </div>
    </div>
  );
}

function TopLink({ to, label, icon }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `inline-flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-neutral-100 ${
          isActive ? "bg-neutral-900 text-white" : "text-neutral-700"
        }`
      }
    >
      {icon}
      <span>{label}</span>
    </NavLink>
  );
}
