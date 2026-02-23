import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { Toaster } from "sonner";

// Components
import AuthCallback from "./components/AuthCallback";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

// Pages
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import PYQSection from "./pages/PYQSection";
import AdmissionForm from "./pages/AdmissionForm";
import AdminPanel from "./pages/AdminPanel";
import ClassesPage from "./pages/ClassesPage";
import MyTestsPage from "./pages/MyTestsPage";
import TakeTestPage from "./pages/TakeTestPage";
import { 
  AssignedTestsPage, 
  AnalyticsPage, 
  BookmarksPage 
} from "./pages/PlaceholderPages";

function AppRouter() {
  const location = useLocation();
  
  // Check URL fragment (not query params) for session_id during render
  // This prevents race conditions by processing session_id BEFORE useEffect runs
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
      
      {/* Protected Routes with Layout */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/pyq"
        element={
          <ProtectedRoute>
            <PYQSection />
          </ProtectedRoute>
        }
      />
      <Route
        path="/my-tests"
        element={
          <ProtectedRoute>
            <Layout>
              <MyTestsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/assigned-tests"
        element={
          <ProtectedRoute>
            <Layout>
              <AssignedTestsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/classes"
        element={
          <ProtectedRoute>
            <Layout>
              <ClassesPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <Layout>
              <AnalyticsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/bookmarks"
        element={
          <ProtectedRoute>
            <Layout>
              <BookmarksPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/test/:testId/take"
        element={
          <ProtectedRoute>
            <TakeTestPage />
          </ProtectedRoute>
        }
      />
      
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
