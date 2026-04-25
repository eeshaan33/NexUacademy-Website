import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { Users, ArrowLeft, BarChart3, Target, FileEdit, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';

const StudentAnalytics = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState('all');
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  useEffect(() => {
    setPageTitle('Student Analytics');
  }, []);

  useEffect(() => {
    loadStudents();
    loadBatches();
  }, []);

  useEffect(() => {
    loadStudents();
  }, [selectedBatch]);

  const loadStudents = async () => {
    try {
      const params = selectedBatch !== 'all' ? `?batch_id=${selectedBatch}` : '';
      const res = await api.get(`/teacher/students/${params}`);
      setStudents(res.data.students || []);
    } catch { }
    finally { setLoading(false); }
  };

  const loadBatches = async () => {
    try {
      const res = await api.get('/batches/');
      setBatches(res.data.batches || []);
    } catch { }
  };

  const viewStudent = async (student) => {
    setSelectedStudent(student);
    setAnalyticsLoading(true);
    try {
      const res = await api.get(`/teacher/students/${student.user_id}/analytics`);
      setAnalytics(res.data.analytics);
    } catch {
      setAnalytics(null);
    }
    finally { setAnalyticsLoading(false); }
  };

  const getInitials = (name) => name?.split(' ').map((n) => n[0]).join('').toUpperCase() || '?';

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6" data-testid="student-analytics-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Student Management</h1>
          <p className="text-slate-500 text-sm mt-1">View student performance and analytics</p>
        </div>
        <Select value={selectedBatch} onValueChange={setSelectedBatch}>
          <SelectTrigger className="w-52" data-testid="batch-filter">
            <SelectValue placeholder="Filter by batch" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Batches</SelectItem>
            {batches.map((b) => <SelectItem key={b.id} value={b.id}>{b.name} {b.code ? `(${b.code})` : ''}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading students...</div>
      ) : students.length === 0 ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="py-12 text-center">
            <Users className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No students found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {students.map((s) => (
            <Card key={s.user_id} className="border-0 shadow-sm hover:shadow-lg transition-all cursor-pointer" onClick={() => viewStudent(s)} data-testid={`student-card-${s.user_id}`}>
              <CardContent className="p-5">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-lg font-bold shrink-0">
                    {s.profile_pic ? <img src={s.profile_pic} alt="" className="w-12 h-12 rounded-full object-cover" /> : getInitials(s.name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-900 truncate">{s.name}</p>
                    <p className="text-xs text-slate-400 truncate">{s.email}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {s.batch_id && (
                        <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{s.batch_id}</span>
                      )}
                      {s.roll_number && (
                        <span className="text-xs bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full font-mono">{s.roll_number}</span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Student Analytics Modal */}
      <Dialog open={!!selectedStudent} onOpenChange={() => { setSelectedStudent(null); setAnalytics(null); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
                {getInitials(selectedStudent?.name)}
              </div>
              <div>
                <div>{selectedStudent?.name}</div>
                <div className="text-xs text-slate-400 font-normal">{selectedStudent?.email}</div>
              </div>
            </DialogTitle>
          </DialogHeader>

          {analyticsLoading ? (
            <div className="py-8 text-center text-slate-400">Loading analytics...</div>
          ) : analytics ? (
            <div className="space-y-6">
              {/* Stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  { label: 'Tests Taken', value: analytics.total_tests_attempted, icon: FileEdit, color: 'text-blue-600 bg-blue-50' },
                  { label: 'Avg Score', value: `${analytics.average_score}%`, icon: TrendingUp, color: 'text-purple-600 bg-purple-50' },
                  { label: 'This Week', value: analytics.questions_this_week, icon: Target, color: 'text-emerald-600 bg-emerald-50' },
                  { label: 'Accuracy', value: `${analytics.overall_accuracy}%`, icon: BarChart3, color: 'text-amber-600 bg-amber-50' },
                ].map((s) => {
                  const Icon = s.icon;
                  return (
                    <div key={s.label} className={`p-4 rounded-xl ${s.color}`}>
                      <Icon className="h-5 w-5 mb-2" />
                      <p className="text-2xl font-bold">{s.value}</p>
                      <p className="text-xs opacity-70">{s.label}</p>
                    </div>
                  );
                })}
              </div>

              {/* Daily Activity Chart */}
              {analytics.daily_activity && analytics.daily_activity.length > 0 && (
                <div>
                  <h3 className="font-semibold text-slate-700 mb-3">Questions Solved - Last 30 Days</h3>
                  <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.daily_activity.map((d) => ({ date: d.date?.substring(5, 10) || d._id?.substring(5, 10) || '', solved: d.questions_solved || d.questionsSolved || 0 }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                        <YAxis tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Bar dataKey="solved" fill="#6366f1" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Test Attempts */}
              {analytics.test_attempts && analytics.test_attempts.length > 0 && (
                <div>
                  <h3 className="font-semibold text-slate-700 mb-3">Recent Test Attempts</h3>
                  <div className="border rounded-lg divide-y max-h-60 overflow-y-auto">
                    {analytics.test_attempts.map((a, i) => (
                      <div key={i} className="px-4 py-3 flex items-center justify-between text-sm">
                        <div>
                          <p className="font-medium">{a.test_name || a.test_id}</p>
                          <p className="text-xs text-slate-400">{a.submitted_at ? new Date(a.submitted_at).toLocaleDateString() : 'In progress'}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">{a.total_score}/{a.max_score}</p>
                          <p className="text-xs text-slate-400">{a.accuracy}% accuracy</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-400">No analytics data available</div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default StudentAnalytics;
