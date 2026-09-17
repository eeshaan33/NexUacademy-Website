import axios from 'axios';
import { getToken, clearTokens } from '../context/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE_URL = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // send Emergent session_token cookie on every request
});

api.interceptors.request.use((config) => {
  const t = getToken();
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      clearTokens();
      // Optional: redirect on hard 401s so protected pages don't infinite-loop
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/auth/')
          && !window.location.pathname.startsWith('/login')
          && window.location.pathname !== '/' && !window.location.pathname.startsWith('/landing')) {
        // don't force-redirect to avoid disrupting public pages
      }
    }
    return Promise.reject(err);
  }
);

export default api;
