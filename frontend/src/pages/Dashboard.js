import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Link, Navigate } from 'react-router-dom';
import { setPageTitle } from '../utils/pageTitle';
import { 
  BookOpen, 
  FileEdit, 
  ClipboardList, 
  Video, 
  BarChart3, 
  Bookmark,
  Target,
  Trophy,
  TrendingUp,
  Flame,
  Play,
  ExternalLink
} from 'lucide-react';
import api from '../utils/api';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resumeTests, setResumeTests] = useState([]);
  const [liveClasses, setLiveClasses] = useState([]);

  useEffect(() => {
    setPageTitle('Student Dashboard');
  }, []);

  useEffect(() => {
    const fetchStats = async () => {
      // Analytics endpoint is being ported to Supabase — stub with empty values
      setStats(null);
      setLoading(false);
    };
    fetchStats();
  }, []);

  // Fetch in-progress tests + upcoming/live classes for resume widget
  useEffect(() => {
    if (user?.role !== 'student') return;
    (async () => {
      try {
        const t = await api.get('/student/tests/assigned');
        setResumeTests((t.data.tests || []).filter(x => x.attempt_status === 'in_progress'));
      } catch {}
      try {
        const c = await api.get('/student/classes/my-classes');
        const now = Date.now();
        const upcoming = (c.data.classes || []).filter(cl => {
          const t = new Date(cl.scheduled_date_time).getTime();
          return t + (cl.duration || 60) * 60 * 1000 > now; // not yet ended
        }).slice(0, 3);
        setLiveClasses(upcoming);
      } catch {}
    })();
  }, [user]);

  // Redirect teachers to teacher dashboard (after hooks)
  if (user?.role === 'teacher') {
    return <Navigate to="/teacher" replace />;
  }

  const navigationCards = [
    {
      title: 'My Classes',
      description: 'Scheduled classes for your batch',
      icon: Video,
      bgColor: 'bg-[#FFE0E6]',
      textColor: 'text-pink-700',
      link: '/classes',
      testId: 'classes-card'
    },
    {
      title: 'Live Classes',
      description: 'Join Zoom classes when they go live',
      icon: Video,
      bgColor: 'bg-[#E3F2FD]',
      textColor: 'text-blue-700',
      link: '/live-classes',
      testId: 'live-classes-card'
    },
    {
      title: 'Profile',
      description: 'Roll number, batch info & personal details',
      icon: Bookmark,
      bgColor: 'bg-[#F3E5F5]',
      textColor: 'text-purple-700',
      link: '/profile',
      testId: 'profile-card'
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* Welcome Section */}
        <div className="space-y-2">
          <h1 className="text-4xl font-heading font-bold text-foreground">
            Welcome back, {user?.name?.split(' ')[0]}!
          </h1>
          <p className="text-muted-foreground text-lg">
            You're making great progress in your JEE journey.
          </p>
        </div>

        {/* Resume widget — surfaces in-progress tests & live classes after re-login */}
        {(resumeTests.length > 0 || liveClasses.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" data-testid="resume-widget">
            {resumeTests.length > 0 && (
              <Card className="border-0 shadow-card bg-amber-50 border-l-4 border-l-amber-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2 text-amber-900">
                    <Play className="h-4 w-4" /> Resume Your Test
                  </CardTitle>
                  <CardDescription className="text-amber-700">
                    You have {resumeTests.length} test{resumeTests.length > 1 ? 's' : ''} in progress. Pick up where you left off — your answers are auto-saved.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 pt-0">
                  {resumeTests.slice(0, 3).map(t => (
                    <Link key={t.test_id} to="/assigned-tests" className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-sm transition" data-testid={`resume-test-${t.test_id}`}>
                      <div>
                        <p className="font-semibold text-slate-900">{t.test_name}</p>
                        <p className="text-xs text-slate-500">{t.subject} · {t.total_questions} Q · {t.duration} min</p>
                      </div>
                      <Button size="sm" className="bg-amber-500 hover:bg-amber-600">
                        Continue <Play className="h-3 w-3 ml-1" />
                      </Button>
                    </Link>
                  ))}
                </CardContent>
              </Card>
            )}
            {liveClasses.length > 0 && (
              <Card className="border-0 shadow-card bg-indigo-50 border-l-4 border-l-indigo-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2 text-indigo-900">
                    <Video className="h-4 w-4" /> Upcoming Classes
                  </CardTitle>
                  <CardDescription className="text-indigo-700">
                    Classes scheduled for your batch. Click to join when live.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 pt-0">
                  {liveClasses.map(c => (
                    <Link key={c.class_id} to="/classes" className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-sm transition" data-testid={`upcoming-class-${c.class_id}`}>
                      <div>
                        <p className="font-semibold text-slate-900">{c.title}</p>
                        <p className="text-xs text-slate-500">{c.subject} · {new Date(c.scheduled_date_time).toLocaleString()}</p>
                      </div>
                      <Button size="sm" variant="outline">
                        View <ExternalLink className="h-3 w-3 ml-1" />
                      </Button>
                    </Link>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="shadow-card hover:shadow-hover transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Questions Solved</p>
                  <p className="text-3xl font-bold">
                    {loading ? '-' : stats?.total_questions_solved || 0}
                  </p>
                </div>
                <div className="bg-blue-100 p-3 rounded-lg">
                  <Target className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-card hover:shadow-hover transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Tests Taken</p>
                  <p className="text-3xl font-bold">
                    {loading ? '-' : stats?.tests_taken || 0}
                  </p>
                </div>
                <div className="bg-green-100 p-3 rounded-lg">
                  <ClipboardList className="h-5 w-5 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-card hover:shadow-hover transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Avg. Accuracy</p>
                  <p className="text-3xl font-bold">
                    {loading ? '-' : `${stats?.average_accuracy?.toFixed(1) || 0}%`}
                  </p>
                </div>
                <div className="bg-purple-100 p-3 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-card hover:shadow-hover transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Current Streak</p>
                  <p className="text-3xl font-bold">
                    {loading ? '-' : stats?.current_streak || 0}
                  </p>
                </div>
                <div className="bg-orange-100 p-3 rounded-lg">
                  <Flame className="h-5 w-5 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Navigation */}
        <div className="space-y-4">
          <h2 className="text-2xl font-heading font-semibold">Quick Navigation</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {navigationCards.map((card) => {
              const Icon = card.icon;
              return (
                <Link key={card.title} to={card.link} data-testid={card.testId}>
                  <Card className={`${card.bgColor} border-none shadow-card hover:shadow-hover hover:-translate-y-1 transition-all duration-300 cursor-pointer`}>
                    <CardContent className="p-6">
                      <div className="space-y-3">
                        <div className="flex items-center justify-center w-12 h-12 bg-white/80 rounded-xl">
                          <Icon className={`h-6 w-6 ${card.textColor}`} />
                        </div>
                        <div className="space-y-1">
                          <h3 className={`text-lg font-semibold ${card.textColor}`}>
                            {card.title}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {card.description}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Coming Soon Section */}
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="font-heading">Coming Soon</CardTitle>
            <CardDescription>
              We're working on exciting features to enhance your preparation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-muted rounded-lg">
                <Trophy className="h-8 w-8 text-primary mb-2" />
                <h4 className="font-semibold mb-1">Leaderboards</h4>
                <p className="text-sm text-muted-foreground">
                  Compete with peers and track your ranking
                </p>
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <Target className="h-8 w-8 text-primary mb-2" />
                <h4 className="font-semibold mb-1">Study Plans</h4>
                <p className="text-sm text-muted-foreground">
                  AI-powered personalized study recommendations
                </p>
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <BookOpen className="h-8 w-8 text-primary mb-2" />
                <h4 className="font-semibold mb-1">Video Lectures</h4>
                <p className="text-sm text-muted-foreground">
                  Comprehensive video content for all topics
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
