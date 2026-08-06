import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Video, Play, Hand, Clock, User, Loader2 } from 'lucide-react';
import api from '../../utils/api';
import { toast } from 'sonner';
import { setPageTitle } from '../../utils/pageTitle';
import ZoomMeetingEmbed from '../../components/live/ZoomMeetingEmbed';

const RaiseHandButton = ({ classId }) => {
  const [raised, setRaised] = useState(false);
  const [loading, setLoading] = useState(false);

  const toggle = async () => {
    setLoading(true);
    try {
      if (raised) {
        await api.post(`/student/live-classes/${classId}/lower-hand`);
        setRaised(false);
        toast.success('Hand lowered');
      } else {
        await api.post(`/student/live-classes/${classId}/raise-hand`);
        setRaised(true);
        toast.success('Hand raised — teacher notified');
      }
    } catch {
      toast.error('Failed');
    }
    setLoading(false);
  };

  return (
    <div className="fixed bottom-6 right-6 z-[70]" data-testid="raise-hand-floater">
      <Button
        onClick={toggle}
        disabled={loading}
        className={`shadow-2xl rounded-full h-14 px-5 text-base font-semibold transition-all ${
          raised ? 'bg-yellow-500 hover:bg-yellow-600 animate-pulse' : 'bg-indigo-600 hover:bg-indigo-700'
        }`}
        data-testid="raise-hand-btn"
      >
        {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Hand className="h-5 w-5 mr-2" />}
        {raised ? 'Hand Raised (tap to lower)' : 'Raise Hand'}
      </Button>
    </div>
  );
};

const StudentLiveClasses = () => {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState('');
  const [session, setSession] = useState(null);

  useEffect(() => { setPageTitle('Live Classes'); }, []);

  const fetchClasses = useCallback(async () => {
    try {
      const r = await api.get('/student/live-classes/');
      setClasses(r.data.classes || []);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchClasses();
    // Poll every 15s so "Join" appears as soon as teacher starts
    const int = setInterval(fetchClasses, 15000);
    return () => clearInterval(int);
  }, [fetchClasses]);

  const joinClass = async (cls) => {
    setJoining(cls.class_id);
    try {
      const r = await api.get(`/student/live-classes/${cls.class_id}/join`);
      setSession({
        signature: r.data.signature,
        sdkKey: r.data.sdk_key,
        meetingNumber: r.data.meeting_number,
        password: r.data.password,
        userName: r.data.user_name,
        isHost: false,
        classId: cls.class_id,
      });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Cannot join class');
    }
    setJoining('');
  };

  const leaveClass = () => {
    setSession(null);
    fetchClasses();
  };

  if (session) {
    return (
      <>
        <ZoomMeetingEmbed
          sdkKey={session.sdkKey}
          signature={session.signature}
          meetingNumber={session.meetingNumber}
          password={session.password}
          userName={session.userName}
          isHost={false}
          onMeetingEnd={leaveClass}
        />
        <RaiseHandButton classId={session.classId} />
      </>
    );
  }

  const now = Date.now();
  const enriched = classes.map(c => {
    const start = new Date(c.scheduled_date_time).getTime();
    const end = start + (c.duration || 60) * 60 * 1000;
    let phase = 'upcoming';
    if (c.is_live) phase = 'live';
    else if (end < now) phase = 'ended';
    return { ...c, phase };
  }).sort((a, b) => (a.phase === 'live' ? -1 : b.phase === 'live' ? 1 : new Date(a.scheduled_date_time) - new Date(b.scheduled_date_time)));

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
          <Video className="h-7 w-7 text-indigo-600" /> Live Classes
        </h1>
        <p className="text-slate-500 mt-1">Your live and upcoming Zoom classes.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Scheduled Classes</CardTitle>
          <CardDescription>The Join button will appear the moment your teacher starts the class.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-slate-400 py-6">Loading...</p>
          ) : enriched.length === 0 ? (
            <p className="text-center text-slate-400 py-8">No live classes for your batch yet.</p>
          ) : (
            <div className="space-y-3">
              {enriched.map(c => (
                <div key={c.class_id} className="p-4 border rounded-lg bg-white flex flex-col md:flex-row md:items-center gap-3"
                  data-testid={`student-class-${c.class_id}`}>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-slate-900">{c.title}</h3>
                      {c.phase === 'live' && <Badge className="bg-red-500 text-white animate-pulse" data-testid={`live-badge-${c.class_id}`}>🔴 LIVE NOW</Badge>}
                      {c.phase === 'upcoming' && <Badge variant="outline">Upcoming</Badge>}
                      {c.phase === 'ended' && <Badge variant="secondary">Ended</Badge>}
                    </div>
                    <div className="mt-1 text-sm text-slate-500 flex flex-wrap gap-3">
                      <span className="flex items-center gap-1"><User className="h-3 w-3" /> {c.teacher_name}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {new Date(c.scheduled_date_time).toLocaleString()}</span>
                      <span>{c.subject}{c.chapter ? ` · ${c.chapter}` : ''}</span>
                    </div>
                  </div>
                  {c.phase === 'live' && (
                    <Button
                      onClick={() => joinClass(c)}
                      disabled={joining === c.class_id}
                      className="bg-green-600 hover:bg-green-700"
                      data-testid={`join-class-${c.class_id}`}
                    >
                      {joining === c.class_id ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
                      Join Class
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentLiveClasses;
