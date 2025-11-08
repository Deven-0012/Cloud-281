import React from 'react';
import { useNavigate } from 'react-router-dom';

const CarMonitoringPage = () => {
  const navigate = useNavigate();

  return (
    <div className="page-container">
      <header className="dashboard-header">
        <h1>Smart Car Cloud</h1>
        <nav className="dashboard-nav">
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/live-map')}>Live Map</button>
          <button onClick={() => navigate('/cars')} className="active">Cars</button>
          <button onClick={() => navigate('/analytics')}>Analytics</button>
          <button onClick={() => navigate('/login')} className="logout-btn">Logout</button>
        </nav>
      </header>
      <div className="page-content">
        <h2>Car Monitoring</h2>
        <p>Vehicle monitoring and management interface will be displayed here.</p>
      </div>
    </div>
  );
};

export default CarMonitoringPage;

