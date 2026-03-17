import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Card, CardContent } from '../../components/ui/card';
import { BookOpen, FileEdit, Users, TrendingUp } from 'lucide-react';
import api from '../../utils/api';

const TeacherDashboard = () => {
  const { user } = useAuth();
  const [classStats, setClassStats] = useState({ total: 0, upcoming: 0, completed: 0 });
  const [testStats, setTestStats] = useState({ total: 0, scheduled: 0, draft: 0 });
  const [studentCount, setStudentCount] = useState(0);

  useEffect(() => {
    const load = async () => {
      try {
        const [cs, ts, ss] = await Promise.all([
          api.get('/teacher/classes/stats'),
          api.get('/teacher/tests/stats'),
          api.get('/teacher/students/'),
        ]);
        setClassStats(cs.data);
        setTestStats(ts.data);
        setStudentCount(ss.data.count || 0);
      } catch (e) {
        console.error(e);
      }
    };
    load();
  }, []);

  const cards = [
    { title: 'Total Classes', value: classStats.total, sub: `${classStats.upcoming} upcoming`, icon: BookOpen, color: 'bg-blue-500', link: '/teacher/classes' },
    { title: 'Total Tests', value: testStats.total, sub: `${testStats.scheduled} active`, icon: FileEdit, color: 'bg-purple-500', link: '/teacher/tests' },
    { title: 'Students', value: studentCount, sub: 'Enrolled', icon: Users, color: 'bg-emerald-500', link: '/teacher/students' },
    { title: 'Drafts', value: testStats.draft, sub: 'Unpublished tests', icon: TrendingUp, color: 'bg-amber-500', link: '/teacher/tests' },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8" data-testid="teacher-dashboard">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Welcome, {user?.name?.split(' ')[0]}</h1>
        <p className="text-slate-500 mt-1">Here's your teaching overview</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <Link key={c.title} to={c.link} data-testid={`stat-${c.title.toLowerCase().replace(/ /g, '-')}`}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer border-0 shadow-sm">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-slate-500">{c.title}</p>
                      <p className="text-3xl font-bold text-slate-900 mt-1">{c.value}</p>
                      <p className="text-xs text-slate-400 mt-1">{c.sub}</p>
                    </div>
                    <div className={`${c.color} p-3 rounded-xl`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Link to="/teacher/classes" data-testid="quick-schedule-class">
          <Card className="border-0 shadow-sm hover:shadow-lg transition-all bg-gradient-to-br from-indigo-500 to-purple-600 text-white cursor-pointer">
            <CardContent className="p-6">
              <BookOpen className="h-8 w-8 mb-3 opacity-80" />
              <h3 className="text-lg font-semibold">Schedule a Class</h3>
              <p className="text-sm opacity-80 mt-1">Create a new live class session</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/teacher/tests" data-testid="quick-create-test">
          <Card className="border-0 shadow-sm hover:shadow-lg transition-all bg-gradient-to-br from-purple-500 to-pink-600 text-white cursor-pointer">
            <CardContent className="p-6">
              <FileEdit className="h-8 w-8 mb-3 opacity-80" />
              <h3 className="text-lg font-semibold">Create a Test</h3>
              <p className="text-sm opacity-80 mt-1">Design and publish a new test</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/teacher/students" data-testid="quick-view-students">
          <Card className="border-0 shadow-sm hover:shadow-lg transition-all bg-gradient-to-br from-emerald-500 to-teal-600 text-white cursor-pointer">
            <CardContent className="p-6">
              <Users className="h-8 w-8 mb-3 opacity-80" />
              <h3 className="text-lg font-semibold">View Students</h3>
              <p className="text-sm opacity-80 mt-1">Track student performance</p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
};

export default TeacherDashboard;
