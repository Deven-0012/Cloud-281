import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.REACT_APP_API_URL || 'http://localhost:5001';

const AlertDetailsPage = () => {
  const { alertId } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlert();
  }, [alertId]);

  const fetchAlert = async () => {
    try {
      const response = await axios.get(`${API_URL}/v1/alerts/${alertId}`);
      setAlert(response.data);
    } catch (error) {
      console.error('Error fetching alert:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async () => {
    try {
      await axios.post(`${API_URL}/v1/alerts/${alertId}/acknowledge`);
      fetchAlert();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  if (loading) {
    return <div className="page-container">Loading...</div>;
  }

  if (!alert) {
    return <div className="page-container">Alert not found</div>;
  }

  return (
    <div className="page-container">
      <header className="dashboard-header">
        <h1>Smart Car Cloud</h1>
        <nav className="dashboard-nav">
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/live-map')}>Live Map</button>
          <button onClick={() => navigate('/cars')}>Cars</button>
          <button onClick={() => navigate('/analytics')}>Analytics</button>
        </nav>
      </header>
      <div className="page-content">
        <h2>Alert Details</h2>
        <div className="alert-details">
          <div className="detail-item">
            <label>Alert ID:</label>
            <span>{alert.alert_id}</span>
          </div>
          <div className="detail-item">
            <label>Vehicle:</label>
            <span>{alert.vehicle_id}</span>
          </div>
          <div className="detail-item">
            <label>Sound Detected:</label>
            <span>{alert.sound_label}</span>
          </div>
          <div className="detail-item">
            <label>Confidence:</label>
            <span>{(alert.confidence * 100).toFixed(2)}%</span>
          </div>
          <div className="detail-item">
            <label>Severity:</label>
            <span>{alert.severity}</span>
          </div>
          <div className="detail-item">
            <label>Status:</label>
            <span>{alert.status}</span>
          </div>
          <div className="detail-item">
            <label>Message:</label>
            <span>{alert.message}</span>
          </div>
          <div className="detail-item">
            <label>Created:</label>
            <span>{new Date(alert.created_at).toLocaleString()}</span>
          </div>
          {alert.status !== 'acknowledged' && (
            <button onClick={handleAcknowledge} className="acknowledge-btn">
              Acknowledge Alert
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlertDetailsPage;

