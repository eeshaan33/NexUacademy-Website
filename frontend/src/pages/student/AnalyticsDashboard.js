import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  LineChart, Line, Legend,
} from 'recharts';
import { Card, CardContent } from '../../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import {
  Target, Trophy, Flame, TrendingUp, Activity, Medal, AlertTriangle,
  Crown, Award, ClipboardList,
} from 'lucide-react';
import api from '../../utils/api';
import { setPageTitle } from '../../utils/pageTitle';

const accuracyColor = (pct) => {
  if (pct >= 80) return 'bg-emerald-500';
  if (pct >= 60) return 'bg-lime-400';
  if (pct >= 40) return 'bg-amber-400';
  if (pct > 0) return 'bg-orange-400';
  return 'bg-slate-200';
};

const Stat = ({ icon: Icon, label, value, tint }) => (
  <Card className="border-0 shadow-sm" data-testid={`stat-${label.toLowerCase().replace(/ /g, '-')}`}>
    <CardContent className="p-5 flex items-start justify-between">
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-3xl font-bold text-slate-900 mt-1">{value}</p>
      </div>
      <div className={`${tint} p-3 rounded-xl`}>
        <Icon className="h-5 w-5 text-white" />
      </div>
    </CardContent>
  </Card>
);

const AnalyticsDashboard = () => {
  const [overview, setOverview] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [activity, setActivity] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { setPageTitle('My Analytics'); }, []);

  useEffect(() => {
    (async () => {
      try {
        const [o, h, a, l] = await Promise.all([
          api.get('/student/analytics/overview'),
          api.get('/student/analytics/heatmap'),
          api.get('/student/analytics/activity'),
          api.get('/student/analytics/leaderboard'),
        ]);
        setOverview(o.data);
        setHeatmap(h.data.heatmap || []);
        setActivity(a.data.activity || []);
        setLeaderboard(l.data.leaderboard || []);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const subjects = useMemo(() => {
    const set = new Set(heatmap.map((h) => h.subject));
    return Array.from(set);
  }, [heatmap]);

  const activityData = useMemo(() => activity.map((d) => ({
    date: d.date?.substring(5),
    solved: d.solved || 0,
    correct: d.correct || 0,
    accuracy: d.solved ? Math.round((d.correct / d.solved) * 100) : 0,
  })), [activity]);

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading your analytics…</div>;
  }

  const hasData = (overview?.total_tests || 0) > 0 || activityData.some((d) => d.solved);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6" data-testid="analytics-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">My Analytics</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track your progress, compare with peers, and find weak areas.
          </p>
        </div>
        {overview?.batch_rank && (
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white px-5 py-3 rounded-xl shadow">
            <div className="text-xs opacity-80">Batch Rank</div>
            <div className="text-2xl font-bold">#{overview.batch_rank}<span className="text-sm font-normal opacity-80"> / {overview.batch_size}</span></div>
          </div>
        )}
      </div>

      {!hasData ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="py-16 text-center space-y-3">
            <Activity className="h-12 w-12 text-slate-300 mx-auto" />
            <p className="text-slate-600 font-medium">No analytics data yet</p>
            <p className="text-sm text-slate-400">
              Take a test to start tracking your progress.
            </p>
            <Link to="/assigned-tests" className="inline-block mt-2 text-indigo-600 font-medium text-sm hover:underline">Go to assigned tests →</Link>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Stat icon={ClipboardList} label="Tests Taken" value={overview?.total_tests || 0} tint="bg-blue-500" />
            <Stat icon={Target} label="Questions Solved" value={overview?.total_questions_attempted || 0} tint="bg-purple-500" />
            <Stat icon={TrendingUp} label="Avg Accuracy" value={`${overview?.avg_accuracy || 0}%`} tint="bg-emerald-500" />
            <Stat icon={Flame} label="Correct / Wrong" value={`${overview?.total_correct || 0} / ${overview?.total_incorrect || 0}`} tint="bg-orange-500" />
          </div>

          <Tabs defaultValue="activity" className="w-full">
            <TabsList className="grid grid-cols-4 w-full max-w-xl">
              <TabsTrigger value="activity" data-testid="tab-activity">Activity</TabsTrigger>
              <TabsTrigger value="heatmap" data-testid="tab-heatmap">Heatmap</TabsTrigger>
              <TabsTrigger value="leaderboard" data-testid="tab-leaderboard">Leaderboard</TabsTrigger>
              <TabsTrigger value="insights" data-testid="tab-insights">Insights</TabsTrigger>
            </TabsList>

            {/* ACTIVITY */}
            <TabsContent value="activity" className="mt-4">
              <Card className="border-0 shadow-sm">
                <CardContent className="p-5 space-y-4">
                  <h2 className="font-semibold text-slate-800">30-Day Activity</h2>
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={activityData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                        <YAxis tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="solved" name="Solved" stroke="#6366f1" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="correct" name="Correct" stroke="#10b981" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <h3 className="font-semibold text-slate-800 pt-2">Daily Volume</h3>
                  <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={activityData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                        <YAxis tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Bar dataKey="solved" fill="#818cf8" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* HEATMAP */}
            <TabsContent value="heatmap" className="mt-4">
              <Card className="border-0 shadow-sm">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="font-semibold text-slate-800">Chapter-wise Accuracy Heatmap</h2>
                    <div className="flex items-center gap-1 text-xs text-slate-500">
                      <span className="inline-block w-3 h-3 bg-orange-400 rounded"></span>Low
                      <span className="inline-block w-3 h-3 bg-amber-400 rounded ml-2"></span>Avg
                      <span className="inline-block w-3 h-3 bg-lime-400 rounded ml-2"></span>Good
                      <span className="inline-block w-3 h-3 bg-emerald-500 rounded ml-2"></span>Strong
                    </div>
                  </div>
                  {heatmap.length === 0 ? (
                    <p className="text-slate-400 text-sm py-10 text-center">No chapter data yet. Attempt more questions to build your heatmap.</p>
                  ) : (
                    <div className="space-y-5">
                      {subjects.map((subj) => (
                        <div key={subj}>
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="text-sm font-semibold text-slate-700">{subj}</h3>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {heatmap.filter((h) => h.subject === subj).map((h) => (
                              <div key={`${h.subject}-${h.chapter}`} className={`rounded-lg p-3 text-white ${accuracyColor(h.accuracy)}`} data-testid={`heat-${h.subject}-${h.chapter}`}>
                                <div className="text-xs font-medium opacity-90 truncate">{h.chapter}</div>
                                <div className="flex justify-between items-end mt-1">
                                  <div className="text-2xl font-bold">{h.accuracy.toFixed(0)}%</div>
                                  <div className="text-xs opacity-80">{h.correct}/{h.attempted}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* LEADERBOARD */}
            <TabsContent value="leaderboard" className="mt-4">
              <Card className="border-0 shadow-sm">
                <CardContent className="p-5 space-y-3">
                  <div className="flex items-center gap-2">
                    <Trophy className="h-5 w-5 text-amber-500" />
                    <h2 className="font-semibold text-slate-800">Batch Leaderboard</h2>
                  </div>
                  {leaderboard.length === 0 ? (
                    <p className="text-slate-400 text-sm py-10 text-center">No leaderboard yet — be the first to attempt a test in your batch!</p>
                  ) : (
                    <div className="divide-y border rounded-xl overflow-hidden">
                      {leaderboard.map((row) => (
                        <div key={row.user_id} className={`flex items-center gap-3 px-4 py-3 ${row.is_me ? 'bg-indigo-50' : 'bg-white'}`} data-testid={`leaderboard-row-${row.rank}`}>
                          <div className="w-8 text-center font-bold text-slate-700">
                            {row.rank === 1 ? <Crown className="h-5 w-5 text-amber-500 mx-auto" /> :
                             row.rank === 2 ? <Medal className="h-5 w-5 text-slate-400 mx-auto" /> :
                             row.rank === 3 ? <Award className="h-5 w-5 text-amber-700 mx-auto" /> :
                             `#${row.rank}`}
                          </div>
                          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-semibold shrink-0">
                            {row.profile_pic ? <img src={row.profile_pic} alt="" className="w-8 h-8 rounded-full object-cover" /> : (row.name || '?').charAt(0)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-slate-800 truncate">{row.name} {row.is_me && <span className="text-xs text-indigo-600">(you)</span>}</div>
                            <div className="text-xs text-slate-400">{row.tests} tests · {row.total_score} points</div>
                          </div>
                          <div className="text-sm font-bold text-emerald-600">{row.avg_accuracy}%</div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* INSIGHTS */}
            <TabsContent value="insights" className="mt-4">
              <div className="grid md:grid-cols-2 gap-4">
                <Card className="border-0 shadow-sm">
                  <CardContent className="p-5 space-y-3">
                    <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                      <Trophy className="h-5 w-5 text-emerald-500" /> Best Performance
                    </h3>
                    {overview?.best_test ? (
                      <Link to={`/test-results/${overview.best_test.attempt_id}`} className="block p-3 rounded-lg border hover:border-emerald-400 transition">
                        <div className="font-medium text-slate-800">{overview.best_test.test_name}</div>
                        <div className="text-sm text-slate-500 mt-1">
                          {overview.best_test.score}/{overview.best_test.max_score} points · <span className="text-emerald-600 font-medium">{overview.best_test.accuracy}%</span>
                        </div>
                      </Link>
                    ) : <p className="text-sm text-slate-400">No tests yet.</p>}
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-sm">
                  <CardContent className="p-5 space-y-3">
                    <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-amber-500" /> Needs Focus
                    </h3>
                    {overview?.worst_test ? (
                      <Link to={`/test-results/${overview.worst_test.attempt_id}`} className="block p-3 rounded-lg border hover:border-amber-400 transition">
                        <div className="font-medium text-slate-800">{overview.worst_test.test_name}</div>
                        <div className="text-sm text-slate-500 mt-1">
                          {overview.worst_test.score}/{overview.worst_test.max_score} points · <span className="text-amber-600 font-medium">{overview.worst_test.accuracy}%</span>
                        </div>
                      </Link>
                    ) : <p className="text-sm text-slate-400">No tests yet.</p>}
                  </CardContent>
                </Card>
              </div>

              {/* Weak chapters */}
              <Card className="border-0 shadow-sm mt-4">
                <CardContent className="p-5 space-y-3">
                  <h3 className="font-semibold text-slate-800">Weak Chapters</h3>
                  {(() => {
                    const weak = heatmap
                      .filter((h) => h.attempted >= 2 && h.accuracy < 60)
                      .sort((a, b) => a.accuracy - b.accuracy)
                      .slice(0, 6);
                    if (!weak.length) return <p className="text-sm text-slate-400">Keep practising — no weak areas detected yet.</p>;
                    return (
                      <div className="space-y-2">
                        {weak.map((w) => (
                          <div key={`${w.subject}-${w.chapter}`} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                            <div className="flex-1">
                              <div className="text-sm font-medium text-slate-800">{w.chapter}</div>
                              <div className="text-xs text-slate-500">{w.subject}</div>
                            </div>
                            <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                              <div className={`h-full ${accuracyColor(w.accuracy)}`} style={{ width: `${w.accuracy}%` }} />
                            </div>
                            <div className="text-sm font-semibold text-slate-700 w-14 text-right">{w.accuracy.toFixed(0)}%</div>
                          </div>
                        ))}
                      </div>
                    );
                  })()}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
