import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { Dashboard } from './pages/Dashboard';
import { AIInterview } from './pages/AIInterview';
import { Profile } from './pages/Profile';
import { JobListings } from './pages/JobListings';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/ai-interview" element={<AIInterview />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/jobs" element={<JobListings />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;