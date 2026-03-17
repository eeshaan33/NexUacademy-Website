import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Link, Navigate } from 'react-router-dom';
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
  Flame
} from 'lucide-react';
import api from '../utils/api';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/analytics/dashboard');
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Redirect teachers to teacher dashboard (after hooks)
  if (user?.role === 'teacher') {
    return <Navigate to="/teacher" replace />;
  }

  const navigationCards = [
    {
      title: 'PYQ Section',
      description: 'Practice Previous Year Questions',
      icon: BookOpen,
      bgColor: 'bg-[#E0DFFB]',
      textColor: 'text-purple-700',
      link: '/pyq',
      testId: 'pyq-card'
    },
    {
      title: 'My Tests',
      description: 'Create Custom Practice Tests',
      icon: FileEdit,
      bgColor: 'bg-[#E8F5E9]',
      textColor: 'text-green-700',
      link: '/my-tests',
      testId: 'my-tests-card'
    },
    {
      title: 'Assigned Tests',
      description: 'View Tests Assigned by Teacher',
      icon: ClipboardList,
      bgColor: 'bg-[#FFF8DC]',
      textColor: 'text-yellow-700',
      link: '/assigned-tests',
      testId: 'assigned-tests-card'
    },
    {
      title: 'My Classes',
      description: 'Attend Live Classes',
      icon: Video,
      bgColor: 'bg-[#FFE0E6]',
      textColor: 'text-pink-700',
      link: '/classes',
      testId: 'classes-card'
    },
    {
      title: 'Analytics',
      description: 'Track Your Performance',
      icon: BarChart3,
      bgColor: 'bg-[#E3F2FD]',
      textColor: 'text-blue-700',
      link: '/analytics',
      testId: 'analytics-card'
    },
    {
      title: 'Bookmarks',
      description: 'Review Saved Questions',
      icon: Bookmark,
      bgColor: 'bg-[#F3E5F5]',
      textColor: 'text-purple-700',
      link: '/bookmarks',
      testId: 'bookmarks-card'
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
