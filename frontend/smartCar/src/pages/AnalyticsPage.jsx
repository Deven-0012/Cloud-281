import React from 'react';
import { useNavigate } from 'react-router-dom';

const AnalyticsPage = () => {
  const navigate = useNavigate();

  return (
    <div className="page-container">
      <header className="dashboard-header">
        <h1>Smart Car Cloud</h1>
        <nav className="dashboard-nav">
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/live-map')}>Live Map</button>
          <button onClick={() => navigate('/cars')}>Cars</button>
          <button onClick={() => navigate('/analytics')} className="active">Analytics</button>
          <button onClick={() => navigate('/login')} className="logout-btn">Logout</button>
        </nav>
      </header>
      <div className="page-content">
        <h2>Analytics</h2>
        <p>Analytics and reporting interface will be displayed here.</p>
      </div>
    </div>
  );
};

export default AnalyticsPage;

