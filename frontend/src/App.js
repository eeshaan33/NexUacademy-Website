import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "sonner";

// Components
import AuthCallback from "./components/AuthCallback";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import TeacherLayout from "./components/TeacherLayout";

// Pages
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import PYQSection from "./pages/PYQSection";
import AdmissionForm from "./pages/AdmissionForm";
import AdminPanel from "./pages/AdminPanel";
import LandingPage from "./pages/LandingPage";
import BookmarksPage from "./pages/BookmarksPage";
import { MyTestsPage } from "./pages/PlaceholderPages";

// Teacher pages
import TeacherDashboard from "./pages/teacher/TeacherDashboard";
import ManageClasses from "./pages/teacher/ManageClasses";
import CreateTest from "./pages/teacher/CreateTest";
import StudentAnalytics from "./pages/teacher/StudentAnalytics";
import TestResultsDetail from "./pages/teacher/TestResultsDetail";

// Student pages
import StudentClasses from "./pages/student/StudentClasses";
import AssignedTests from "./pages/student/AssignedTests";
import TakeTest from "./pages/student/TakeTest";
import TestResults from "./pages/student/TestResults";
import JEEMainInterface from "./pages/student/JEEMainInterface";
import JEEAdvancedInterface from "./pages/student/JEEAdvancedInterface";
import AnalyticsDashboard from "./pages/student/AnalyticsDashboard";

function RoleBasedRedirect() {
  const { user, isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/landing" replace />;
  if (user?.role === 'admin') return <Navigate to="/admin" replace />;
  if (user?.role === 'teacher') return <Navigate to="/teacher" replace />;
  return <Navigate to="/dashboard" replace />;
}

function SmartTestRouter() {
  const location = useLocation();
  const test = location.state?.test;
  const pattern = test?.test_pattern;

  if (pattern === 'JEE_Advanced_Pattern') return <JEEAdvancedInterface />;
  if (pattern === 'JEE_Main_Pattern') return <JEEMainInterface />;
  return <TakeTest />;
}

function AppRouter() {
  const location = useLocation();

  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/landing" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/admission" element={<AdmissionForm />} />
      <Route path="/admin" element={<AdminPanel />} />

      {/* Teacher Routes */}
      <Route path="/teacher" element={<ProtectedRoute><TeacherLayout><TeacherDashboard /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/classes" element={<ProtectedRoute><TeacherLayout><ManageClasses /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/tests" element={<ProtectedRoute><TeacherLayout><CreateTest /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/students" element={<ProtectedRoute><TeacherLayout><StudentAnalytics /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/tests/:testId/results" element={<ProtectedRoute><TeacherLayout><TestResultsDetail /></TeacherLayout></ProtectedRoute>} />

      {/* Student Protected Routes */}
      <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
      <Route path="/pyq" element={<ProtectedRoute><PYQSection /></ProtectedRoute>} />
      <Route path="/my-tests" element={<ProtectedRoute><Layout><MyTestsPage /></Layout></ProtectedRoute>} />
      <Route path="/assigned-tests" element={<ProtectedRoute><Layout><AssignedTests /></Layout></ProtectedRoute>} />
      <Route path="/classes" element={<ProtectedRoute><Layout><StudentClasses /></Layout></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><Layout><AnalyticsDashboard /></Layout></ProtectedRoute>} />
      <Route path="/bookmarks" element={<ProtectedRoute><Layout><BookmarksPage /></Layout></ProtectedRoute>} />

      {/* Test taking (no layout - fullscreen) */}
      <Route path="/take-test/:attemptId" element={<ProtectedRoute><SmartTestRouter /></ProtectedRoute>} />
      <Route path="/test-results/:attemptId" element={<ProtectedRoute><Layout><TestResults /></Layout></ProtectedRoute>} />

      {/* Default redirect */}
      <Route path="/" element={<RoleBasedRedirect />} />
      <Route path="*" element={<RoleBasedRedirect />} />
    </Routes>
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
