import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "sonner";

// Components
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import TeacherLayout from "./components/TeacherLayout";

// Pages
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import AdmissionForm from "./pages/AdmissionForm";
import AdminPanel from "./pages/AdminPanel";
import LandingPage from "./pages/LandingPage";
import ProfilePage from "./pages/ProfilePage";
import AuthCallback from "./pages/AuthCallback";
import FeeStructure from "./pages/FeeStructure";
import StudentAnalytics from "./pages/student/AnalyticsDashboard";

// Teacher pages
import TeacherDashboard from "./pages/teacher/TeacherDashboard";
import ManageClasses from "./pages/teacher/ManageClasses";
import CreateTest from "./pages/teacher/CreateTest";
import TeacherLiveClasses from "./pages/teacher/LiveClasses";

// Student pages
import StudentClasses from "./pages/student/StudentClasses";
import StudentLiveClasses from "./pages/student/LiveClasses";
import SampleQuestions from "./pages/SampleQuestions";

// Shared components
import PageViewTracker from "./components/PageViewTracker";

function RoleBasedRedirect() {
  const { user, isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/landing" replace />;
  if (user?.role === 'admin') return <Navigate to="/admin" replace />;
  if (user?.role === 'teacher') return <Navigate to="/teacher" replace />;
  return <Navigate to="/dashboard" replace />;
}

function AppRouter() {
  return (
    <>
    <Routes>
      {/* Public Routes */}
      <Route path="/landing" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/admission" element={<AdmissionForm />} />
      <Route path="/admin" element={<AdminPanel />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/sample-questions" element={<SampleQuestions />} />
      <Route path="/fee-structure" element={<ProtectedRoute><FeeStructure /></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><Layout><StudentAnalytics /></Layout></ProtectedRoute>} />

      {/* Teacher Routes */}
      <Route path="/teacher" element={<ProtectedRoute><TeacherLayout><TeacherDashboard /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/classes" element={<ProtectedRoute><TeacherLayout><ManageClasses /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/tests" element={<ProtectedRoute><TeacherLayout><CreateTest /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/live-classes" element={<ProtectedRoute><TeacherLayout><TeacherLiveClasses /></TeacherLayout></ProtectedRoute>} />

      {/* Student Protected Routes */}
      <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
      <Route path="/classes" element={<ProtectedRoute><Layout><StudentClasses /></Layout></ProtectedRoute>} />
      <Route path="/live-classes" element={<ProtectedRoute><Layout><StudentLiveClasses /></Layout></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Layout><ProfilePage /></Layout></ProtectedRoute>} />

      {/* Default redirect */}
      <Route path="/" element={<RoleBasedRedirect />} />
      <Route path="*" element={<RoleBasedRedirect />} />
      </Routes>
      <PageViewTracker />
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;
