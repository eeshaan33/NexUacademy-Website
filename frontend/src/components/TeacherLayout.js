import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import NotificationBell from './NotificationBell';
import {
  LayoutDashboard,
  BookOpen,
  FileEdit,
  Users,
  Settings,
  LogOut,
  User,
  Menu,
  X,
} from 'lucide-react';

const TeacherLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/teacher', icon: LayoutDashboard, testId: 'teacher-nav-dashboard' },
    { name: 'Manage Classes', href: '/teacher/classes', icon: BookOpen, testId: 'teacher-nav-classes' },
    { name: 'Create Tests', href: '/teacher/tests', icon: FileEdit, testId: 'teacher-nav-tests' },
    { name: 'View Students', href: '/teacher/students', icon: Users, testId: 'teacher-nav-students' },
  ];

  const getInitials = (name) =>
    name?.split(' ').map((n) => n[0]).join('').toUpperCase() || 'T';

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 rounded-md text-slate-600 hover:bg-slate-100"
                data-testid="teacher-mobile-menu"
              >
                {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
              <Link to="/teacher" className="flex items-center space-x-3 ml-2 md:ml-0">
                <img src="/logo.png" alt="NexUacademy" className="h-10 w-auto object-contain" />
                <span className="hidden sm:block text-sm font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded" data-testid="teacher-badge">
                  Teacher Panel
                </span>
              </Link>
            </div>
            <div className="flex items-center space-x-3">
              <NotificationBell />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full" data-testid="teacher-user-menu">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={user?.profile_pic} alt={user?.name} />
                      <AvatarFallback className="bg-indigo-600 text-white">{getInitials(user?.name)}</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium">{user?.name}</p>
                      <p className="text-xs text-muted-foreground">{user?.email}</p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard" className="cursor-pointer">
                      <User className="mr-2 h-4 w-4" />
                      Student View
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout} data-testid="teacher-logout">
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        <aside
          className={`fixed md:sticky top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64 bg-white border-r border-slate-200 transform transition-transform duration-200 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}
        >
          <nav className="p-4 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  data-testid={item.testId}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-50'}`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {sidebarOpen && (
          <div className="fixed inset-0 bg-black/20 z-30 md:hidden" onClick={() => setSidebarOpen(false)} />
        )}

        <main className="flex-1 min-h-[calc(100vh-4rem)]">{children}</main>
      </div>
    </div>
  );
};

export default TeacherLayout;
