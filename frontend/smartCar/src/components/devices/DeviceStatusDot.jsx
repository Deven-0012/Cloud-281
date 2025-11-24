import React from "react";
export default function DeviceStatusDot({ status = "Online" }) {
  const tone = status === "Online" ? "bg-emerald-500" : "bg-red-500";
  return <span className={`inline-block w-2 h-2 rounded-full ${tone}`} />;
}
