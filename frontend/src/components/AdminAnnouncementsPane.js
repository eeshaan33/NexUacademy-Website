import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Megaphone, Pin, Trash2 } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

const AdminAnnouncementsPane = () => {
  const [items, setItems] = useState([]);
  const [batches, setBatches] = useState([]);
  const [form, setForm] = useState({ title: '', message: '', is_pinned: false, batches: [] });
  const [saving, setSaving] = useState(false);

  const fetchAll = async () => {
    try {
      const [a, b] = await Promise.all([api.get('/announcements/'), api.get('/batches/')]);
      setItems(a.data.announcements || []);
      setBatches(b.data.batches || []);
    } catch { toast.error('Failed to load'); }
  };

  useEffect(() => { fetchAll(); }, []);

  const toggleBatch = (id) => {
    setForm(f => ({
      ...f,
      batches: f.batches.includes(id) ? f.batches.filter(x => x !== id) : [...f.batches, id],
    }));
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!form.title || !form.message || form.batches.length === 0) {
      toast.error('Title, message and at least one batch are required');
      return;
    }
    setSaving(true);
    try {
      await api.post('/announcements/', {
        title: form.title,
        message: form.message,
        assigned_batches: form.batches,
        is_pinned: form.is_pinned,
      });
      toast.success('Announcement posted and students notified');
      setForm({ title: '', message: '', is_pinned: false, batches: [] });
      fetchAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed');
    }
    setSaving(false);
  };

  const del = async (id) => {
    if (!window.confirm('Delete this announcement?')) return;
    try { await api.delete(`/announcements/${id}`); fetchAll(); }
    catch { toast.error('Delete failed'); }
  };

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2"><Megaphone className="h-5 w-5 text-amber-500" /> Post Announcement</CardTitle>
          <CardDescription className="text-slate-400">Reaches every student in the selected batch(es) instantly via bell + in-app.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="grid grid-cols-1 gap-4">
            <div className="space-y-2">
              <Label className="text-slate-300">Title</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="bg-slate-700 border-slate-600 text-white" data-testid="ann-title" />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Message</Label>
              <Textarea rows={3} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })}
                className="bg-slate-700 border-slate-600 text-white" data-testid="ann-message" />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Target Batches</Label>
              <div className="flex flex-wrap gap-2">
                {batches.map(b => (
                  <button key={b.id} type="button" onClick={() => toggleBatch(b.id)}
                    className={`px-3 py-1.5 rounded-full text-sm border ${
                      form.batches.includes(b.id)
                        ? 'bg-amber-500 border-amber-500 text-slate-900'
                        : 'bg-slate-700 border-slate-600 text-slate-200'
                    }`}
                    data-testid={`ann-batch-${b.code}`}>
                    {b.name} <span className="font-mono opacity-70">({b.code})</span>
                  </button>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2 text-slate-200 text-sm">
              <input type="checkbox" checked={form.is_pinned}
                onChange={(e) => setForm({ ...form, is_pinned: e.target.checked })}
                data-testid="ann-pin" />
              <Pin className="h-3 w-3" /> Pin to top of student dashboard
            </label>
            <Button type="submit" disabled={saving} className="bg-amber-500 text-slate-900 w-fit"
              data-testid="ann-submit">
              {saving ? 'Posting...' : 'Post Announcement'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">All Announcements ({items.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <p className="text-slate-500 text-center py-8">Nothing posted yet.</p>
          ) : (
            <div className="space-y-3">
              {items.map(a => (
                <div key={a.announcement_id} className="p-4 bg-slate-700/50 border border-slate-600 rounded-lg"
                  data-testid={`ann-row-${a.announcement_id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {a.is_pinned && <Pin className="h-3 w-3 text-amber-400" />}
                        <h3 className="text-white font-medium">{a.title}</h3>
                      </div>
                      <p className="text-slate-300 mt-1 text-sm whitespace-pre-line">{a.message}</p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {(a.assigned_batches || []).map(b => (
                          <Badge key={b} className="bg-indigo-500/20 text-indigo-200 border-indigo-500/30 font-mono">{b}</Badge>
                        ))}
                      </div>
                      <p className="text-xs text-slate-500 mt-2">{new Date(a.created_at).toLocaleString()} · {a.created_by_name}</p>
                    </div>
                    <Button size="sm" variant="outline" onClick={() => del(a.announcement_id)}
                      className="border-red-500/40 text-red-400 hover:bg-red-500/10"
                      data-testid={`ann-delete-${a.announcement_id}`}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminAnnouncementsPane;
