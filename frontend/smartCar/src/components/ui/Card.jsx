import React from "react";
export default function Card({ children, className = "" }) {
  return (
    <section
      className={`bg-white rounded-2xl shadow-sm border border-neutral-200 p-4 ${className}`}
    >
      {children}
    </section>
  );
}
