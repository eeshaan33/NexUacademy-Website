import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../utils/api';

const PAGE_NAMES = {
  '/': 'Landing',
  '/login': 'Login',
  '/signup': 'Signup',
  '/dashboard': 'Dashboard',
  '/admin': 'Admin Panel',
  '/analytics': 'Student Analytics',
  '/bookmarks': 'Bookmarks',
  '/my-tests': 'My Tests',
  '/assigned-tests': 'Assigned Tests',
  '/pyq': 'PYQ Bank',
  '/classes': 'Student Classes',
  '/teacher/dashboard': 'Teacher Dashboard',
  '/teacher/classes': 'Teacher Classes',
  '/teacher/tests': 'Teacher Tests',
  '/teacher/students': 'Teacher Students',
};

function detectDevice() {
  if (typeof navigator === 'undefined') return 'unknown';
  const ua = navigator.userAgent.toLowerCase();
  if (/mobile|android|iphone|ipod/.test(ua)) return 'mobile';
  if (/ipad|tablet/.test(ua)) return 'tablet';
  return 'desktop';
}

/**
 * Fires a /api/analytics/pageview record on every route change.
 * Silent — never blocks the UI.
 */
const PageViewTracker = () => {
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname;
    // Best-effort match: exact → prefix
    let page = PAGE_NAMES[path];
    if (!page) {
      const prefix = Object.keys(PAGE_NAMES).find((p) => p !== '/' && path.startsWith(p));
      page = prefix ? PAGE_NAMES[prefix] : path;
    }
    api.post('/analytics/pageview', {
      path,
      page,
      referrer: document.referrer || '',
      device: detectDevice(),
    }).catch(() => { /* silent */ });
  }, [location.pathname]);

  return null;
};

export default PageViewTracker;
