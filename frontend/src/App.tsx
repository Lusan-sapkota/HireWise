import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { Dashboard } from './pages/Dashboard';
import { AIInterview } from './pages/AIInterview';
import { Profile } from './pages/Profile';
import { JobListings } from './pages/JobListings';
import { Messages } from './pages/Messages';
import { Notifications } from './pages/Notifications';
import { ResumeBuilder } from './pages/ResumeBuilder';
import { Signin } from './pages/Signin';
import { Signup } from './pages/Signup';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/signin" element={<Signin />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/ai-interview" element={<AIInterview />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/jobs" element={<JobListings />} />
              <Route path="/messages" element={<Messages />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/resume-builder" element={<ResumeBuilder />} />
            </Routes>
          </Layout>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;