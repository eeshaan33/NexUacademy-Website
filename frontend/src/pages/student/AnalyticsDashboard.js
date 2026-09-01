import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { BarChart3, Award, BookOpen, Video, Bell, Timer } from 'lucide-react';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';

const Stat = ({ icon: Icon, label, value, color }) => (
  <Card className="border-0 shadow-sm">
    <CardContent className="p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-lg ${color} flex items-center justify-center text-white`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
      </div>
    </CardContent>
  </Card>
);

const StudentAnalytics = () => {
  const [data, setData] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPageTitle('My Analytics');
    (async () => {
      try {
        const [a, b] = await Promise.all([
          api.get('/analytics/dashboard'),
          api.get('/analytics/subject-wise'),
        ]);
        setData(a.data.stats);
        setSubjects(b.data.subjects || []);
      } catch { /* ignore */ }
      setLoading(false);
    })();
  }, []);

  if (loading) return <div className="p-6 text-slate-400 text-center">Loading analytics...</div>;
  if (!data) return <div className="p-6 text-slate-400 text-center">Analytics unavailable.</div>;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6" data-testid="analytics-page">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
          <BarChart3 className="h-7 w-7 text-indigo-600" /> My Analytics
        </h1>
        <p className="text-slate-500 mt-1">Your test performance and class attendance snapshot.</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Stat icon={Award}    label="Tests Taken"        value={data.tests_taken}         color="bg-indigo-500" />
        <Stat icon={Timer}    label="Tests In Progress"  value={data.tests_in_progress}   color="bg-amber-500" />
        <Stat icon={BarChart3} label="Avg Accuracy"      value={`${data.average_accuracy}%`} color="bg-emerald-500" />
        <Stat icon={Video}    label="Total Classes"      value={data.total_classes}       color="bg-blue-500" />
        <Stat icon={Video}    label="Upcoming Classes"   value={data.upcoming_classes}    color="bg-purple-500" />
        <Stat icon={Bell}     label="Unread Notifs"      value={data.unread_notifications} color="bg-rose-500" />
      </div>
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2"><BookOpen className="h-4 w-4 text-indigo-500" /> Subject-wise breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          {subjects.length === 0 ? (
            <p className="text-slate-400 text-center py-6 text-sm">Take a test to see subject-wise analytics.</p>
          ) : (
            <div className="space-y-3">
              {subjects.map((s) => (
                <div key={s.subject} className="p-4 border rounded-lg" data-testid={`subject-${s.subject}`}>
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-slate-900">{s.subject || 'Unspecified'}</h3>
                    <span className="text-sm text-slate-500">{s.attempts} test{s.attempts !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="mt-2 flex items-center gap-3">
                    <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600"
                           style={{ width: `${Math.min(100, Number(s.avg_accuracy) || 0)}%` }} />
                    </div>
                    <span className="text-sm font-semibold text-emerald-700 w-14 text-right">
                      {Number(s.avg_accuracy).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    <span className="text-green-600">✓ {s.correct}</span> · <span className="text-red-500">✗ {s.incorrect}</span>
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentAnalytics;
