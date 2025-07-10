import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import JobSeekerDashboard from './pages/jobseeker/Dashboard';
import RecruiterDashboard from './pages/recruiter/Dashboard';
import ResumeUpload from './pages/jobseeker/ResumeUpload';
import JobMatches from './pages/jobseeker/JobMatches';
import PostJob from './pages/recruiter/PostJob';
import Applicants from './pages/recruiter/Applicants';
import './App.css';

// Protected Route component
const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: string[] }> = ({ 
  children, 
  allowedRoles 
}) => {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.user_type)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Navbar />
          <main className="flex-grow">
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Job Seeker routes */}
              <Route 
                path="/jobseeker/dashboard" 
                element={
                  <ProtectedRoute allowedRoles={['job_seeker']}>
                    <JobSeekerDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/jobseeker/resume" 
                element={
                  <ProtectedRoute allowedRoles={['job_seeker']}>
                    <ResumeUpload />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/jobseeker/matches" 
                element={
                  <ProtectedRoute allowedRoles={['job_seeker']}>
                    <JobMatches />
                  </ProtectedRoute>
                } 
              />
              
              {/* Recruiter routes */}
              <Route 
                path="/recruiter/dashboard" 
                element={
                  <ProtectedRoute allowedRoles={['recruiter']}>
                    <RecruiterDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/recruiter/post-job" 
                element={
                  <ProtectedRoute allowedRoles={['recruiter']}>
                    <PostJob />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/recruiter/applicants/:jobId?" 
                element={
                  <ProtectedRoute allowedRoles={['recruiter']}>
                    <Applicants />
                  </ProtectedRoute>
                } 
              />
              
              {/* Fallback route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
