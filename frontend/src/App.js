import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
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
import { MyTestsPage, AnalyticsPage, BookmarksPage } from "./pages/PlaceholderPages";

// Teacher pages
import TeacherDashboard from "./pages/teacher/TeacherDashboard";
import ManageClasses from "./pages/teacher/ManageClasses";
import CreateTest from "./pages/teacher/CreateTest";
import StudentAnalytics from "./pages/teacher/StudentAnalytics";

// Student pages
import StudentClasses from "./pages/student/StudentClasses";
import AssignedTests from "./pages/student/AssignedTests";
import TakeTest from "./pages/student/TakeTest";
import TestResults from "./pages/student/TestResults";

function AppRouter() {
  const location = useLocation();

  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/admission" element={<AdmissionForm />} />
      <Route path="/admin" element={<AdminPanel />} />

      {/* Teacher Routes */}
      <Route path="/teacher" element={<ProtectedRoute><TeacherLayout><TeacherDashboard /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/classes" element={<ProtectedRoute><TeacherLayout><ManageClasses /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/tests" element={<ProtectedRoute><TeacherLayout><CreateTest /></TeacherLayout></ProtectedRoute>} />
      <Route path="/teacher/students" element={<ProtectedRoute><TeacherLayout><StudentAnalytics /></TeacherLayout></ProtectedRoute>} />

      {/* Student Protected Routes */}
      <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
      <Route path="/pyq" element={<ProtectedRoute><PYQSection /></ProtectedRoute>} />
      <Route path="/my-tests" element={<ProtectedRoute><Layout><MyTestsPage /></Layout></ProtectedRoute>} />
      <Route path="/assigned-tests" element={<ProtectedRoute><Layout><AssignedTests /></Layout></ProtectedRoute>} />
      <Route path="/classes" element={<ProtectedRoute><Layout><StudentClasses /></Layout></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><Layout><AnalyticsPage /></Layout></ProtectedRoute>} />
      <Route path="/bookmarks" element={<ProtectedRoute><Layout><BookmarksPage /></Layout></ProtectedRoute>} />

      {/* Test taking (no layout - fullscreen) */}
      <Route path="/take-test/:attemptId" element={<ProtectedRoute><TakeTest /></ProtectedRoute>} />
      <Route path="/test-results/:attemptId" element={<ProtectedRoute><Layout><TestResults /></Layout></ProtectedRoute>} />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
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
