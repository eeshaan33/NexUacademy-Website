import React, { lazy, Suspense } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "sonner";

// Small shell components stay eager (needed by every route)
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import TeacherLayout from "./components/TeacherLayout";
import PageViewTracker from "./components/PageViewTracker";
import PageLoader from "./components/PageLoader";

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
const EmergentAuthCallback = lazy(() => import("./pages/EmergentAuthCallback"));
const FeeStructure = lazy(() => import("./pages/FeeStructure"));
const FirstTimeSetup = lazy(() => import("./pages/FirstTimeSetup"));
const UpgradePage = lazy(() => import("./pages/UpgradePage"));
const StudentAnalytics = lazy(() => import("./pages/student/AnalyticsDashboard"));
const SampleQuestions = lazy(() => import("./pages/SampleQuestions"));

const TeacherDashboard = lazy(() => import("./pages/teacher/TeacherDashboard"));
const ManageClasses = lazy(() => import("./pages/teacher/ManageClasses"));
const CreateTest = lazy(() => import("./pages/teacher/CreateTest"));
const TeacherLiveClasses = lazy(() => import("./pages/teacher/LiveClasses"));
const BrowseQuestionBank = lazy(() => import("./pages/teacher/QuestionBank/BrowseQuestionBank"));
const AddQuestion = lazy(() => import("./pages/teacher/QuestionBank/AddQuestion"));
const EmailOtpVerify = lazy(() => import("./pages/EmailOtpVerify"));

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
  // Detect Emergent OAuth callback synchronously (URL fragment #session_id=...).
  // This runs BEFORE any route/ProtectedRoute, avoiding race conditions where
  // AuthProvider's /me check would 401 while the cookie hasn't been set yet.
  const location = useLocation();
  if (location.hash?.includes('session_id=')) {
    return (
      <Suspense fallback={<PageLoader />}>
        <EmergentAuthCallback />
      </Suspense>
    );
  }
  return (
    <>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/landing" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/admission" element={<AdmissionForm />} />
          <Route path="/first-time-setup" element={<FirstTimeSetup />} />
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
          <Route path="/teacher/question-bank" element={<ProtectedRoute><TeacherLayout><BrowseQuestionBank /></TeacherLayout></ProtectedRoute>} />
          <Route path="/teacher/question-bank/new" element={<ProtectedRoute><TeacherLayout><AddQuestion /></TeacherLayout></ProtectedRoute>} />
          <Route path="/verify-email" element={<EmailOtpVerify />} />

          {/* Student Protected Routes */}
          <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
          <Route path="/classes" element={<ProtectedRoute><Layout><StudentClasses /></Layout></ProtectedRoute>} />
          <Route path="/live-classes" element={<ProtectedRoute><Layout><StudentLiveClasses /></Layout></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Layout><ProfilePage /></Layout></ProtectedRoute>} />
          <Route path="/upgrade" element={<ProtectedRoute><Layout><UpgradePage /></Layout></ProtectedRoute>} />

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
