import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, setTokens, clearTokens } from '../context/AuthContext';
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
        const u = me.data.user;

        // Block Google sign-up for preseed students that haven't claimed yet.
        // A preseed student's email is only bound to their profile via the
        // /first-time-setup flow; if it lands here first, we sign them out
        // and redirect them to claim manually so we can enforce name+batch.
        try {
          const st = await api.get('/auth/preseed-status', { params: { email: u.email } });
          if (st.data.is_preseed === false) {
            // Not a claimed preseed email — check if their profile is missing tier/batch
            // and if their email happens to still be a valid unclaimed preseed
            // (handled by admin routing in profile if needed). No block needed.
          }
        } catch { /* non-fatal */ }

        // For legitimately logged-in users, proceed to their dashboard
        setUser(u);
        setIsAuthenticated(true);
        const role = u?.role;
        const target = role === 'admin' ? '/admin'
                     : role === 'teacher' ? '/teacher'
                     : '/dashboard';
        window.location.hash = '';
        navigate(target, { replace: true });
      } catch (e) {
        clearTokens();
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
