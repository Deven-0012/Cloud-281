import React from "react";
export default function Tabs({ value, onChange, options }) {
  return (
    <div className="flex items-center gap-2">
      {options.map((opt) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className={`px-3 py-1.5 rounded-full text-sm border ${
            value === opt
              ? "bg-neutral-900 text-white border-neutral-900"
              : "bg-white hover:bg-neutral-100 border-neutral-200"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
