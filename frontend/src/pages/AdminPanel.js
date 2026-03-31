import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Shield, User, Mail, Lock, Plus, Users, MessageSquare, Eye, EyeOff, CheckCircle, Clock } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { setPageTitle } from '../utils/pageTitle';

const AdminPanel = () => {
  const { user, isAuthenticated, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('teachers');
  const [teacherForm, setTeacherForm] = useState({ name: '', email: '', password: '' });
  const [createLoading, setCreateLoading] = useState(false);
  const [teachers, setTeachers] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [contactStats, setContactStats] = useState({ total: 0, new: 0, responded: 0 });
  const [showTeacherPassword, setShowTeacherPassword] = useState(false);

  useEffect(() => { setPageTitle('Admin Panel'); }, []);

  useEffect(() => {
    if (isAuthenticated && user?.role === 'admin') {
      fetchTeachers();
      fetchContacts();
    }
  }, [isAuthenticated, user]);

  if (loading) return <div className="min-h-screen bg-slate-900 flex items-center justify-center"><div className="animate-spin h-8 w-8 border-2 border-amber-500 border-t-transparent rounded-full" /></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />;

  const fetchTeachers = async () => {
    try {
      const { data } = await api.get('/admin/teachers');
      setTeachers(data.teachers || []);
    } catch {}
  };

  const fetchContacts = async () => {
    try {
      const { data } = await api.get('/admin/contacts');
      setContacts(data.contacts || []);
      setContactStats(data.stats || { total: 0, new: 0, responded: 0 });
    } catch {}
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
      await api.post('/admin/create-teacher', teacherForm);
      toast.success(`Teacher account created for ${teacherForm.email}`);
      setTeacherForm({ name: '', email: '', password: '' });
      fetchTeachers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create teacher account');
    } finally {
      setCreateLoading(false);
    }
  };

  const markResponded = async (contactId) => {
    try {
      await api.put(`/admin/contacts/${contactId}/status`);
      toast.success('Marked as responded');
      fetchContacts();
    } catch {}
  };

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500/10 rounded-xl flex items-center justify-center">
              <Shield className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
              <p className="text-sm text-slate-400">NexUacademy Administration</p>
            </div>
          </div>
          <div className="flex gap-2">
            {[
              { id: 'teachers', label: 'Teachers', icon: Users },
              { id: 'contacts', label: 'Inquiries', icon: MessageSquare, badge: contactStats.new }
            ].map(tab => (
              <Button key={tab.id} variant={activeTab === tab.id ? 'default' : 'outline'}
                onClick={() => setActiveTab(tab.id)}
                className={activeTab === tab.id ? 'bg-amber-600 hover:bg-amber-700 text-white' : 'border-slate-600 text-slate-300 hover:bg-slate-800'}
                data-testid={`tab-${tab.id}`}>
                <tab.icon className="h-4 w-4 mr-2" />{tab.label}
                {tab.badge > 0 && <Badge className="ml-2 bg-red-500 text-white text-xs">{tab.badge}</Badge>}
              </Button>
            ))}
          </div>
        </div>

        {activeTab === 'teachers' && (
          <>
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2"><Plus className="h-5 w-5 text-amber-500" /> Create Teacher Account</CardTitle>
                <CardDescription className="text-slate-400">Teachers can log in from the main login page after creation.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateTeacher} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300">Name</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                        <Input value={teacherForm.name} onChange={(e) => setTeacherForm({ ...teacherForm, name: e.target.value })} required
                          className="pl-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500" placeholder="Dr. John Doe" data-testid="teacher-name-input" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                        <Input type="email" value={teacherForm.email} onChange={(e) => setTeacherForm({ ...teacherForm, email: e.target.value })} required
                          className="pl-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500" placeholder="teacher@nexuacademy.com" data-testid="teacher-email-input" />
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input type={showTeacherPassword ? 'text' : 'password'} value={teacherForm.password}
                        onChange={(e) => setTeacherForm({ ...teacherForm, password: e.target.value })} required minLength={6}
                        className="pl-10 pr-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500" placeholder="Min 6 characters" data-testid="teacher-password-input" />
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

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2"><Users className="h-5 w-5 text-amber-500" /> Teachers ({teachers.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {teachers.length === 0 ? (
                  <p className="text-slate-500 text-center py-8">No teacher accounts yet.</p>
                ) : (
                  <div className="space-y-3">
                    {teachers.map((t) => (
                      <div key={t.user_id} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-indigo-500/20 rounded-full flex items-center justify-center">
                            <span className="text-indigo-400 font-semibold text-sm">{t.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'T'}</span>
                          </div>
                          <div>
                            <p className="text-white font-medium">{t.name}</p>
                            <p className="text-slate-400 text-sm">{t.email}</p>
                          </div>
                        </div>
                        <Badge className="bg-indigo-500/20 text-indigo-400 border-indigo-500/30">Teacher</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}

        {activeTab === 'contacts' && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white flex items-center gap-2"><MessageSquare className="h-5 w-5 text-amber-500" /> Contact Inquiries</CardTitle>
                <div className="flex gap-2">
                  <Badge className="bg-blue-500/20 text-blue-400">Total: {contactStats.total}</Badge>
                  <Badge className="bg-green-500/20 text-green-400">New: {contactStats.new}</Badge>
                  <Badge className="bg-slate-500/20 text-slate-400">Responded: {contactStats.responded}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {contacts.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No contact inquiries yet.</p>
              ) : (
                <div className="space-y-3">
                  {contacts.map((c) => (
                    <div key={c.contact_id} className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-white font-medium">{c.name}</p>
                            <Badge className={c.status === 'new' ? 'bg-amber-500/20 text-amber-400' : 'bg-green-500/20 text-green-400'}>
                              {c.status === 'new' ? <Clock className="h-3 w-3 mr-1" /> : <CheckCircle className="h-3 w-3 mr-1" />}
                              {c.status}
                            </Badge>
                          </div>
                          <p className="text-slate-400 text-sm">{c.email} | {c.phone}</p>
                          <p className="text-slate-400 text-sm">Course: {c.course}</p>
                          {c.message && <p className="text-slate-300 text-sm mt-2 bg-slate-800 p-2 rounded">{c.message}</p>}
                          <p className="text-slate-500 text-xs mt-1">{new Date(c.created_at).toLocaleString()}</p>
                        </div>
                        {c.status === 'new' && (
                          <Button size="sm" onClick={() => markResponded(c.contact_id)} className="bg-green-600 hover:bg-green-700 text-white ml-4" data-testid={`respond-${c.contact_id}`}>
                            <CheckCircle className="h-3 w-3 mr-1" /> Mark Responded
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;
