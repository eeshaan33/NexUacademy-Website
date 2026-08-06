import React, { useEffect, useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Shield, Layers, Megaphone, LogOut } from 'lucide-react';
import { toast } from 'sonner';
import { setPageTitle } from '../utils/pageTitle';
import AdminBatchesPane from '../components/AdminBatchesPane';
import AdminAnnouncementsPane from '../components/AdminAnnouncementsPane';

const TABS = [
  { id: 'batches', label: 'Batches', icon: Layers },
  { id: 'announcements', label: 'Announcements', icon: Megaphone },
];

const AdminPanel = () => {
  const { user, isAuthenticated, logout, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('batches');
  const navigate = useNavigate();

  useEffect(() => { setPageTitle('Admin Panel'); }, []);

  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />;

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="h-7 w-7 text-amber-500" />
          <div>
            <h1 className="text-xl font-semibold">NexUacademy Admin</h1>
            <p className="text-xs text-slate-400">Signed in as {user.email}</p>
          </div>
        </div>
        <Button variant="outline" onClick={() => { logout(); navigate('/login'); }} data-testid="admin-logout-btn"
          className="border-slate-600 text-slate-100 hover:bg-slate-700">
          <LogOut className="h-4 w-4 mr-2" /> Logout
        </Button>
      </header>

      <div className="p-6 flex flex-col md:flex-row gap-6 max-w-7xl mx-auto">
        <nav className="md:w-56 space-y-1">
          {TABS.map(t => {
            const Icon = t.icon;
            const isActive = activeTab === t.id;
            return (
              <button key={t.id}
                onClick={() => setActiveTab(t.id)}
                data-testid={`admin-tab-${t.id}`}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition ${
                  isActive ? 'bg-amber-500 text-slate-900 font-medium' : 'text-slate-300 hover:bg-slate-800'
                }`}>
                <Icon className="h-4 w-4" /> {t.label}
              </button>
            );
          })}
        </nav>
        <div className="flex-1 min-w-0">
          {activeTab === 'batches' && <AdminBatchesPane />}
          {activeTab === 'announcements' && <AdminAnnouncementsPane />}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
