import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();
  const [checkComplete, setCheckComplete] = useState(location.state?.user ? true : false);

  useEffect(() => {
    // If user data was passed from AuthCallback, skip check
    if (location.state?.user) {
      setCheckComplete(true);
      return;
    }

    // Wait for auth check to complete
    if (!loading) {
      setCheckComplete(true);
    }
  }, [loading, location.state]);

  // Show loading while checking
  if (!checkComplete) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
