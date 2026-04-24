import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { Eye, Users, MessageSquare, Download, RefreshCw, TrendingUp, Trash2, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import api from '../utils/api';

const COLORS = ['#1B3A52', '#3B5F82', '#14B8A6', '#F97316', '#8B5CF6', '#10B981'];
const STATUSES = ['New', 'In Review', 'Planned', 'In Progress', 'Completed', 'Rejected'];
const PRIORITIES = ['Low', 'Medium', 'High', 'Urgent'];

const statusTint = {
  'New': 'bg-blue-100 text-blue-700',
  'In Review': 'bg-yellow-100 text-yellow-700',
  'Planned': 'bg-purple-100 text-purple-700',
  'In Progress': 'bg-orange-100 text-orange-700',
  'Completed': 'bg-green-100 text-green-700',
  'Rejected': 'bg-red-100 text-red-700',
};
const priorityTint = {
  'Low': 'bg-slate-100 text-slate-700',
  'Medium': 'bg-blue-100 text-blue-700',
  'High': 'bg-orange-100 text-orange-700',
  'Urgent': 'bg-red-100 text-red-700',
};

const Stat = ({ icon: Icon, label, value, tint }) => (
  <Card className="bg-slate-800 border-slate-700">
    <CardContent className="p-4 flex items-center justify-between">
      <div>
        <p className="text-slate-400 text-xs uppercase tracking-wide">{label}</p>
        <p className="text-3xl font-bold text-white mt-1">{(value ?? 0).toLocaleString()}</p>
      </div>
      <div className={`${tint} p-3 rounded-xl`}><Icon className="h-5 w-5 text-white" /></div>
    </CardContent>
  </Card>
);

const AdminAnalyticsPane = () => {
  const [days, setDays] = useState(30);
  const [overview, setOverview] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [filters, setFilters] = useState({ status: 'all', priority: 'all' });
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const [o, u, s] = await Promise.all([
        api.get(`/admin/dashboard/overview?days=${days}`),
        api.get('/admin/dashboard/users'),
        api.get('/admin/dashboard/suggestions', {
          params: {
            status: filters.status === 'all' ? undefined : filters.status,
            priority: filters.priority === 'all' ? undefined : filters.priority,
          },
        }),
      ]);
      setOverview(o.data);
      setUserStats(u.data);
      setSuggestions(s.data.suggestions || []);
    } catch (e) {
      toast.error('Failed to load analytics');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [days, filters]); // eslint-disable-line

  const exportCsv = () => {
    const rows = overview?.pageVisits || [];
    const header = 'Page,Total Visits,Unique Visitors\n';
    const body = rows.map((r) => `"${r._id}",${r.totalVisits},${r.uniqueVisitors}`).join('\n');
    const blob = new Blob([header + body], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const updateSuggestion = async (id, patch) => {
    try {
      await api.put(`/admin/dashboard/suggestions/${id}`, patch);
      toast.success('Updated');
      load();
      setSelected(null);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed');
    }
  };

  const deleteSuggestion = async (id) => {
    if (!window.confirm('Delete this suggestion?')) return;
    try {
      await api.delete(`/admin/dashboard/suggestions/${id}`);
      toast.success('Deleted');
      setSelected(null);
      load();
    } catch { toast.error('Failed'); }
  };

  if (loading && !overview) {
    return <div className="py-12 text-center text-slate-400"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></div>;
  }

  return (
    <div className="space-y-5" data-testid="admin-analytics-pane">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-2 items-center">
          <Select value={String(days)} onValueChange={(v) => setDays(Number(v))}>
            <SelectTrigger className="bg-slate-800 border-slate-600 text-white w-[160px]" data-testid="days-filter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="365">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={load} className="border-slate-600 text-slate-300 hover:bg-slate-800">
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
        </div>
        <Button onClick={exportCsv} size="sm" className="bg-emerald-600 hover:bg-emerald-700" data-testid="export-csv">
          <Download className="h-4 w-4 mr-1" /> Export CSV
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat icon={Eye} label="Total Visits" value={overview?.total_visits} tint="bg-blue-500" />
        <Stat icon={Users} label="Unique Visitors" value={overview?.unique_visitors} tint="bg-purple-500" />
        <Stat icon={Users} label="Total Users" value={userStats?.totalUsers} tint="bg-emerald-500" />
        <Stat icon={MessageSquare} label="New Suggestions" value={suggestions.filter((s) => s.status === 'New').length} tint="bg-amber-500" />
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-slate-200">Most Visited Pages</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={overview?.pageVisits || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="_id" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9' }} />
                <Legend />
                <Bar dataKey="totalVisits" fill="#3B5F82" name="Total" />
                <Bar dataKey="uniqueVisitors" fill="#14B8A6" name="Unique" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-slate-200">Daily Traffic</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={overview?.dailyTrends || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="_id" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9' }} />
                <Legend />
                <Line type="monotone" dataKey="visits" stroke="#F97316" strokeWidth={2} dot={false} name="Visits" />
                <Line type="monotone" dataKey="uniqueVisitors" stroke="#14B8A6" strokeWidth={2} dot={false} name="Unique" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-slate-200">Device Breakdown</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={overview?.deviceBreakdown || []} dataKey="count" nameKey="_id" cx="50%" cy="50%" outerRadius={90} label>
                  {(overview?.deviceBreakdown || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-slate-200">Batch Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={userStats?.batchDistribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="_id" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9' }} />
                <Bar dataKey="count" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Suggestions */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
          <CardTitle className="text-sm text-slate-200 flex items-center gap-2">
            <MessageSquare className="h-4 w-4" /> Student Suggestions
          </CardTitle>
          <div className="flex gap-2">
            <Select value={filters.status} onValueChange={(v) => setFilters({ ...filters, status: v })}>
              <SelectTrigger className="bg-slate-700 border-slate-600 text-white w-[150px] h-8" data-testid="sug-status-filter"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All status</SelectItem>
                {STATUSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={filters.priority} onValueChange={(v) => setFilters({ ...filters, priority: v })}>
              <SelectTrigger className="bg-slate-700 border-slate-600 text-white w-[140px] h-8"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All priority</SelectItem>
                {PRIORITIES.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {suggestions.length === 0 ? (
            <p className="text-slate-400 text-sm py-6 text-center">No suggestions yet.</p>
          ) : suggestions.map((s) => (
            <div
              key={s.suggestion_id}
              onClick={() => setSelected(s)}
              className={`p-3 rounded-lg cursor-pointer border ${s.is_read ? 'border-slate-700 bg-slate-700/30' : 'border-indigo-500/40 bg-indigo-500/10'} hover:bg-slate-700/50 transition`}
              data-testid={`suggestion-row-${s.suggestion_id}`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium truncate">{s.subject}</span>
                    {!s.is_read && <Badge className="bg-indigo-500 text-white text-[10px]">NEW</Badge>}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {s.student_name} · {new Date(s.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${statusTint[s.status]}`}>{s.status}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${priorityTint[s.priority]}`}>{s.priority}</span>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <SuggestionDetailDialog
        suggestion={selected}
        onClose={() => setSelected(null)}
        onUpdate={updateSuggestion}
        onDelete={deleteSuggestion}
      />
    </div>
  );
};

const SuggestionDetailDialog = ({ suggestion, onClose, onUpdate, onDelete }) => {
  const [status, setStatus] = useState('New');
  const [priority, setPriority] = useState('Medium');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (suggestion) {
      setStatus(suggestion.status || 'New');
      setPriority(suggestion.priority || 'Medium');
      setNotes(suggestion.admin_notes || '');
    }
  }, [suggestion]);

  if (!suggestion) return null;

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Suggestion details</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          <div>
            <div className="text-xs text-slate-500">Subject</div>
            <div className="font-semibold text-slate-800">{suggestion.subject}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">From</div>
            <div>{suggestion.student_name} <span className="text-slate-500">({suggestion.student_email})</span></div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Type</div>
            <div>{suggestion.suggestion_type}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Message</div>
            <div className="whitespace-pre-wrap bg-slate-50 rounded p-3 text-slate-700">{suggestion.message}</div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <div className="text-xs text-slate-500 mb-1">Status</div>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger data-testid="dialog-status"><SelectValue /></SelectTrigger>
                <SelectContent>{STATUSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <div className="text-xs text-slate-500 mb-1">Priority</div>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{PRIORITIES.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Admin notes</div>
            <Textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Internal notes" />
          </div>
          <div className="flex gap-2 pt-2">
            <Button
              className="flex-1 bg-indigo-600 hover:bg-indigo-700"
              data-testid="save-suggestion"
              onClick={() => onUpdate(suggestion.suggestion_id, { status, priority, admin_notes: notes, is_read: true })}
            >
              Save
            </Button>
            <Button variant="outline" onClick={() => onDelete(suggestion.suggestion_id)}>
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AdminAnalyticsPane;
