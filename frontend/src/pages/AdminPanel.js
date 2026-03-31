import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Lock, User, Mail, Plus, LogOut, Shield, Eye, EyeOff, Users } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { setPageTitle } from '../utils/pageTitle';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AdminPanel = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [adminToken, setAdminToken] = useState('');
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [loginLoading, setLoginLoading] = useState(false);
  const [teacherForm, setTeacherForm] = useState({ name: '', email: '', password: '' });
  const [createLoading, setCreateLoading] = useState(false);
  const [teachers, setTeachers] = useState([]);
  const [showPassword, setShowPassword] = useState(false);
  const [showTeacherPassword, setShowTeacherPassword] = useState(false);

  useEffect(() => {
    setPageTitle('Admin Panel');
  }, []);

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setLoginLoading(true);
    try {
      const { data } = await axios.post(`${API}/admin/login`, loginData, { withCredentials: true });
      setAdminToken(data.token);
      setIsLoggedIn(true);
      toast.success('Admin login successful');
      fetchTeachers(data.token);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid admin credentials');
    } finally {
      setLoginLoading(false);
    }
  };

  const fetchTeachers = async (token) => {
    try {
      const { data } = await axios.get(`${API}/admin/teachers`, {
        withCredentials: true,
        headers: { Authorization: `Bearer ${token || adminToken}` }
      });
      setTeachers(data.teachers || []);
    } catch (error) {
      console.error('Failed to fetch teachers:', error);
    }
  };

  const handleCreateTeacher = async (e) => {
    e.preventDefault();
    if (!teacherForm.name.trim() || !teacherForm.email.trim() || !teacherForm.password.trim()) {
      toast.error('All fields are required');
      return;
    }
    if (teacherForm.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setCreateLoading(true);
    try {
      await axios.post(`${API}/admin/create-teacher`, teacherForm, {
        withCredentials: true,
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      toast.success(`Teacher account created for ${teacherForm.email}`);
      setTeacherForm({ name: '', email: '', password: '' });
      fetchTeachers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create teacher account');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/admin/logout`, {}, {
        withCredentials: true,
        headers: { Authorization: `Bearer ${adminToken}` }
      });
    } catch {}
    setIsLoggedIn(false);
    setAdminToken('');
    setTeachers([]);
    toast.success('Logged out');
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md bg-slate-800 border-slate-700">
          <CardHeader className="text-center space-y-3">
            <div className="mx-auto w-16 h-16 bg-amber-500/10 rounded-2xl flex items-center justify-center">
              <Shield className="h-8 w-8 text-amber-500" />
            </div>
            <CardTitle className="text-2xl text-white">Admin Access</CardTitle>
            <CardDescription className="text-slate-400">NexUacademy Administration Panel</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAdminLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="admin-username" className="text-slate-300">Username</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <Input
                    id="admin-username"
                    value={loginData.username}
                    onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
                    required
                    className="pl-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                    placeholder="Admin username"
                    data-testid="admin-username-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="admin-password" className="text-slate-300">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <Input
                    id="admin-password"
                    type={showPassword ? 'text' : 'password'}
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                    required
                    className="pl-10 pr-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                    placeholder="Admin password"
                    data-testid="admin-password-input"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-3 text-slate-500 hover:text-slate-300">
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <Button type="submit" className="w-full bg-amber-600 hover:bg-amber-700 text-white" disabled={loginLoading} data-testid="admin-login-button">
                {loginLoading ? 'Authenticating...' : 'Access Admin Panel'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500/10 rounded-xl flex items-center justify-center">
              <Shield className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
              <p className="text-sm text-slate-400">NexUacademy Teacher Management</p>
            </div>
          </div>
          <Button variant="outline" onClick={handleLogout} className="border-slate-600 text-slate-300 hover:bg-slate-800" data-testid="admin-logout-button">
            <LogOut className="h-4 w-4 mr-2" /> Logout
          </Button>
        </div>

        {/* Create Teacher Form */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Plus className="h-5 w-5 text-amber-500" /> Create Teacher Account
            </CardTitle>
            <CardDescription className="text-slate-400">
              Add a new teacher to the NexUacademy platform. They can log in using the main login page.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateTeacher} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">Teacher Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                    <Input
                      value={teacherForm.name}
                      onChange={(e) => setTeacherForm({ ...teacherForm, name: e.target.value })}
                      required
                      className="pl-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                      placeholder="Dr. John Doe"
                      data-testid="teacher-name-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                    <Input
                      type="email"
                      value={teacherForm.email}
                      onChange={(e) => setTeacherForm({ ...teacherForm, email: e.target.value })}
                      required
                      className="pl-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                      placeholder="teacher@nexuacademy.com"
                      data-testid="teacher-email-input"
                    />
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-slate-300">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <Input
                    type={showTeacherPassword ? 'text' : 'password'}
                    value={teacherForm.password}
                    onChange={(e) => setTeacherForm({ ...teacherForm, password: e.target.value })}
                    required
                    minLength={6}
                    className="pl-10 pr-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                    placeholder="Minimum 6 characters"
                    data-testid="teacher-password-input"
                  />
                  <button type="button" onClick={() => setShowTeacherPassword(!showTeacherPassword)} className="absolute right-3 top-3 text-slate-500 hover:text-slate-300">
                    {showTeacherPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <Button type="submit" className="bg-amber-600 hover:bg-amber-700 text-white" disabled={createLoading} data-testid="create-teacher-button">
                {createLoading ? 'Creating...' : 'Create Teacher Account'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Teachers List */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Users className="h-5 w-5 text-amber-500" /> Existing Teachers ({teachers.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {teachers.length === 0 ? (
              <p className="text-slate-500 text-center py-8">No teacher accounts yet. Create one above.</p>
            ) : (
              <div className="space-y-3">
                {teachers.map((teacher) => (
                  <div key={teacher.user_id} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-indigo-500/20 rounded-full flex items-center justify-center">
                        <span className="text-indigo-400 font-semibold text-sm">
                          {teacher.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'T'}
                        </span>
                      </div>
                      <div>
                        <p className="text-white font-medium">{teacher.name}</p>
                        <p className="text-slate-400 text-sm">{teacher.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-indigo-500/20 text-indigo-400 border-indigo-500/30">Teacher</Badge>
                      {teacher.last_login && (
                        <span className="text-xs text-slate-500">
                          Last login: {new Date(teacher.last_login).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminPanel;
