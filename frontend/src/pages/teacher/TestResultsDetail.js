import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Input } from '../../components/ui/input';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from 'recharts';
import { ArrowLeft, Download, Users, Trophy, TrendingUp, Search, FileEdit } from 'lucide-react';
import api, { API_BASE_URL } from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';

const TestResultsDetail = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');

  useEffect(() => {
    setPageTitle('Test Results');
    (async () => {
      try {
        const res = await api.get(`/teacher/tests/${testId}/results`);
        setData(res.data);
      } catch (e) {
        setData(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [testId]);

  const filteredAttempts = useMemo(() => {
    if (!data?.attempts) return [];
    const needle = q.toLowerCase();
    return data.attempts.filter((a) =>
      (a.student_name || '').toLowerCase().includes(needle) ||
      (a.email || '').toLowerCase().includes(needle) ||
      (a.batch_id || '').toLowerCase().includes(needle)
    );
  }, [data, q]);

  if (loading) return <div className="p-8 text-center text-slate-400">Loading results…</div>;
  if (!data?.test) return (
    <div className="p-8 text-center text-slate-500 space-y-3">
      <p>Test not found or you don't have access.</p>
      <Button variant="outline" onClick={() => navigate('/teacher/tests')}>← Back to tests</Button>
    </div>
  );

  const { test, stats, attempts, question_stats } = data;

  const downloadCsv = () => {
    // Send browser to the CSV endpoint (will carry cookies for auth)
    window.location.href = `${API_BASE_URL}/teacher/tests/${testId}/results.csv`;
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-5" data-testid="test-results-detail">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <Button variant="ghost" size="sm" onClick={() => navigate('/teacher/tests')} className="mb-2">
            <ArrowLeft className="h-4 w-4 mr-1" /> Back to tests
          </Button>
          <h1 className="text-2xl font-bold text-slate-900">{test.test_name}</h1>
          <p className="text-sm text-slate-500 mt-1">
            {test.exam_type} · {test.subject} · {test.total_questions} questions · {test.duration} min
          </p>
        </div>
        <Button onClick={downloadCsv} className="bg-indigo-600 hover:bg-indigo-700" data-testid="download-csv">
          <Download className="h-4 w-4 mr-2" /> Export CSV
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Attempts', value: attempts.length, icon: Users, tint: 'bg-blue-500' },
          { label: 'Avg Score', value: stats?.avg_score || 0, icon: TrendingUp, tint: 'bg-purple-500' },
          { label: 'Avg Accuracy', value: `${stats?.avg_accuracy || 0}%`, icon: TrendingUp, tint: 'bg-emerald-500' },
          { label: 'Top Score', value: `${stats?.highest || 0} / ${test.total_marks}`, icon: Trophy, tint: 'bg-amber-500' },
        ].map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.label} className="border-0 shadow-sm">
              <CardContent className="p-5 flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-500">{s.label}</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{s.value}</p>
                </div>
                <div className={`${s.tint} p-2 rounded-lg`}>
                  <Icon className="h-4 w-4 text-white" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Tabs defaultValue="students" className="w-full">
        <TabsList>
          <TabsTrigger value="students" data-testid="tab-students">Students ({attempts.length})</TabsTrigger>
          <TabsTrigger value="questions" data-testid="tab-questions">Question Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="students" className="mt-3">
          <Card className="border-0 shadow-sm">
            <CardContent className="p-4 space-y-3">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <Input className="pl-9" placeholder="Search name, email or batch…" value={q} onChange={(e) => setQ(e.target.value)} data-testid="student-search" />
              </div>
              {filteredAttempts.length === 0 ? (
                <div className="py-12 text-center text-slate-400">No attempts match your filter.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-left text-slate-500 border-b">
                      <tr>
                        <th className="py-2 w-12">#</th>
                        <th className="py-2">Student</th>
                        <th className="py-2">Batch</th>
                        <th className="py-2 text-center">Score</th>
                        <th className="py-2 text-center">Accuracy</th>
                        <th className="py-2 text-center">C / W / S</th>
                        <th className="py-2 text-center">Time</th>
                        <th className="py-2 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {filteredAttempts.map((a) => (
                        <tr key={a.attempt_id} className="hover:bg-slate-50" data-testid={`attempt-row-${a.rank}`}>
                          <td className="py-3 font-semibold text-slate-700">#{a.rank}</td>
                          <td className="py-3">
                            <div className="font-medium text-slate-900">{a.student_name}</div>
                            <div className="text-xs text-slate-400">{a.email}</div>
                          </td>
                          <td className="py-3 text-slate-500 text-xs">{a.batch_id || '—'}</td>
                          <td className="py-3 text-center font-semibold">{a.total_score}<span className="text-slate-400 text-xs"> / {a.max_score}</span></td>
                          <td className="py-3 text-center">
                            <span className={`font-semibold ${a.accuracy >= 60 ? 'text-emerald-600' : a.accuracy >= 40 ? 'text-amber-600' : 'text-red-500'}`}>{a.accuracy}%</span>
                          </td>
                          <td className="py-3 text-center text-xs">
                            <span className="text-emerald-600">{a.correct_answers}</span> / <span className="text-red-500">{a.incorrect_answers}</span> / <span className="text-slate-400">{a.unattempted}</span>
                          </td>
                          <td className="py-3 text-center text-xs text-slate-500">{Math.round((a.time_spent || 0) / 60)} min</td>
                          <td className="py-3 text-center">
                            <span className={`text-xs px-2 py-0.5 rounded ${a.status === 'submitted' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>{a.status}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="questions" className="mt-3">
          <Card className="border-0 shadow-sm">
            <CardContent className="p-5 space-y-4">
              <h3 className="font-semibold text-slate-800">Per-question Performance</h3>
              {question_stats.length === 0 ? (
                <div className="py-8 text-center text-slate-400">No question data yet.</div>
              ) : (
                <>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={question_stats.map((q) => ({ q: `Q${q.question_number}`, correct: q.correct, incorrect: q.incorrect, skipped: q.skipped }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="q" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Bar dataKey="correct" stackId="a" fill="#10b981" />
                        <Bar dataKey="incorrect" stackId="a" fill="#ef4444" />
                        <Bar dataKey="skipped" stackId="a" fill="#cbd5e1" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="divide-y border rounded-lg">
                    {question_stats.map((q) => {
                      const total = q.correct + q.incorrect + q.skipped || 1;
                      const pct = Math.round((q.correct / total) * 100);
                      return (
                        <div key={q.question_number} className="px-4 py-3 flex items-center gap-3 text-sm">
                          <div className="w-10 font-semibold text-slate-700">Q{q.question_number}</div>
                          <div className="flex-1 min-w-0">
                            <div className="truncate text-slate-700">{q.question_text || '—'}</div>
                            <div className="text-xs text-slate-400">{q.subject} · {q.chapter}</div>
                          </div>
                          <div className="w-40 h-2 bg-slate-200 rounded overflow-hidden">
                            <div className="h-full bg-emerald-500" style={{ width: `${pct}%` }} />
                          </div>
                          <div className="w-28 text-xs text-right text-slate-500">
                            <span className="text-emerald-600">{q.correct}</span> / <span className="text-red-500">{q.incorrect}</span> / <span className="text-slate-400">{q.skipped}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TestResultsDetail;
