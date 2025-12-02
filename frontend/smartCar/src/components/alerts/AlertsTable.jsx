import React, { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Trash2 } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import { fmtTime } from "../../utils/format";
import { API_URL } from "../../utils/api";

export default function AlertsTable({ alerts, onDelete }) {
  const { user } = useAuth();
  const [deleting, setDeleting] = useState({});
  const isAdmin = user?.role === 'admin';

  const handleDelete = async (alertId, event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this alert? This action cannot be undone.')) {
      return;
    }

    setDeleting({ ...deleting, [alertId]: true });

    try {
      await axios.delete(`${API_URL}/v1/alerts/${alertId}`);
      
      // Call parent callback to refresh alerts
      if (onDelete) {
        onDelete(alertId);
      } else {
        // Fallback: reload page if no callback provided
        window.location.reload();
      }
    } catch (error) {
      console.error('Error deleting alert:', error);
      alert(error.response?.data?.error || 'Failed to delete alert');
    } finally {
      setDeleting({ ...deleting, [alertId]: false });
    }
  };

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
                        : a.type === "High priority"
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
                <td className="py-2 pr-3">{a.vehicle}</td>
                <td className="py-2">
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/alerts/${a.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      Details
                    </Link>
                    {isAdmin && (
                      <button
                        onClick={(e) => handleDelete(a.id, e)}
                        disabled={deleting[a.id]}
                        className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Delete alert"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
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
