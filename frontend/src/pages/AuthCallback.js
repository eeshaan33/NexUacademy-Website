import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, setTokens } from '../context/AuthContext';
import api from '../utils/api';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const [msg, setMsg] = useState('Finishing sign-in...');
  const navigate = useNavigate();
  const { setUser, setIsAuthenticated } = useAuth();

  useEffect(() => {
    (async () => {
      try {
        const hash = window.location.hash.replace(/^#/, '');
        const params = new URLSearchParams(hash);
        const access = params.get('access_token');
        const refresh = params.get('refresh_token');
        if (!access) {
          setMsg('Missing session — please try logging in again.');
          setTimeout(() => navigate('/login'), 2000);
          return;
        }
        setTokens(access, refresh);
        const me = await api.get('/auth/me');
        setUser(me.data.user);
        setIsAuthenticated(true);
        const role = me.data.user?.role;
        const target = role === 'admin' ? '/admin'
                     : role === 'teacher' ? '/teacher'
                     : '/dashboard';
        window.location.hash = '';
        navigate(target, { replace: true });
      } catch (e) {
        setMsg('Sign-in failed. Redirecting...');
        setTimeout(() => navigate('/login'), 2000);
      }
    })();
  }, [navigate, setUser, setIsAuthenticated]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-indigo-500 mb-3" />
        <p className="text-slate-600" data-testid="auth-callback-msg">{msg}</p>
      </div>
    </div>
  );
}
