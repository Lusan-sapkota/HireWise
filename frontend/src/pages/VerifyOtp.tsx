import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { 
  Shield, 
  Mail, 
  Phone, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  ArrowLeft,
  RefreshCw
} from 'lucide-react';

const VerifyOtp: React.FC = () => {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [resendTimer, setResendTimer] = useState(60);
  const [resendLoading, setResendLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  // Get data from previous page
  const email = location.state?.email;
  const phoneNumber = location.state?.phoneNumber;
  const purpose = location.state?.purpose || 'signup'; // 'signup', 'login', 'password_reset'
  const userData = location.state?.userData; // For signup completion
  const verificationType = phoneNumber ? 'phone' : 'email';
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  // Redirect if no verification data
  useEffect(() => {
    if (!email && !phoneNumber) {
      navigate('/signup');
    }
  }, [email, phoneNumber, navigate]);

  const handleResend = async () => {
    if (!email && !phoneNumber) return;
    
    setResendLoading(true);
    setError('');
    setSuccess('');
    
    try {
      if (phoneNumber) {
        await apiService.resendOTP(phoneNumber, purpose);
        setSuccess('OTP resent to your phone!');
      } else {
        await apiService.requestEmailVerification(email);
        setSuccess('Verification email resent!');
      }
      setResendTimer(60);
    } catch (err: any) {
      setError(err.response?.data?.message || `Failed to resend ${verificationType === 'phone' ? 'OTP' : 'verification email'}.`);
    } finally {
      setResendLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!otp.trim()) {
      setError('Please enter the verification code');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      if (verificationType === 'phone') {
        // Phone OTP verification
        await apiService.verifyOTP(phoneNumber, otp, purpose);
        
        if (purpose === 'signup' && userData) {
          // Complete registration with verified phone
          const registrationData = { ...userData, otp, phone_number: phoneNumber };
          const response = await apiService.registerWithOTP(registrationData);
          
          if (response.data.user) {
            setSuccess('Account created successfully! Redirecting...');
            setTimeout(() => {
              navigate('/complete-profile');
            }, 1500);
          }
        } else {
          setSuccess('Phone verified successfully!');
          setTimeout(() => {
            navigate(purpose === 'password_reset' ? '/reset-password' : '/complete-profile');
          }, 1500);
        }
      } else {
        // Email verification
        await apiService.verifyEmail(otp);
        setSuccess('Email verified! Redirecting...');
        setTimeout(() => {
          navigate('/complete-profile');
        }, 1500);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Invalid or expired verification code.');
    } finally {
      setLoading(false);
    }
  };

  const getDisplayContact = () => {
    if (phoneNumber) {
      return phoneNumber.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
    }
    if (email) {
      return email.replace(/(.{2})(.*)(@.*)/, '$1***$3');
    }
    return '';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center">
            <Shield className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900 dark:text-white">
            Verify Your {verificationType === 'phone' ? 'Phone' : 'Email'}
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            We sent a {verificationType === 'phone' ? '6-digit code' : 'verification link'} to
          </p>
          <div className="flex items-center justify-center space-x-2 mt-2">
            {verificationType === 'phone' ? (
              <Phone className="w-4 h-4 text-gray-500" />
            ) : (
              <Mail className="w-4 h-4 text-gray-500" />
            )}
            <span className="font-medium text-gray-900 dark:text-white">
              {getDisplayContact()}
            </span>
          </div>
        </div>

        <Card>
          <CardContent className="p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              
              {/* OTP Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {verificationType === 'phone' ? 'Verification Code' : 'Email Verification Code'}
                </label>
                <Input
                  type="text"
                  placeholder={verificationType === 'phone' ? 'Enter 6-digit code' : 'Enter verification code'}
                  value={otp}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '');
                    setOtp(verificationType === 'phone' ? value.slice(0, 6) : value);
                  }}
                  className="w-full text-center text-2xl tracking-widest"
                  maxLength={verificationType === 'phone' ? 6 : 8}
                  autoComplete="one-time-code"
                />
                {verificationType === 'phone' && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">
                    Enter the 6-digit code sent to your phone
                  </p>
                )}
              </div>

              {/* Error/Success Messages */}
              {error && (
                <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              {success && (
                <div className="flex items-center space-x-2 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                  <CheckCircle className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm">{success}</span>
                </div>
              )}

              {/* Verify Button */}
              <Button
                type="submit"
                disabled={loading || !otp.trim() || (verificationType === 'phone' && otp.length !== 6)}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Verify Code'
                )}
              </Button>

              {/* Resend Section */}
              <div className="text-center space-y-3">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Didn't receive the code?
                </p>
                
                {resendTimer > 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Resend code in {resendTimer}s
                  </p>
                ) : (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleResend}
                    disabled={resendLoading}
                    className="w-full"
                  >
                    {resendLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Resending...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Resend Code
                      </>
                    )}
                  </Button>
                )}
              </div>

              {/* Back Button */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => navigate(-1)}
                  className="flex items-center justify-center space-x-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white w-full"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Help Text */}
        <div className="text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Having trouble? Contact our support team for assistance.
          </p>
        </div>
      </div>
    </div>
  );
};

export default VerifyOtp;
