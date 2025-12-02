import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../utils/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token and get user info
      axios.get(`${API_URL}/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(response => {
        setUser(response.data.user);
        setIsAuthenticated(true);
        // Set default axios header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      })
      .catch(() => {
        // Token invalid, clear it
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      })
      .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_URL}/v1/auth/login`, {
        email,
        password
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const { token, user: userData } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setUser(userData);
      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      // Handle ERR_BLOCKED_BY_CLIENT (usually browser extension)
      if (error.message.includes('ERR_BLOCKED_BY_CLIENT') || error.code === 'ERR_BLOCKED_BY_CLIENT') {
        return { 
          success: false, 
          error: 'Request blocked. Please disable ad blockers or privacy extensions and try again.' 
        };
      }
      return { 
        success: false, 
        error: error.response?.data?.error || error.message || 'Login failed' 
      };
    }
  };

  const register = async (email, password, full_name, role = 'owner') => {
    try {
      const response = await axios.post(`${API_URL}/v1/auth/register`, {
        email,
        password,
        full_name,
        role
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const { token, user: userData } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setUser(userData);
      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      // Handle ERR_BLOCKED_BY_CLIENT (usually browser extension)
      if (error.message.includes('ERR_BLOCKED_BY_CLIENT') || error.code === 'ERR_BLOCKED_BY_CLIENT') {
        return { 
          success: false, 
          error: 'Request blocked. Please disable ad blockers or privacy extensions and try again.' 
        };
      }
      return { 
        success: false, 
        error: error.response?.data?.error || error.message || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      user, 
      loading,
      login, 
      register,
      logout 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

