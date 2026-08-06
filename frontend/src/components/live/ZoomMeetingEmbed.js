import React, { useEffect, useRef, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';

/**
 * Full-screen embedded Zoom Meeting SDK (Client View).
 *
 * Loads @zoom/meetingsdk lazily so it doesn't slow the initial bundle.
 * Injects the meeting UI into #zmmtg-root (Zoom's expected container).
 */
const ZoomMeetingEmbed = ({
  sdkKey,
  signature,
  meetingNumber,
  password,
  userName,
  isHost = false,
  zak = '',
  onMeetingEnd = () => {},
}) => {
  const [joining, setJoining] = useState(true);
  const [error, setError] = useState('');
  const initedRef = useRef(false);

  useEffect(() => {
    if (initedRef.current) return;
    initedRef.current = true;

    let cancelled = false;

    (async () => {
      try {
        const { ZoomMtg } = await import('@zoom/meetingsdk');

        // Ensure Zoom's root exists and is visible
        let root = document.getElementById('zmmtg-root');
        if (!root) {
          root = document.createElement('div');
          root.id = 'zmmtg-root';
          document.body.appendChild(root);
        }
        root.style.display = 'block';

        ZoomMtg.preLoadWasm();
        ZoomMtg.prepareWebSDK();
        ZoomMtg.i18n.load('en-US');
        ZoomMtg.i18n.reload('en-US');

        ZoomMtg.init({
          leaveUrl: window.location.origin + (isHost ? '/teacher/live-classes' : '/live-classes'),
          patchJsMedia: true,
          leaveOnPageUnload: true,
          success: () => {
            if (cancelled) return;
            const joinOpts = {
              signature,
              sdkKey,
              meetingNumber: String(meetingNumber),
              passWord: password || '',
              userName: userName || 'Student',
              success: () => setJoining(false),
              error: (err) => {
                console.error('Zoom join error:', err);
                setError(err?.errorMessage || 'Failed to join the class. Please refresh and try again.');
                setJoining(false);
              },
            };
            if (isHost && zak) joinOpts.zak = zak;
            ZoomMtg.join(joinOpts);
          },
          error: (err) => {
            console.error('Zoom init error:', err);
            setError(err?.errorMessage || 'Failed to load the meeting.');
            setJoining(false);
          },
        });
      } catch (e) {
        console.error('Zoom SDK failed to load:', e);
        setError('Zoom SDK failed to load. Please check your connection.');
        setJoining(false);
      }
    })();

    return () => {
      cancelled = true;
      try {
        import('@zoom/meetingsdk').then(({ ZoomMtg }) => {
          try { ZoomMtg.leaveMeeting({}); } catch { /* ignore */ }
        });
      } catch { /* ignore */ }
      const root = document.getElementById('zmmtg-root');
      if (root) root.style.display = 'none';
      onMeetingEnd();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-black" data-testid="zoom-embed">
      {joining && (
        <div className="absolute inset-0 flex items-center justify-center z-[60] bg-slate-900/95">
          <div className="text-center text-white">
            <Loader2 className="h-10 w-10 animate-spin mx-auto mb-4 text-indigo-400" />
            <p className="text-lg font-medium">Joining class{isHost ? ' as host' : ''}...</p>
            <p className="text-sm text-slate-400 mt-1">This can take a few seconds.</p>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center z-[60] bg-slate-900/95 p-6">
          <div className="max-w-md text-center text-white">
            <p className="text-red-400 mb-4">{error}</p>
            <div className="flex gap-2 justify-center">
              <Button variant="outline" onClick={() => window.location.reload()} data-testid="zoom-retry-btn">Retry</Button>
              <Button onClick={onMeetingEnd} data-testid="zoom-close-btn">
                <X className="h-4 w-4 mr-1" /> Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ZoomMeetingEmbed;
