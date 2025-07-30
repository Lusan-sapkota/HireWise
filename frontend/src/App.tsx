import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { useLenis } from './hooks/useLenis';
import Lenis from 'lenis';
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
import About from './pages/About';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import Contact from './pages/Contact';

import CompleteProfile from './pages/CompleteProfile';
import EmailSignup from './pages/EmailSignup';
import VerifyOtp from './pages/VerifyOtp';
import { ForgotPassword } from './pages/ForgotPassword';
import { EmailNotificationSettings } from './pages/EmailNotificationSettings';
import SettingsPage from './pages/SettingsPage';
import RequireAuth from './components/auth/RequireAuth';

function ScrollToTop({ lenis }: { lenis: Lenis | null }) {
  const { pathname } = useLocation();
  useEffect(() => {
    if (lenis) {
      lenis.scrollTo(0, { immediate: false });
    } else {
      window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    }
  }, [pathname, lenis]);
  return null;
}

function App() {
  const lenisRef = useLenis();
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <ScrollToTop lenis={lenisRef.current} />
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/signin" element={<Signin />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/email-signup" element={<EmailSignup />} />
              <Route path="/verify-otp" element={<VerifyOtp />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/about" element={<About />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/terms" element={<Terms />} />
              <Route path="/contact" element={<Contact />} />

              {/* AI Interview - accessible to both logged in and logged out users */}
              <Route path="/ai-interview" element={<AIInterview />} />

              {/* Protected routes */}
              <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
              <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
              <Route path="/jobs" element={<RequireAuth><JobListings /></RequireAuth>} />
              <Route path="/messages" element={<RequireAuth><Messages /></RequireAuth>} />
              <Route path="/notifications" element={<RequireAuth><Notifications /></RequireAuth>} />
              <Route path="/email-settings" element={<RequireAuth><EmailNotificationSettings /></RequireAuth>} />
              <Route path="/resume-builder" element={<RequireAuth><ResumeBuilder /></RequireAuth>} />
              <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
              <Route path="/complete-profile" element={<RequireAuth><CompleteProfile /></RequireAuth>} />
            </Routes>
          </Layout>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;