import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { Loader2 } from 'lucide-react';

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS,
// THIS BREAKS THE AUTH. The redirect is built from window.location.origin.
export default function EmergentAuthCallback() {
  const [msg, setMsg] = useState('Finishing sign-in...');
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser, setIsAuthenticated } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    (async () => {
      try {
        const hash = location.hash.replace(/^#/, '');
        const params = new URLSearchParams(hash);
        const sessionId = params.get('session_id');
        if (!sessionId) {
          setMsg('Missing session_id — please try signing in again.');
          setTimeout(() => navigate('/login', { replace: true }), 1500);
          return;
        }
        const res = await api.post(
          '/auth/emergent/session',
          {},
          { headers: { 'X-Session-ID': sessionId }, withCredentials: true }
        );
        const u = res.data.user;
        setUser(u);
        setIsAuthenticated(true);
        // Clear the fragment so refresh doesn't re-run the exchange
        window.history.replaceState({}, '', window.location.pathname + window.location.search);
        const target = u.role === 'admin' ? '/admin'
                     : u.role === 'teacher' ? '/teacher'
                     : '/dashboard';
        navigate(target, { replace: true, state: { user: u } });
      } catch (err) {
        console.error('Emergent auth callback failed', err);
        setMsg('Sign-in failed. Redirecting...');
        setTimeout(() => navigate('/login', { replace: true }), 1500);
      }
    })();
  }, [location.hash, navigate, setUser, setIsAuthenticated]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-indigo-500 mb-3" />
        <p className="text-slate-600" data-testid="emergent-callback-msg">{msg}</p>
      </div>
    </div>
  );
}
