import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Users, BookOpen, Video, Megaphone, IndianRupee, TrendingUp } from 'lucide-react';
import api from '../utils/api';

const Stat = ({ icon: Icon, label, value, hint }) => (
  <Card className="bg-slate-800 border-slate-700">
    <CardContent className="p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase text-slate-400 tracking-wide">{label}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
          {hint && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
        </div>
        <div className="w-11 h-11 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </CardContent>
  </Card>
);

const AdminAnalyticsPane = () => {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.get('/analytics/admin/overview').then(r => setData(r.data)).catch(() => {});
  }, []);
  if (!data) return <p className="text-center text-slate-500 py-8">Loading...</p>;
  const { stats, batches, recent_signups, recent_payments } = data;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat icon={Users}     label="Students"      value={stats.total_students} />
        <Stat icon={Users}     label="Teachers"      value={stats.total_teachers} />
        <Stat icon={Video}     label="Classes"       value={stats.total_classes} />
        <Stat icon={BookOpen}  label="Tests"         value={stats.total_tests} />
        <Stat icon={Megaphone} label="Announcements" value={stats.total_announcements} />
        <Stat icon={IndianRupee} label="Revenue"     value={`₹${(stats.revenue_inr || 0).toLocaleString('en-IN')}`} hint={`${stats.paid_students} paid students`} />
      </div>
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2"><TrendingUp className="h-5 w-5 text-amber-500" /> Batch Distribution</CardTitle>
          <CardDescription className="text-slate-400">Students per batch</CardDescription>
        </CardHeader>
        <CardContent>
          {batches.length === 0 ? (
            <p className="text-slate-500 text-center py-4 text-sm">No batches yet.</p>
          ) : (
            <div className="space-y-2">
              {batches.map(b => (
                <div key={b.id} className="flex items-center justify-between p-3 bg-slate-700/50 border border-slate-600 rounded-lg">
                  <div>
                    <p className="text-white font-medium">{b.name}</p>
                    <p className="font-mono text-xs text-amber-300">{b.code}</p>
                  </div>
                  <Badge className="bg-indigo-500/20 text-indigo-200 border-indigo-500/30">{b.students} student{b.students !== 1 ? 's' : ''}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader><CardTitle className="text-white text-base">Recent Signups</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {recent_signups.length === 0 ? <p className="text-slate-500 text-sm text-center">No signups yet.</p> :
              recent_signups.map(u => (
                <div key={u.id} className="flex items-center justify-between text-sm">
                  <div>
                    <p className="text-white">{u.name}</p>
                    <p className="text-slate-400 text-xs">{u.email}</p>
                  </div>
                  <Badge className="bg-slate-700 text-slate-300 border-slate-600 font-mono">{u.batch_id || '—'}</Badge>
                </div>
              ))}
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader><CardTitle className="text-white text-base">Recent Payments</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {recent_payments.length === 0 ? <p className="text-slate-500 text-sm text-center">No payments yet.</p> :
              recent_payments.map(p => (
                <div key={p.payment_id} className="flex items-center justify-between text-sm">
                  <div>
                    <p className="text-white">₹{(p.amount / 100).toLocaleString('en-IN')}</p>
                    <p className="text-slate-400 text-xs">{p.plan}</p>
                  </div>
                  <Badge className={
                    p.status === 'paid' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : p.status === 'failed' ? 'bg-red-500/20 text-red-300 border-red-500/30'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/30'}>
                    {p.status}
                  </Badge>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminAnalyticsPane;
