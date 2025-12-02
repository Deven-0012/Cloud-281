import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../utils/api';
import './DashboardPage.css';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    connectedCars: 0,
    onlineCars: 0,
    offlineCars: 0,
    activeAlerts: 0,
    emergencyAlerts: 0,
    safetyAlerts: 0,
    anomalyAlerts: 0,
    iotDevices: 0,
    microphones: 0,
    cameras: 0
  });
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [connectedCars, setConnectedCars] = useState([]);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch stats from API
      try {
        const statsResponse = await axios.get(`${API_URL}/v1/dashboard/stats`);
        setStats(statsResponse.data);
      } catch (e) {
        console.error('Error fetching stats:', e);
        // Use mock data if API fails
        setStats({
          connectedCars: 25,
          onlineCars: 19,
          offlineCars: 6,
          activeAlerts: 5,
          emergencyAlerts: 2,
          safetyAlerts: 2,
          anomalyAlerts: 1,
          iotDevices: 72,
          microphones: 25,
          cameras: 18,
          other: 29
        });
      }

      // Fetch recent alerts
      try {
        const alertsResponse = await axios.get(`${API_URL}/v1/alerts?limit=10`);
        const alerts = alertsResponse.data.alerts || [];
        setRecentAlerts(alerts.map(alert => ({
          id: alert.alert_id,
          type: alert.alert_type?.toUpperCase() || 'UNKNOWN',
          sound: alert.sound_label || 'Unknown sound',
          carId: alert.vehicle_id,
          timestamp: new Date(alert.created_at).toLocaleString(),
          status: alert.status
        })));
      } catch (e) {
        console.error('Error fetching alerts:', e);
        // Use mock data
        setRecentAlerts([
          {
            id: '2456',
            type: 'EMERGENCY',
            sound: 'Gun sound detected',
            carId: 'CAR-A1234',
            timestamp: '2025-10-05 14:22',
            status: 'new'
          },
          {
            id: '2457',
            type: 'SAFETY',
            sound: 'Baby cry',
            carId: 'CAR-B207',
            timestamp: '2025-10-05 13:10',
            status: 'under_review'
          }
        ]);
      }

      // Fetch vehicles
      try {
        const vehiclesResponse = await axios.get(`${API_URL}/v1/vehicles`);
        const vehicles = vehiclesResponse.data.vehicles || [];
        setConnectedCars(vehicles.map(v => ({
          id: v.vehicle_id,
          status: v.status === 'active' ? 'online' : 'offline',
          driver: v.owner_id || 'Unknown'
        })));
      } catch (e) {
        console.error('Error fetching vehicles:', e);
        // Use mock data
        setConnectedCars([
          { id: 'CAR-A1234', status: 'online', driver: 'John Doe' },
          { id: 'CAR-B4567', status: 'offline', driver: 'Jane Smith' }
        ]);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const getAlertTypeClass = (type) => {
    switch (type) {
      case 'EMERGENCY':
        return 'alert-emergency';
      case 'SAFETY':
        return 'alert-safety';
      case 'ANOMALY':
      case 'MAINTENANCE':
        return 'alert-anomaly';
      default:
        return '';
    }
  };

  const handleAlertClick = (alertId) => {
    navigate(`/alert/${alertId}`);
  };

  const handleAcknowledgeAll = async () => {
    try {
      // API call to acknowledge all alerts
      console.log('Acknowledging all alerts...');
      fetchDashboardData();
    } catch (error) {
      console.error('Error acknowledging alerts:', error);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Smart Car Cloud</h1>
        <nav className="dashboard-nav">
          <button onClick={() => navigate('/dashboard')} className="active">Dashboard</button>
          <button onClick={() => navigate('/live-map')}>Live Map</button>
          <button onClick={() => navigate('/cars')}>Cars</button>
          <button onClick={() => navigate('/analytics')}>Analytics</button>
          <button onClick={() => navigate('/login')} className="logout-btn">Logout</button>
        </nav>
      </header>

      <div className="dashboard-content">
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Connected Cars</h3>
            <div className="stat-value">{stats.connectedCars}</div>
            <div className="stat-detail">
              Online: {stats.onlineCars} • Offline: {stats.offlineCars}
            </div>
          </div>

          <div className="stat-card alert-card">
            <h3>Active Alerts (open)</h3>
            <div className="stat-value">{stats.activeAlerts}</div>
            <div className="stat-detail">
              Emergency: {stats.emergencyAlerts} • Safety: {stats.safetyAlerts} • Anomaly: {stats.anomalyAlerts}
            </div>
          </div>

          <div className="stat-card">
            <h3>IoT Devices</h3>
            <div className="stat-value">{stats.iotDevices}</div>
            <div className="stat-detail">
              Mic: {stats.microphones} • Camera: {stats.cameras} • Other: {stats.other || 0}
            </div>
          </div>
        </div>

        <div className="content-grid">
          <div className="content-section">
            <div className="section-header">
              <h2>Recent Alerts</h2>
            </div>
            <div className="alerts-list">
              {recentAlerts.length > 0 ? (
                recentAlerts.map(alert => (
                  <div 
                    key={alert.id} 
                    className={`alert-item ${getAlertTypeClass(alert.type)}`}
                    onClick={() => handleAlertClick(alert.id)}
                  >
                    <div className="alert-badge">{alert.type}</div>
                    <div className="alert-content">
                      <div className="alert-title">{alert.sound}</div>
                      <div className="alert-meta">
                        Alert ID: {alert.id} • Car: {alert.carId} • {alert.timestamp}
                      </div>
                    </div>
                    <button className="view-btn">View</button>
                  </div>
                ))
              ) : (
                <div className="no-data">No alerts</div>
              )}
            </div>
          </div>

          <div className="content-section">
            <div className="section-header">
              <h2>Connected Cars</h2>
            </div>
            <div className="cars-list">
              {connectedCars.length > 0 ? (
                connectedCars.map(car => (
                  <div key={car.id} className="car-item">
                    <div className={`status-indicator ${car.status}`}></div>
                    <div className="car-content">
                      <div className="car-id">{car.id}</div>
                      <div className="car-driver">{car.driver}</div>
                    </div>
                    <span className="status-label">{car.status}</span>
                  </div>
                ))
              ) : (
                <div className="no-data">No vehicles</div>
              )}
            </div>
          </div>
        </div>

        <div className="quick-actions">
          <div className="section-header">
            <h2>Quick Actions</h2>
          </div>
          <div className="action-buttons">
            <button onClick={handleAcknowledgeAll} className="action-btn primary">
              Acknowledge All
            </button>
            <button onClick={() => navigate('/live-map')} className="action-btn">
              View Live Map
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;

