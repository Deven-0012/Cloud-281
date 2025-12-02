/**
 * API URL Configuration
 * Simple local configuration - always uses localhost:5001
 */

const getApiUrl = () => {
  // If VITE_API_URL is explicitly set, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Default to localhost (local development)
  return 'http://localhost:5001';
};

export const API_URL = getApiUrl();

// Log for debugging
console.log('API URL configured:', API_URL);

