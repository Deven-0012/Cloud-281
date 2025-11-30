import React, { useEffect } from "react";
import Card from "../ui/Card";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import { Link } from "react-router-dom";

function FitToMarkers({ points }) {
  const map = useMap();
  useEffect(() => {
    if (!points?.length) return;
    const bounds = points.map((p) => [p.location.lat, p.location.lng]);
    if (bounds.length === 1) {
      map.setView(bounds[0], 13);
    } else {
      map.fitBounds(bounds, { padding: [30, 30] });
    }
    // ensure tiles align
    setTimeout(() => map.invalidateSize(), 100);
  }, [points, map]);
  return null;
}

function InvalidateOnResize() {
  const map = useMap();
  useEffect(() => {
    const ro = new ResizeObserver(() => map.invalidateSize());
    ro.observe(map.getContainer());
    return () => ro.disconnect();
  }, [map]);
  return null;
}

export default function AlertsMap({ alerts }) {
  const center = alerts[0]?.location
    ? [alerts[0].location.lat, alerts[0].location.lng]
    : [37.7749, -122.4194];

  return (
    <Card>
      <div className="font-medium mb-3">Map</div>
      <div className="map-card rounded-2xl overflow-hidden border border-neutral-200">
        <MapContainer center={center} zoom={12} className="h-full w-full">
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap contributors"
          />
          <InvalidateOnResize />
          <FitToMarkers points={alerts} />
          {alerts
            .filter(a => a.location && a.location.lat && a.location.lng)
            .map((a) => (
            <Marker
              key={a.id}
              position={[a.location.lat, a.location.lng]}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-medium">
                    #{a.id} · {a.type}
                  </div>
                  <div className="text-neutral-600">{a.sound}</div>
                  <div className="text-xs text-neutral-500 mt-1">
                    Priority: {a.priority || 'medium'}
                  </div>
                  <Link
                    to={`/alerts/${a.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    Details
                  </Link>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </Card>
  );
}
