import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, useMap } from "react-leaflet";

function InvalidateOnResize() {
  const map = useMap();
  useEffect(() => {
    const ro = new ResizeObserver(() => map.invalidateSize());
    ro.observe(map.getContainer());
    // also invalidate after first paint to avoid blank tiles
    const t = setTimeout(() => map.invalidateSize(), 120);
    return () => {
      ro.disconnect();
      clearTimeout(t);
    };
  }, [map]);
  return null;
}

export default function AlertLocationMap({ lat, lng }) {
  const center = [lat, lng];
  return (
    <MapContainer
      center={center}
      zoom={14}
      // Use inline height so it can’t be purged by Tailwind, and always renders
      style={{ height: 420, width: "100%" }}
      className="rounded-[14px]"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      <InvalidateOnResize />
      <Marker position={center} />
    </MapContainer>
  );
}
