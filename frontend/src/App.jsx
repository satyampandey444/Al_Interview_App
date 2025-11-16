import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import AdminDashboard from './pages/AdminDashboard';
import CandidateDashboard from './pages/CandidateDashboard';
import TakeTest from './pages/TakeTest';
import './App.css';

// Protected route component for Admin
function AdminRoute({ children }) {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-screen"><div className="spinner"></div></div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (!isAdmin) {
    return <Navigate to="/candidate" />;
  }
  
  return children;
}

// Protected route component for Candidate
function CandidateRoute({ children }) {
  const { isAuthenticated, isCandidate, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-screen"><div className="spinner"></div></div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (!isCandidate) {
    return <Navigate to="/admin" />;
  }
  
  return children;
}

// Home redirect based on role
function Home() {
  const { isAuthenticated, isAdmin, isCandidate, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-screen"><div className="spinner"></div></div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (isAdmin) {
    return <Navigate to="/admin" />;
  }
  
  if (isCandidate) {
    return <Navigate to="/candidate" />;
  }
  
  return <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminDashboard />
              </AdminRoute>
            }
          />
          
          <Route
            path="/candidate"
            element={
              <CandidateRoute>
                <CandidateDashboard />
              </CandidateRoute>
            }
          />
          
          <Route
            path="/candidate/test/:testId"
            element={
              <CandidateRoute>
                <TakeTest />
              </CandidateRoute>
            }
          />
          
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
