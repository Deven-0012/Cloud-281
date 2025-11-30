import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import Shell from "./components/layout/Shell";
import HomePage from "./pages/HomePage";
import Analytics from "./pages/Analytics";
import Alerts from "./pages/Alerts";
import Devices from "./pages/Devices";
import Cars from "./pages/Cars";
import AlertDetails from "./pages/AlertDetails";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div className="p-6">Loading…</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

export default function App() {
  return (
    <React.Suspense fallback={<div className="p-6">Loading…</div>}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Shell />
            </ProtectedRoute>
          }
        >
          <Route index element={<HomePage />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="alerts/:id" element={<AlertDetails />} />
          <Route path="cars" element={<Cars />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="devices" element={<Devices />} />
        </Route>
      </Routes>
    </React.Suspense>
  );
}
