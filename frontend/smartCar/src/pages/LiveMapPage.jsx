import React from 'react';
import { useNavigate } from 'react-router-dom';

const LiveMapPage = () => {
  const navigate = useNavigate();

  return (
    <div className="page-container">
      <header className="dashboard-header">
        <h1>Smart Car Cloud</h1>
        <nav className="dashboard-nav">
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/live-map')} className="active">Live Map</button>
          <button onClick={() => navigate('/cars')}>Cars</button>
          <button onClick={() => navigate('/analytics')}>Analytics</button>
          <button onClick={() => navigate('/login')} className="logout-btn">Logout</button>
        </nav>
      </header>
      <div className="page-content">
        <h2>Live Map</h2>
        <p>Live map view of connected vehicles will be displayed here.</p>
        <div className="map-placeholder">
          Map Integration Coming Soon
        </div>
      </div>
    </div>
  );
};

export default LiveMapPage;

