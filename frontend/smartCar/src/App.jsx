import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import './App.css';

// Lazy-load pages (code-splitting)
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const LiveMapPage = lazy(() => import('./pages/LiveMapPage'));
const AlertDetailsPage = lazy(() => import('./pages/AlertDetailsPage'));
const CarMonitoringPage = lazy(() => import('./pages/CarMonitoringPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));

// Simple loading fallback
function Loader() {
  return <div className="p-6 text-sm text-gray-600">Loading…</div>;
}

// Protected route: waits for auth to resolve, then gates access
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth(); // make sure AuthContext exposes isLoading
  const location = useLocation();

  if (isLoading) return <Loader />;

  if (!isAuthenticated) {
    // Send user to login and remember where they were trying to go
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}

// Public-only route: blocks if user is already signed in (e.g., /login, /register)
function PublicOnlyRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <Loader />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Suspense fallback={<Loader />}>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            <PublicOnlyRoute>
              <LoginPage />
            </PublicOnlyRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicOnlyRoute>
              <RegisterPage />
            </PublicOnlyRoute>
          }
        />

        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/live-map"
          element={
            <ProtectedRoute>
              <LiveMapPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/alert/:alertId"
          element={
            <ProtectedRoute>
              <AlertDetailsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/cars"
          element={
            <ProtectedRoute>
              <CarMonitoringPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <AnalyticsPage />
            </ProtectedRoute>
          }
        />

        {/* Default + 404 */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<div className="p-6">404 — Page not found</div>} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <AppRoutes />
        </div>
      </Router>
    </AuthProvider>
  );
}
