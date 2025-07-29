import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';

const VerifyOtp: React.FC = () => {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [resendTimer, setResendTimer] = useState(30);
  const [resendCount, setResendCount] = useState(0);
  const [resendLoading, setResendLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email;
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const handleResend = async () => {
    if (!email) return;
    setResendLoading(true);
    setError('');
    setSuccess('');
    try {
      await apiService.requestEmailVerification(email);
      setSuccess('Verification email resent!');
      setResendCount(resendCount + 1);
      setResendTimer(resendCount === 0 ? 60 : 60); // 30s for first, 60s for subsequent
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to resend verification email.');
    } finally {
      setResendLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await apiService.verifyEmail(otp);
      setSuccess('Email verified! Redirecting...');
      setTimeout(() => {
        navigate('/complete-profile');
      }, 1200);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Invalid or expired OTP.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Verify Your Email</h2>
        <div className="mb-4">
          <label className="block mb-1 font-medium" htmlFor="otp">OTP / Verification Code</label>
          <input
            id="otp"
            name="otp"
            type="text"
            value={otp}
            onChange={e => setOtp(e.target.value)}
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring"
            required
          />
        </div>
        {error && <div className="text-red-500 mb-4">{error}</div>}
        {success && <div className="text-green-600 mb-4">{success}</div>}
        <button
          type="submit"
          className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition mb-2"
          disabled={loading}
        >
          {loading ? 'Verifying...' : 'Verify'}
        </button>
        <button
          type="button"
          className="w-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 py-2 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition"
          onClick={handleResend}
          disabled={resendTimer > 0 || resendLoading || !email}
        >
          {resendLoading ? 'Resending...' : resendTimer > 0 ? `Resend OTP (${resendTimer}s)` : 'Resend OTP'}
        </button>
      </form>
    </div>
  );
};

export default VerifyOtp;
