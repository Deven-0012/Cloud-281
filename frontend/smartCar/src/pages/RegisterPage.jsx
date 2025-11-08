import React from 'react';
import { useNavigate } from 'react-router-dom';

const RegisterPage = () => {
  const navigate = useNavigate();

  return (
    <div className="register-container">
      <div className="register-box">
        <h1>Registration</h1>
        <p>Registration is currently disabled. Please use the default credentials to login.</p>
        <button onClick={() => navigate('/login')} className="back-btn">
          Back to Login
        </button>
      </div>
    </div>
  );
};

export default RegisterPage;

