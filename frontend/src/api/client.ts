import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000,
});

// Request interceptor to attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('traffic_sense_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor with 1 retry on timeout / wake-up delay
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Retry once if server is cold-starting
    if (error.code === 'ECONNABORTED' && !originalRequest._retry) {
      originalRequest._retry = true;
      console.warn("Server cold-start delay detected, retrying request...");
      return api(originalRequest);
    }

    if (error.response?.status === 401) {
      // Clear token and redirect to login if session expired
      if (window.location.pathname.startsWith('/admin')) {
        localStorage.removeItem('traffic_sense_token');
        window.location.href = '/login?expired=1';
      }
    }

    return Promise.reject(error);
  }
);
