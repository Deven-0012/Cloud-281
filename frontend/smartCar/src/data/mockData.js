// Central mock data source for Smart Car Cloud Staff Dashboard
// Replace these later with API endpoints or database queries

const d = (offset) => {
    const dt = new Date();
    dt.setDate(dt.getDate() - (30 - offset));
    return dt.toISOString().slice(0, 10);
  };
  
  // === Alert trends (daily counts) ===
  export const alertTrends = Array.from({ length: 30 }).map((_, i) => ({
    date: d(i + 1),
    Emergency: Math.max(0, Math.round(6 + Math.sin(i / 3) * 4 + (i % 7 === 0 ? 3 : 0))),
    Safety: Math.max(0, Math.round(8 + Math.cos(i / 4) * 5)),
    Anomaly: Math.max(0, Math.round(2 + Math.sin(i / 5) * 3)),
  }));
  
  // === Fleet status donut ===
  export const fleetStatus = { online: 58, offline: 12 };
  
  // === System performance lines ===
  export const systemPerf = Array.from({ length: 30 }).map((_, i) => ({
    date: d(i + 1),
    "Latency (ms)": Math.round(120 + Math.sin(i / 4) * 30 + (i % 9 === 0 ? 25 : 0)),
    "Throughput (req/s)": Math.round(300 + Math.cos(i / 5) * 60),
    "Model RT (ms)": Math.round(70 + Math.sin(i / 3) * 18),
  }));
  
  // === Sound classification mix ===
  export const soundMix = [
    { label: "Engine knock", count: 42 },
    { label: "Baby cry", count: 18 },
    { label: "Gunshot", count: 5 },
    { label: "Glass break", count: 4 },
    { label: "Siren", count: 11 },
    { label: "Other", count: 27 },
  ];
export const mockStats = {
    connectedCars: { total: 25, online: 19, offline: 6 },
    activeAlerts: { total: 5, emergency: 2, safety: 2, anomaly: 1 },
    devices: { total: 72, mic: 25, camera: 18, other: 29 },
    modelHealth: { accuracy: 98, model: 'AudioNet‑v1.2' },
    };
    
    
    export const mockAlerts = [
        {
        id: '2456', vehicleId: 'CAR-101', type: 'Emergency', sound: 'Gunshot', title: 'Gunshot detected',
        confidence: 0.95, ts: '2025-10-05T14:22:31Z', passengerDetected: true,
        location: { city: 'San Jose', lat: 37.7837, lng: -122.4090 },
        notes: 'Detected loud gunshot-like impulse near vehicle front left. Background traffic present. Model confidence high.'
        },
        {
        id: '2457', vehicleId: 'CAR-203', type: 'Safety', sound: 'Baby cry', title: 'Baby cry',
        confidence: 0.88, ts: '2025-10-05T13:10:00Z', passengerDetected: true,
        location: { city: 'San Jose', lat: 37.39, lng: -122.08 },
        notes: 'Infant crying detected inside cabin. Check passenger state.'
        },
        {
        id: '2468', vehicleId: 'CAR-C015', type: 'Anomaly', sound: 'Unknown noise', title: 'Unknown noise',
        confidence: 0.89, ts: '2025-10-04T20:44:00Z', passengerDetected: false,
        location: { city: 'Fremont', lat: 37.55, lng: -121.99 },
        notes: 'Intermittent metallic clicking outside vehicle. Could be loose trim or external source.'
        },
        ];
    
        export const mockCars = [
            {
              id: "CAR-101",
              driver: "John Doe",
              location: "San Jose, CA",
              model: "Tesla Model Y",
              lastUpdate: "11:08:59 PM",
              status: "Active",
              latestAlert: { type: "Emergency", title: "Gunshot" }, // or null
            },
            {
              id: "CAR-310",
              driver: "John Doe",
              location: "San Jose, CA",
              model: "Rivian R1S",
              lastUpdate: "11:08:59 PM",
              status: "Active",
              latestAlert: null, // no issues -> green banner
            },
            {
              id: "CAR-203",
              driver: "Emily Chen",
              location: "Los Angeles, CA",
              model: "Ford Mach-E",
              lastUpdate: "11:08:59 PM",
              status: "Idle",
              latestAlert: { type: "Safety", title: "Baby cry" },
            },
          ];
          
    
    
   
    export const mockDevices = [
        { id: "MIC-1001", type: "Microphone", model: "AudioNet-M1", firmware: "1.4.3", outdated: false, status: "Online", carId: "CAR-101", rssi: -61, lastSeen: "2025-11-21T22:07:00Z" },
        { id: "CAM-1002", type: "Camera", model: "Vision-S2", firmware: "1.1.0", outdated: false, status: "Online", carId: "CAR-101", rssi: -55, lastSeen: "2025-11-21T22:05:00Z" },
        { id: "OBD-1003", type: "Other", model: "CAN-Bus-Reader", firmware: "2.0.0", outdated: false, status: "Online", carId: "CAR-101", rssi: -70, lastSeen: "2025-11-21T21:59:00Z" },
        { id: "MIC-2001", type: "Microphone", model: "AudioNet-M1", firmware: "1.2.1", outdated: true, status: "Online", carId: "CAR-203", rssi: -68, lastSeen: "2025-11-21T22:08:00Z" },
        { id: "CAM-2002", type: "Camera", model: "Vision-S2", firmware: "1.0.4", outdated: true, status: "Offline", carId: "CAR-203", rssi: null, lastSeen: "2025-11-21T20:10:00Z" },
        { id: "MIC-3001", type: "Microphone", model: "AudioNet-M2", firmware: "1.0.0", outdated: false, status: "Online", carId: "CAR-310", rssi: -59, lastSeen: "2025-11-21T22:06:00Z" },
        { id: "OTH-3002", type: "Other", model: "Pressure-Sensor", firmware: "0.9.9", outdated: true, status: "Online", carId: "CAR-310", rssi: -72, lastSeen: "2025-11-21T22:03:00Z" },
        ];
    
    // Example export for quick import in pages/components
    export default { mockStats, mockAlerts, mockCars, mockDevices, alertTrends, soundMix, fleetStatus, systemPerf,  };