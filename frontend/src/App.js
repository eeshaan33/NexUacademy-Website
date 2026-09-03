import React, { lazy, Suspense } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "sonner";

// Small shell components stay eager (needed by every route)
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import TeacherLayout from "./components/TeacherLayout";
import PageViewTracker from "./components/PageViewTracker";
import PageLoader from "./components/PageLoader";
import { ErrorBoundary } from "./ErrorBoundary";

// Every heavy page is code-split so the initial bundle stays tiny.
// Webpack-dev-server compiles each chunk on demand → cold navigation to
// /login only pulls Login.js instead of framer-motion / recharts / katex.
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const AdmissionForm = lazy(() => import("./pages/AdmissionForm"));
const AdminPanel = lazy(() => import("./pages/AdminPanel"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const ProfilePage = lazy(() => import("./pages/ProfilePage"));
const AuthCallback = lazy(() => import("./pages/AuthCallback"));
const FeeStructure = lazy(() => import("./pages/FeeStructure"));
const StudentAnalytics = lazy(() => import("./pages/student/AnalyticsDashboard"));
const SampleQuestions = lazy(() => import("./pages/SampleQuestions"));

const TeacherDashboard = lazy(() => import("./pages/teacher/TeacherDashboard"));
const ManageClasses = lazy(() => import("./pages/teacher/ManageClasses"));
const CreateTest = lazy(() => import("./pages/teacher/CreateTest"));
const TeacherLiveClasses = lazy(() => import("./pages/teacher/LiveClasses"));

const StudentClasses = lazy(() => import("./pages/student/StudentClasses"));
const StudentLiveClasses = lazy(() => import("./pages/student/LiveClasses"));

function RoleBasedRedirect() {
  const { user, isAuthenticated, loading } = useAuth();
  if (loading) return <PageLoader />;
  if (!isAuthenticated) return <Navigate to="/landing" replace />;
  if (user?.role === 'admin') return <Navigate to="/admin" replace />;
  if (user?.role === 'teacher') return <Navigate to="/teacher" replace />;
  return <Navigate to="/dashboard" replace />;
}

function AppRouter() {
  return (
    <>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/landing" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/admission" element={<ErrorBoundary><AdmissionForm /></ErrorBoundary>} />
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
      </Suspense>
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
