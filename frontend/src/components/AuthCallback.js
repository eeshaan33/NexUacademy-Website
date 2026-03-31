import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthCallback = () => {
  const navigate = useNavigate();
  const { setUser, setIsAuthenticated } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    const processSession = async () => {
      if (hasProcessed.current) return;
      hasProcessed.current = true;

      const hash = window.location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);

      if (!sessionIdMatch) {
        navigate('/login');
        return;
      }

      const sessionId = sessionIdMatch[1];

      try {
        const response = await axios.post(
          `${API}/auth/google/session`,
          {},
          {
            headers: { 'X-Session-ID': sessionId },
            withCredentials: true
          }
        );

        setUser(response.data.user);
        setIsAuthenticated(true);

        window.location.hash = '';

        const userRole = response.data.user?.role;
        if (userRole === 'teacher') {
          navigate('/teacher', { replace: true, state: { user: response.data.user } });
        } else {
          navigate('/dashboard', { replace: true, state: { user: response.data.user } });
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        navigate('/login', { replace: true });
      }
    };

    processSession();
  }, [navigate, setUser, setIsAuthenticated]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Completing authentication...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
