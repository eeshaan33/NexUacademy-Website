import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Radio, X } from 'lucide-react';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';

/**
 * Sticky red pulsing banner that appears when any class assigned to the
 * student's batch is currently is_live=true. Polls every 30s.
 * Dismissable for the current session (per class_id).
 */
const DISMISS_KEY = 'nx_dismissed_live_ids';

const LiveNowBanner = () => {
  const { user, isAuthenticated } = useAuth();
  const [live, setLive] = useState([]);
  const [dismissed, setDismissed] = useState(() => {
    try { return new Set(JSON.parse(sessionStorage.getItem(DISMISS_KEY) || '[]')); }
    catch { return new Set(); }
  });

  const fetchLive = useCallback(async () => {
    if (!isAuthenticated || user?.role !== 'student') return;
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
    try {
      const r = await api.get('/student/live-classes/');
      const liveOnes = (r.data.classes || []).filter(c => c.is_live);
      setLive(liveOnes);
    } catch { /* ignore */ }
  }, [isAuthenticated, user]);

  useEffect(() => {
    fetchLive();
    const iv = setInterval(fetchLive, 30000);
    return () => clearInterval(iv);
  }, [fetchLive]);

  const dismiss = (classId) => {
    const next = new Set(dismissed);
    next.add(classId);
    setDismissed(next);
    try { sessionStorage.setItem(DISMISS_KEY, JSON.stringify([...next])); } catch { /* ignore */ }
  };

  const visible = live.filter(c => !dismissed.has(c.class_id));
  if (visible.length === 0) return null;

  const primary = visible[0];
  const extra = visible.length - 1;

  return (
    <div
      className="sticky top-16 z-40 mx-3 md:mx-6 mt-2 rounded-lg overflow-hidden shadow-lg"
      data-testid="live-now-banner"
      role="alert"
      aria-live="polite"
    >
      <div className="bg-gradient-to-r from-red-600 via-red-500 to-red-600 text-white flex items-center justify-between gap-3 px-4 py-2.5">
        <div className="flex items-center gap-2 min-w-0">
          <span className="relative flex h-3 w-3 flex-shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-white" />
          </span>
          <Radio className="h-4 w-4 flex-shrink-0" />
          <div className="min-w-0">
            <span className="font-semibold mr-2 text-sm uppercase tracking-wide">Live now</span>
            <span className="text-sm md:text-base font-medium truncate" data-testid="live-banner-title">
              {primary.title}
            </span>
            {extra > 0 && (
              <span className="ml-2 text-xs bg-white/20 rounded-full px-2 py-0.5">
                +{extra} more
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Link
            to="/live-classes"
            className="bg-white text-red-600 hover:bg-red-50 font-semibold text-sm px-4 py-1.5 rounded-md transition"
            data-testid="live-banner-join-btn"
          >
            Join Now →
          </Link>
          <button
            onClick={() => dismiss(primary.class_id)}
            className="text-white/80 hover:text-white p-1 rounded transition"
            aria-label="Dismiss"
            data-testid="live-banner-dismiss-btn"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default LiveNowBanner;
