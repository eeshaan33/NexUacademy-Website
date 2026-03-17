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
  BookOpen, 
  LayoutDashboard,
  FileEdit, 
  ClipboardList, 
  Video, 
  BarChart3, 
  Bookmark,
  LogOut,
  User,
  Menu,
  X
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, testId: 'nav-dashboard' },
    { name: 'PYQ Section', href: '/pyq', icon: BookOpen, testId: 'nav-pyq' },
    { name: 'My Tests', href: '/my-tests', icon: FileEdit, testId: 'nav-my-tests' },
    { name: 'Assigned Tests', href: '/assigned-tests', icon: ClipboardList, testId: 'nav-assigned-tests' },
    { name: 'My Classes', href: '/classes', icon: Video, testId: 'nav-classes' },
    { name: 'Analytics', href: '/analytics', icon: BarChart3, testId: 'nav-analytics' },
    { name: 'Bookmarks', href: '/bookmarks', icon: Bookmark, testId: 'nav-bookmarks' },
  ];

  const handleLogout = async () => {
    await logout();
  };

  const getInitials = (name) => {
    return name
      ?.split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase() || 'U';
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navbar */}
      <nav className="sticky top-0 z-50 bg-white border-b border-border shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100"
                data-testid="mobile-menu-button"
              >
                {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
              
              {/* Logo */}
              <Link to="/dashboard" className="flex items-center space-x-3 ml-2 md:ml-0">
                <img src="/logo.png" alt="NexUacademy" className="h-12 w-auto object-contain" />
              </Link>
            </div>

            {/* User menu */}
            <div className="flex items-center space-x-4">
              <NotificationBell />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full" data-testid="user-menu">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={user?.profile_pic} alt={user?.name} />
                      <AvatarFallback className="bg-primary text-white">
                        {getInitials(user?.name)}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{user?.name}</p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user?.email}
                      </p>
                      <p className="text-xs leading-none text-muted-foreground capitalize mt-1">
                        {user?.role}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <User className="mr-2 h-4 w-4" />
                    <span>Profile</span>
                  </DropdownMenuItem>
                  {user?.role === 'teacher' && (
                    <>
                      <DropdownMenuItem asChild>
                        <Link to="/teacher" className="cursor-pointer">
                          <LayoutDashboard className="mr-2 h-4 w-4" />
                          <span>Teacher Dashboard</span>
                        </Link>
                      </DropdownMenuItem>
                    </>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} data-testid="logout-button">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`
            fixed md:sticky top-16 left-0 z-40 h-[calc(100vh-4rem)]
            w-64 bg-[#E9ECEF]/50 border-r border-border
            transform transition-transform duration-200 ease-in-out
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            md:translate-x-0
          `}
        >
          <nav className="p-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  data-testid={item.testId}
                  className={`
                    flex items-center space-x-3 px-4 py-3 rounded-lg
                    transition-all duration-200
                    ${isActive 
                      ? 'bg-primary text-white shadow-sm' 
                      : 'text-gray-600 hover:bg-white hover:shadow-sm'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/20 z-30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 min-h-[calc(100vh-4rem)]">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
