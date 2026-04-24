import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Checkbox } from '../../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Plus, Trash2, Edit, Video, Calendar, Clock, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';
import BatchManagerDialog from '../../components/BatchManagerDialog';

const SUBJECTS = ['Physics', 'Chemistry', 'Mathematics', 'General'];
const PLATFORMS = ['Zoom', 'Google Meet', 'Microsoft Teams'];
const DURATIONS = [30, 45, 60, 90, 120, 180];

const ManageClasses = () => {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    setPageTitle('Manage Classes');
  }, []);
  const [batches, setBatches] = useState([]);
  const [form, setForm] = useState({
    title: '', subject: 'Physics', chapter: '', topic: '',
    meeting_link: '', meeting_platform: 'Zoom',
    scheduled_date: '', scheduled_time: '', duration: '60',
    assigned_batches: [], description: '', prerequisites: '',
  });

  useEffect(() => {
    loadClasses();
    loadBatches();
  }, []);

  const loadClasses = async () => {
    try {
      const res = await api.get('/teacher/classes/');
      setClasses(res.data.classes || []);
    } catch { toast.error('Failed to load classes'); }
    finally { setLoading(false); }
  };

  const loadBatches = async () => {
    try {
      const res = await api.get('/batches/');
      setBatches(res.data.batches || []);
    } catch { }
  };

  const handleBatchToggle = (batchId) => {
    setForm((prev) => ({
      ...prev,
      assigned_batches: prev.assigned_batches.includes(batchId)
        ? prev.assigned_batches.filter((b) => b !== batchId)
        : [...prev.assigned_batches, batchId],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title || !form.meeting_link || !form.scheduled_date || !form.scheduled_time || form.assigned_batches.length === 0) {
      toast.error('Please fill all required fields and select at least one batch');
      return;
    }
    try {
      const res = await api.post('/teacher/classes/create', form);
      toast.success(res.data.message);
      setShowForm(false);
      setForm({ title: '', subject: 'Physics', chapter: '', topic: '', meeting_link: '', meeting_platform: 'Zoom', scheduled_date: '', scheduled_time: '', duration: '60', assigned_batches: [], description: '', prerequisites: '' });
      loadClasses();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create class');
    }
  };

  const handleDelete = async (classId) => {
    if (!window.confirm('Delete this class?')) return;
    try {
      await api.delete(`/teacher/classes/${classId}`);
      toast.success('Class deleted');
      loadClasses();
    } catch { toast.error('Failed to delete'); }
  };

  const formatDate = (dt) => {
    if (!dt) return '';
    return new Date(dt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  };

  const statusColors = { upcoming: 'bg-blue-100 text-blue-700', ongoing: 'bg-green-100 text-green-700', completed: 'bg-slate-100 text-slate-600', cancelled: 'bg-red-100 text-red-700' };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6" data-testid="manage-classes-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Manage Classes</h1>
          <p className="text-slate-500 text-sm mt-1">Schedule and manage live class sessions</p>
        </div>
        <Dialog open={showForm} onOpenChange={setShowForm}>
          <DialogTrigger asChild>
            <Button className="bg-indigo-600 hover:bg-indigo-700" data-testid="schedule-class-btn">
              <Plus className="h-4 w-4 mr-2" /> Schedule New Class
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Schedule New Class</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Title *</Label>
                <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Kinematics - Part 1" data-testid="class-title-input" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Subject *</Label>
                  <Select value={form.subject} onValueChange={(v) => setForm({ ...form, subject: v })}>
                    <SelectTrigger data-testid="class-subject-select"><SelectValue /></SelectTrigger>
                    <SelectContent>{SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Platform</Label>
                  <Select value={form.meeting_platform} onValueChange={(v) => setForm({ ...form, meeting_platform: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{PLATFORMS.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Meeting Link *</Label>
                <Input value={form.meeting_link} onChange={(e) => setForm({ ...form, meeting_link: e.target.value })} placeholder="https://zoom.us/j/..." data-testid="class-link-input" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-2">
                  <Label>Date *</Label>
                  <Input type="date" value={form.scheduled_date} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })} data-testid="class-date-input" />
                </div>
                <div className="space-y-2">
                  <Label>Time *</Label>
                  <Input type="time" value={form.scheduled_time} onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })} data-testid="class-time-input" />
                </div>
                <div className="space-y-2">
                  <Label>Duration</Label>
                  <Select value={form.duration} onValueChange={(v) => setForm({ ...form, duration: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{DURATIONS.map((d) => <SelectItem key={d} value={String(d)}>{d} min</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Assign to Batches *</Label>
                  <BatchManagerDialog batches={batches} onBatchesChanged={loadBatches} />
                </div>
                <div className="grid grid-cols-2 gap-2 p-3 border rounded-lg bg-slate-50">
                  {batches.map((b) => (
                    <label key={b.id} className="flex items-center space-x-2 cursor-pointer">
                      <Checkbox
                        checked={form.assigned_batches.includes(b.id)}
                        onCheckedChange={() => handleBatchToggle(b.id)}
                        data-testid={`batch-${b.id}`}
                      />
                      <span className="text-sm">{b.name}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <textarea className="w-full border rounded-lg p-2 text-sm min-h-[60px] resize-none" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Optional class description..." />
              </div>
              <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700" data-testid="submit-class-btn">
                Schedule & Notify Students
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading classes...</div>
      ) : classes.length === 0 ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="py-12 text-center">
            <Video className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No classes scheduled yet</p>
            <p className="text-sm text-slate-400 mt-1">Click "Schedule New Class" to get started</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {classes.map((cls) => (
            <Card key={cls.class_id} className="border-0 shadow-sm hover:shadow-md transition-shadow" data-testid={`class-card-${cls.class_id}`}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-slate-900">{cls.title}</h3>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusColors[cls.status] || statusColors.upcoming}`}>
                        {cls.status}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                      <span className="flex items-center gap-1"><BookmarkIcon />{cls.subject}</span>
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{formatDate(cls.scheduled_date_time)}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{cls.duration} min</span>
                      <span className="flex items-center gap-1"><Video className="h-3.5 w-3.5" />{cls.meeting_platform}</span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(cls.assigned_batches || []).map((b) => (
                        <span key={b} className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{b}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {cls.meeting_link && (
                      <a href={cls.meeting_link} target="_blank" rel="noreferrer">
                        <Button variant="outline" size="sm"><ExternalLink className="h-3.5 w-3.5" /></Button>
                      </a>
                    )}
                    <Button variant="outline" size="sm" onClick={() => handleDelete(cls.class_id)} data-testid={`delete-class-${cls.class_id}`}>
                      <Trash2 className="h-3.5 w-3.5 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

const BookmarkIcon = () => (
  <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

export default ManageClasses;
