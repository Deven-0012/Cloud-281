import React from "react";
import { Link } from "react-router-dom";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import { fmtTime } from "../../utils/format";

export default function AlertsTable({ alerts }) {
  return (
    <Card>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-neutral-500">
              <th className="py-2 pr-3">Alert ID</th>
              <th className="py-2 pr-3">Type</th>
              <th className="py-2 pr-3">Sound</th>
              <th className="py-2 pr-3">Confidence</th>
              <th className="py-2 pr-3">Time</th>
              <th className="py-2 pr-3">Car</th>
              <th className="py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id} className="border-t border-neutral-200">
                <td className="py-2 pr-3 font-medium">#{a.id}</td>
                <td className="py-2 pr-3">
                  <Badge
                    tone={
                      a.type === "Emergency"
                        ? "red"
                        : a.type === "Safety"
                        ? "amber"
                        : "blue"
                    }
                  >
                    {a.type}
                  </Badge>
                </td>
                <td className="py-2 pr-3">
                  <span className="px-2 py-0.5 rounded-full bg-neutral-100 text-neutral-700 text-xs">
                    {a.sound}
                  </span>
                </td>
                <td className="py-2 pr-3">{Math.round(a.confidence * 100)}%</td>
                <td className="py-2 pr-3 whitespace-nowrap">{fmtTime(a.ts)}</td>
                <td className="py-2 pr-3">{a.vehicleId}</td>
                <td className="py-2">
                  <Link
                    to={`/alerts/${a.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    Details
                  </Link>
                </td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr>
                <td colSpan={7} className="py-10 text-center text-neutral-500">
                  No alerts match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
