import React, { useState } from 'react';
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { apiService } from '../services/api';
import { Eye, EyeOff, Mail, Lock, AlertCircle, CheckCircle } from 'lucide-react';
import Footer from '../components/layout/Footer';
const logo = '/logo.png';

export const Signin: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await apiService.login(formData);
      setSuccess('Login successful! Redirecting...');
      // Redirect based on user type
      const userType = response.data.user.user_type;
      setTimeout(() => {
        if (userType === 'recruiter') {
          navigate('/dashboard/recruiter');
        } else {
          navigate('/dashboard');
        }
      }, 1000);
    } catch (err: any) {
      setError(
        err.response?.data?.error?.message || 
        err.response?.data?.detail || 
        'Login failed. Please check your credentials.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Main Content Container */}
      <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900 transition-colors p-3 sm:p-4 lg:p-6">
        <div className="w-full max-w-sm sm:max-w-md md:max-w-4xl lg:max-w-5xl xl:max-w-6xl">
          <div className="bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl lg:rounded-2xl shadow-sm sm:shadow-lg lg:shadow-xl overflow-hidden">
            <div className="flex flex-col md:flex-row min-h-[500px] sm:min-h-[600px] md:min-h-[650px]">
              
              {/* Left Column - Branding (Hidden on mobile, visible on md+) */}
              <div className="hidden md:flex md:w-1/2 lg:w-2/5 xl:w-1/2 flex-col items-center justify-center bg-gradient-to-br from-indigo-500 via-violet-500 to-indigo-600 p-6 lg:p-8 xl:p-12">
                <div className="text-center space-y-4 lg:space-y-6">
                  <div className="mx-auto">
                    <img 
                      src={logo} 
                      alt="HireWise Logo" 
                      className="w-16 h-16 lg:w-20 lg:h-20 xl:w-24 xl:h-24 mx-auto rounded-lg shadow-lg bg-white/10 backdrop-blur-sm p-2 lg:p-3" 
                    />
                  </div>
                  <div className="space-y-2 lg:space-y-3">
                    <h2 className="text-2xl lg:text-3xl xl:text-4xl font-bold text-white">Welcome back</h2>
                    <p className="text-indigo-100 text-base lg:text-lg xl:text-xl leading-relaxed max-w-xs lg:max-w-sm mx-auto">
                      Sign in to your HireWise account and continue your career journey
                    </p>
                  </div>
                  <div className="hidden lg:block w-16 h-1 bg-white/20 rounded-full mx-auto"></div>
                </div>
              </div>

              {/* Right Column - Sign in Form */}
              <div className="w-full md:w-1/2 lg:w-3/5 xl:w-1/2 flex flex-col justify-center p-4 sm:p-6 lg:p-8 xl:p-12">
                
                {/* Mobile Logo (visible only on mobile) */}
                <div className="flex md:hidden justify-center mb-6 sm:mb-8">
                  <div className="relative">
                    <img 
                      src={logo} 
                      alt="HireWise Logo" 
                      className="w-16 h-16 sm:w-20 sm:h-20 rounded-lg shadow-lg bg-gradient-to-br from-indigo-500 to-violet-500 p-2" 
                    />
                  </div>
                </div>

                {/* Form Header */}
                <div className="text-center md:text-left mb-6 sm:mb-8">
                  <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    Sign in to your account
                  </h1>
                  <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 md:hidden">
                    Welcome back! Please enter your details.
                  </p>
                </div>

                {/* Google OAuth Button */}
                <div className="mb-4 sm:mb-6">
                  <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
                    <GoogleLogin
                      onSuccess={async (credentialResponse) => {
                        if (credentialResponse.credential) {
                          try {
                            const res = await apiService.googleLogin(credentialResponse.credential);
                            setSuccess('Google sign-in successful! Redirecting...');
                            const userType = res.data.user.user_type;
                            setTimeout(() => {
                              if (userType === 'recruiter') {
                                navigate('/dashboard/recruiter');
                              } else {
                                navigate('/dashboard');
                              }
                            }, 1000);
                          } catch (err: any) {
                            setError(err.response?.data?.error || 'Google sign-in failed.');
                          }
                        }
                      }}
                      onError={() => setError('Google sign-in failed.')}
                      width="100%"
                      useOneTap
                    />
                  </GoogleOAuthProvider>
                  {/* Divider */}
                  <div className="flex items-center my-4 sm:my-6">
                    <div className="flex-grow border-t border-gray-300 dark:border-gray-600"></div>
                    <span className="mx-3 sm:mx-4 text-gray-400 dark:text-gray-500 text-xs sm:text-sm font-medium">or</span>
                    <div className="flex-grow border-t border-gray-300 dark:border-gray-600"></div>
                  </div>
                </div>

                {/* Error/Success Messages */}
                {error && (
                  <div className="mb-4 p-3 sm:p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg lg:rounded-xl flex items-start sm:items-center space-x-2 sm:space-x-3">
                    <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-600 flex-shrink-0 mt-0.5 sm:mt-0" />
                    <span className="text-xs sm:text-sm text-red-700 dark:text-red-300 leading-relaxed">{error}</span>
                  </div>
                )}
                
                {success && (
                  <div className="mb-4 p-3 sm:p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg lg:rounded-xl flex items-start sm:items-center space-x-2 sm:space-x-3">
                    <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0 mt-0.5 sm:mt-0" />
                    <span className="text-xs sm:text-sm text-green-700 dark:text-green-300 leading-relaxed">{success}</span>
                  </div>
                )}

                {/* Sign in Form */}
                <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5 lg:space-y-6">
                  
                  {/* Username/Email Field */}
                  <div className="space-y-1 sm:space-y-2">
                    <label htmlFor="username" className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                      Username or Email
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 sm:left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
                      <Input
                        id="username"
                        name="username"
                        type="text"
                        required
                        value={formData.username}
                        onChange={handleInputChange}
                        className="pl-9 sm:pl-10 lg:pl-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Enter your username or email"
                      />
                    </div>
                  </div>

                  {/* Password Field */}
                  <div className="space-y-1 sm:space-y-2">
                    <label htmlFor="password" className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 sm:left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
                      <Input
                        id="password"
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        value={formData.password}
                        onChange={handleInputChange}
                        className="pl-9 sm:pl-10 lg:pl-11 pr-9 sm:pr-10 lg:pr-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Enter your password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 sm:right-3.5 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-0.5"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4 sm:w-5 sm:h-5" /> : <Eye className="w-4 h-4 sm:w-5 sm:h-5" />}
                      </button>
                    </div>
                  </div>

                  {/* Remember Me & Forgot Password */}
                  <div className="flex flex-col xs:flex-row items-start xs:items-center justify-between gap-3 xs:gap-2 pt-1">
                    <div className="flex items-center">
                      <input
                        id="remember-me"
                        name="remember-me"
                        type="checkbox"
                        className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded transition-colors"
                      />
                      <label htmlFor="remember-me" className="ml-2 block text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                        Remember me
                      </label>
                    </div>
                    <Link
                      to="/forgot-password"
                      className="text-xs sm:text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium transition-colors"
                    >
                      Forgot password?
                    </Link>
                  </div>

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    className="w-full h-10 sm:h-11 lg:h-12 text-sm sm:text-base font-medium rounded-lg lg:rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center space-x-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Signing in...</span>
                      </div>
                    ) : (
                      'Sign in'
                    )}
                  </Button>
                </form>

                {/* Sign up Link */}
                <div className="mt-6 sm:mt-8 text-center">
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                    Don't have an account?{' '}
                    <Link
                      to="/signup"
                      className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors"
                    >
                      Sign up
                    </Link>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
};
