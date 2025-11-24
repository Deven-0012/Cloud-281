import React, { useMemo, useState } from "react";
import DevicesToolbar from "../components/devices/DevicesToolbar";
import DeviceTable from "../components/devices/DeviceTable";
import DeviceCard from "../components/devices/DeviceCard";
import StatCard from "../components/ui/StatCard";
import { Router, Cpu, WifiOff, RefreshCcw, Layers } from "lucide-react";
import { mockDevices } from "../data/mockData";


export default function Devices() {
const [view, setView] = useState("table"); // table | grid
const [status, setStatus] = useState("All"); // All | Online | Offline
const [type, setType] = useState("All"); // All | Microphone | Camera | Other
const [query, setQuery] = useState("");
const [sortBy, setSortBy] = useState("id"); // id | car | type | status | rssi | lastSeen


const stats = useMemo(() => {
const total = mockDevices.length;
const online = mockDevices.filter((d) => d.status === "Online").length;
const offline = total - online;
const outdated = mockDevices.filter((d) => d.outdated === true).length;
return { total, online, offline, outdated };
}, []);

const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let list = mockDevices.filter((d) => {
    const statusOk = status === "All" || d.status === status;
    const typeOk = type === "All" || d.type === type;
    const qOk =
    !q ||
    d.id.toLowerCase().includes(q) ||
    d.carId.toLowerCase().includes(q) ||
    d.model.toLowerCase().includes(q) ||
    d.type.toLowerCase().includes(q) ||
    (d.firmware || "").toLowerCase().includes(q);
    return statusOk && typeOk && qOk;
    });
    
    
    const by = {
    id: (a, b) => a.id.localeCompare(b.id),
    car: (a, b) => a.carId.localeCompare(b.carId),
    type: (a, b) => a.type.localeCompare(b.type),
    status: (a, b) => a.status.localeCompare(b.status),
    rssi: (a, b) => (b.rssi ?? -9999) - (a.rssi ?? -9999),
    lastSeen: (a, b) => new Date(b.lastSeen) - new Date(a.lastSeen),
    }[sortBy];
    
    
    return list.sort(by);
    }, [status, type, query, sortBy]);

    return (
        <div className="space-y-6">
        <div className="text-center">
        <h1 className="text-xl font-semibold">IoT Device Management</h1>
        <p className="text-sm text-neutral-600">A list of all sensors and devices connected to the fleet.</p>
        </div>
        
        
        {/* KPI Row */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Devices" value={stats.total} icon={<Layers className="w-5 h-5" />} />
        <StatCard title="Online" value={stats.online} icon={<Router className="w-5 h-5" />} sub="Healthy connectivity" />
        <StatCard title="Offline" value={stats.offline} icon={<WifiOff className="w-5 h-5" />} sub="Needs attention" />
        <StatCard title="Firmware Updates" value={stats.outdated} icon={<RefreshCcw className="w-5 h-5" />} sub="Out-of-date" />
        </div>
        
        
        {/* Toolbar */}
        <DevicesToolbar
        view={view}
        onViewChange={setView}
        status={status}
        onStatusChange={setStatus}
        type={type}
        onTypeChange={setType}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        query={query}
        onQueryChange={setQuery}
        onRefresh={() => window.location.reload()}
        />
        
        
        {/* Content */}
        {view === "table" ? (
        <DeviceTable devices={filtered} />
        ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((d) => (
        <DeviceCard key={d.id} device={d} />
        ))}
        {filtered.length === 0 && (
        <div className="col-span-full text-center text-neutral-500 py-16">No devices match your filters.</div>
        )}
        </div>
        )}
        </div>
        );
        }