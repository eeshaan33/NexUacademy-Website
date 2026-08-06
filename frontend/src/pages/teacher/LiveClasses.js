import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Video, Play, StopCircle, Trash2, Hand, Users, Clock, Loader2, X } from 'lucide-react';
import api from '../../utils/api';
import { toast } from 'sonner';
import { setPageTitle } from '../../utils/pageTitle';
import ZoomMeetingEmbed from '../../components/live/ZoomMeetingEmbed';

const SUBJECTS = ['Physics', 'Chemistry', 'Mathematics', 'Biology'];

const RaisedHandsPanel = ({ classId, onLower }) => {
  const [data, setData] = useState({ raised_hands: [], participants: [], is_live: false });
  const [open, setOpen] = useState(true);

  useEffect(() => {
    if (!classId) return;
    let alive = true;
    const tick = async () => {
      try {
        const r = await api.get(`/teacher/live-classes/${classId}/participants`);
        if (alive) setData(r.data);
      } catch { /* ignore */ }
    };
    tick();
    const int = setInterval(tick, 5000);
    return () => { alive = false; clearInterval(int); };
  }, [classId]);

  const hands = data.raised_hands || [];

  return (
    <div className="fixed top-20 right-6 z-[70] w-80 max-w-[92vw]" data-testid="raised-hands-panel">
      <div className="bg-white shadow-2xl rounded-lg border border-slate-200 overflow-hidden">
        <button
          className="w-full flex items-center justify-between px-4 py-3 bg-indigo-600 text-white"
          onClick={() => setOpen(!open)}
          data-testid="hands-toggle-btn"
        >
          <div className="flex items-center gap-2">
            <Hand className="h-4 w-4" />
            <span className="font-medium">{hands.length} hand{hands.length !== 1 ? 's' : ''} raised</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <Users className="h-3 w-3" />
            {(data.participants || []).length}
          </div>
        </button>
        {open && (
          <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
            {hands.length === 0 ? (
              <p className="p-4 text-sm text-slate-400 text-center">No hands raised yet.</p>
            ) : hands.map((h) => (
              <div key={h.student_id} className="flex items-center justify-between p-3 hover:bg-slate-50" data-testid={`hand-${h.student_id}`}>
                <div>
                  <p className="font-medium text-slate-800 text-sm">{h.student_name}</p>
                  <p className="text-xs text-slate-500">{new Date(h.raised_at).toLocaleTimeString()}</p>
                </div>
                <Button size="sm" variant="outline" onClick={() => onLower(h.student_id)} data-testid={`ack-hand-${h.student_id}`}>
                  Acknowledge
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const TeacherLiveClasses = () => {
  const [classes, setClasses] = useState([]);
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [starting, setStarting] = useState('');
  const [session, setSession] = useState(null); // { signature, sdkKey, meetingNumber, password, userName, isHost, zak, classId }
  const [form, setForm] = useState({
    title: '', subject: 'Chemistry', chapter: '', description: '',
    scheduled_date: '', scheduled_time: '', duration: 60,
    assigned_batches: [],
  });

  useEffect(() => { setPageTitle('Live Classes'); }, []);

  const fetchClasses = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get('/teacher/classes/my-classes');
      // Filter to Zoom-enabled classes only
      setClasses((r.data.classes || []).filter(c => c.zoom_meeting_id || c.meeting_platform === 'Zoom'));
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchClasses();
    api.get('/batches/').then(r => setBatches(r.data.batches || [])).catch(() => {});
  }, [fetchClasses]);

  const toggleBatch = (id) => {
    setForm(prev => ({
      ...prev,
      assigned_batches: prev.assigned_batches.includes(id)
        ? prev.assigned_batches.filter(x => x !== id)
        : [...prev.assigned_batches, id],
    }));
  };

  const submitCreate = async (e) => {
    e.preventDefault();
    if (!form.title || !form.scheduled_date || !form.scheduled_time || form.assigned_batches.length === 0) {
      toast.error('Please fill title, date, time and pick at least one batch');
      return;
    }
    setCreating(true);
    try {
      const r = await api.post('/teacher/live-classes/create', form);
      toast.success('Live class scheduled and Zoom meeting created');
      setForm({ title: '', subject: 'Chemistry', chapter: '', description: '', scheduled_date: '', scheduled_time: '', duration: 60, assigned_batches: [] });
      fetchClasses();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to schedule');
    }
    setCreating(false);
  };

  const startClass = async (cls) => {
    setStarting(cls.class_id);
    try {
      const r = await api.post(`/teacher/live-classes/${cls.class_id}/start`);
      setSession({
        signature: r.data.signature,
        sdkKey: r.data.sdk_key,
        meetingNumber: r.data.meeting_number,
        password: r.data.password,
        userName: r.data.user_name,
        zak: r.data.zak,
        isHost: true,
        classId: cls.class_id,
      });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start class');
    }
    setStarting('');
  };

  const endClass = async (classId) => {
    try {
      await api.post(`/teacher/live-classes/${classId}/end`);
      toast.success('Class ended');
      setSession(null);
      fetchClasses();
    } catch (err) {
      toast.error('Failed to end class');
    }
  };

  const deleteClass = async (cls) => {
    if (!window.confirm(`Delete "${cls.title}"? The Zoom meeting will be cancelled.`)) return;
    try {
      await api.delete(`/teacher/live-classes/${cls.class_id}`);
      toast.success('Class deleted');
      fetchClasses();
    } catch { toast.error('Delete failed'); }
  };

  const lowerHand = async (studentId) => {
    if (!session?.classId) return;
    try {
      await api.post(`/teacher/live-classes/${session.classId}/lower-hand/${studentId}`);
    } catch { /* ignore */ }
  };

  // If a session is active, render the embed + raised-hands panel + End button
  if (session) {
    return (
      <>
        <ZoomMeetingEmbed
          sdkKey={session.sdkKey}
          signature={session.signature}
          meetingNumber={session.meetingNumber}
          password={session.password}
          userName={session.userName}
          zak={session.zak}
          isHost={true}
          onMeetingEnd={() => endClass(session.classId)}
        />
        <RaisedHandsPanel classId={session.classId} onLower={lowerHand} />
        <div className="fixed top-6 left-6 z-[70] flex gap-2">
          <Button variant="destructive" onClick={() => endClass(session.classId)} data-testid="end-class-btn">
            <StopCircle className="h-4 w-4 mr-2" /> End Class
          </Button>
        </div>
      </>
    );
  }

  const now = Date.now();

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
          <Video className="h-7 w-7 text-indigo-600" /> Live Classes
        </h1>
        <p className="text-slate-500 mt-1">Schedule and run Zoom classes directly on the platform.</p>
      </div>

      {/* Schedule form */}
      <Card>
        <CardHeader>
          <CardTitle>Schedule New Live Class</CardTitle>
          <CardDescription>A Zoom meeting will be created automatically and students in selected batches will be notified.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submitCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2 md:col-span-2">
              <Label>Class Title *</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="e.g. Thermodynamics Deep Dive" data-testid="live-title-input" />
            </div>
            <div className="space-y-2">
              <Label>Subject *</Label>
              <Select value={form.subject} onValueChange={(v) => setForm({ ...form, subject: v })}>
                <SelectTrigger data-testid="live-subject-select"><SelectValue /></SelectTrigger>
                <SelectContent>{SUBJECTS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Chapter</Label>
              <Input value={form.chapter} onChange={(e) => setForm({ ...form, chapter: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Date *</Label>
              <Input type="date" value={form.scheduled_date} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })} data-testid="live-date-input" />
            </div>
            <div className="space-y-2">
              <Label>Time *</Label>
              <Input type="time" value={form.scheduled_time} onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })} data-testid="live-time-input" />
            </div>
            <div className="space-y-2">
              <Label>Duration (min)</Label>
              <Input type="number" min={15} max={480} value={form.duration}
                onChange={(e) => setForm({ ...form, duration: Number(e.target.value) })} data-testid="live-duration-input" />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Description</Label>
              <Textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Assigned Batches *</Label>
              <div className="flex flex-wrap gap-2">
                {batches.map(b => (
                  <button key={b.id} type="button"
                    onClick={() => toggleBatch(b.id)}
                    className={`px-3 py-1.5 rounded-full text-sm border transition ${
                      form.assigned_batches.includes(b.id)
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'bg-white text-slate-700 border-slate-300 hover:border-indigo-400'
                    }`}
                    data-testid={`batch-chip-${b.code}`}>
                    {b.name} <span className="font-mono opacity-70">({b.code})</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={creating} className="bg-indigo-600 hover:bg-indigo-700" data-testid="schedule-live-btn">
                {creating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Video className="h-4 w-4 mr-2" />}
                Schedule Class
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Class list */}
      <Card>
        <CardHeader>
          <CardTitle>My Live Classes</CardTitle>
          <CardDescription>Live and upcoming Zoom classes you are hosting.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-slate-400 py-6">Loading...</p>
          ) : classes.length === 0 ? (
            <p className="text-center text-slate-400 py-8">No live classes yet — schedule one above.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {classes.map(c => {
                const scheduledMs = new Date(c.scheduled_date_time).getTime();
                const canStart = scheduledMs - now < 10 * 60 * 1000; // within 10 min or past
                return (
                  <div key={c.class_id} className="p-4 border rounded-lg bg-white" data-testid={`live-class-card-${c.class_id}`}>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="font-semibold text-slate-900">{c.title}</h3>
                        <p className="text-xs text-slate-500">{c.subject}{c.chapter ? ` · ${c.chapter}` : ''}</p>
                      </div>
                      {c.is_live ? <Badge className="bg-red-500 text-white animate-pulse">🔴 LIVE</Badge> : <Badge variant="outline">{c.status || 'upcoming'}</Badge>}
                    </div>
                    <div className="mt-3 space-y-1 text-sm text-slate-600">
                      <p className="flex items-center gap-2"><Clock className="h-3 w-3" /> {new Date(c.scheduled_date_time).toLocaleString()} · {c.duration} min</p>
                      <p className="flex items-center gap-2"><Users className="h-3 w-3" /> {(c.assigned_batches || []).join(', ')}</p>
                    </div>
                    <div className="mt-3 flex gap-2">
                      <Button size="sm" disabled={!canStart || starting === c.class_id}
                        onClick={() => startClass(c)}
                        className="bg-green-600 hover:bg-green-700"
                        data-testid={`start-class-${c.class_id}`}>
                        {starting === c.class_id ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Play className="h-3 w-3 mr-1" />}
                        {c.is_live ? 'Rejoin' : 'Start Class'}
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => deleteClass(c)} data-testid={`delete-class-${c.class_id}`}>
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                    {!canStart && !c.is_live && (
                      <p className="text-xs text-slate-400 mt-2">Start button unlocks 10 min before scheduled time.</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TeacherLiveClasses;
