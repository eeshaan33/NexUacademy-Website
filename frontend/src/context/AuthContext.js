import React, { createContext, useState, useContext, useCallback, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TOKEN_KEY = 'nx_access_token';
const REFRESH_KEY = 'nx_refresh_token';

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setTokens = (access, refresh) => {
  if (access) localStorage.setItem(TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
};
export const clearTokens = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

const authHeader = () => {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const checkAuth = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const response = await axios.get(`${API}/auth/me`, { headers: authHeader() });
      setUser(response.data.user);
      setIsAuthenticated(true);
    } catch {
      clearTokens();
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    setTokens(response.data.access_token || response.data.token, response.data.refresh_token);
    setUser(response.data.user);
    setIsAuthenticated(true);
    return response.data;
  };

  const register = async (userData) => {
    const response = await axios.post(`${API}/auth/signup`, userData);
    setTokens(response.data.access_token || response.data.token, response.data.refresh_token);
    setUser(response.data.user);
    setIsAuthenticated(true);
    return response.data;
  };

  const loginWithGoogle = async () => {
    // Always pass the current browser origin so Supabase sends the callback
    // back to THIS domain (dev / preview / prod) — otherwise it uses whatever
    // Site URL is configured in the Supabase Dashboard (may be localhost).
    const redirectTo = `${window.location.origin}/auth/callback`;
    const { data } = await axios.get(`${API}/auth/google/url`, { params: { redirect_to: redirectTo } });
    if (data.url) window.location.href = data.url;
  };

  const logout = async () => {
    try { await axios.post(`${API}/auth/logout`, {}); } catch { /* ignore */ }
    clearTokens();
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    loginWithGoogle,
    logout,
    setUser,
    setIsAuthenticated,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
