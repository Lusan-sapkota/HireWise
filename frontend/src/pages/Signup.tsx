import React, { useState } from 'react';
import { GoogleLogin, googleLogout, GoogleOAuthProvider } from '@react-oauth/google';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, AlertCircle, CheckCircle, User, Mail, Phone, Lock } from 'lucide-react';
import { apiService } from '../services/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import Footer from '../components/layout/Footer';
const logo = '/logo.png';

export const Signup: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    user_type: 'job_seeker' as 'job_seeker' | 'recruiter',
    phone_number: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setFieldErrors(prev => ({ ...prev, [name]: '' }));
    if (error) setError('');
  };

  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    // First name
    if (!formData.first_name.trim()) {
      errors.first_name = 'First name is required';
    }
    // Last name
    if (!formData.last_name.trim()) {
      errors.last_name = 'Last name is required';
    }
    // Username
    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    } else if (!/^[a-zA-Z0-9_]{3,20}$/.test(formData.username)) {
      errors.username = 'Username must be 3-20 characters, letters, numbers, or _';
    }
    // Email
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    // Phone (optional)
    if (formData.phone_number && !/^\+?[0-9\-\s]{7,20}$/.test(formData.phone_number)) {
      errors.phone_number = 'Enter a valid phone number';
    }
    // Password
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (!/^(?=.*[A-Za-z])(?=.*\d).{8,}$/.test(formData.password)) {
      errors.password = 'Password must contain at least one letter and one number';
    }
    // Confirm password
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      setError('Please fix the errors below');
      return false;
    }
    setError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsLoading(true);
    setError('');

    try {
      const { confirmPassword, ...registrationData } = formData;
      await apiService.register(registrationData);
      setSuccess('Account created successfully! Please complete your profile.');
      setTimeout(() => {
        navigate('/complete-profile');
      }, 1200);
    } catch (err: any) {
      const errorMessage = err.response?.data?.error?.message || 
                          err.response?.data?.detail ||
                          err.response?.data?.username?.[0] ||
                          err.response?.data?.email?.[0] ||
                          'Registration failed. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Main Content Container */}
      <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900 transition-colors p-3 sm:p-4 lg:p-6">
        <div className="w-full max-w-sm sm:max-w-md md:max-w-5xl lg:max-w-6xl xl:max-w-7xl">
          <div className="bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl lg:rounded-2xl shadow-sm sm:shadow-lg lg:shadow-xl overflow-hidden">
            <div className="flex flex-col md:flex-row min-h-[600px] sm:min-h-[700px] md:min-h-[750px]">
              
              {/* Left Column - Branding (Hidden on mobile, visible on md+) */}
              <div className="hidden md:flex md:w-2/5 lg:w-1/2 flex-col items-center justify-center bg-gradient-to-br from-indigo-500 via-violet-500 to-indigo-600 p-6 lg:p-8 xl:p-12">
                <div className="text-center space-y-4 lg:space-y-6">
                  <div className="mx-auto">
                    <img 
                      src={logo} 
                      alt="HireWise Logo" 
                      className="w-16 h-16 lg:w-20 lg:h-20 xl:w-24 xl:h-24 mx-auto rounded-lg shadow-lg bg-white/10 backdrop-blur-sm p-2 lg:p-3" 
                    />
                  </div>
                  <div className="space-y-2 lg:space-y-3">
                    <h2 className="text-2xl lg:text-3xl xl:text-4xl font-bold text-white">Welcome to HireWise</h2>
                    <p className="text-indigo-100 text-base lg:text-lg xl:text-xl leading-relaxed max-w-xs lg:max-w-sm mx-auto">
                      Create your account to get started with AI-powered hiring and job search
                    </p>
                  </div>
                  <div className="hidden lg:block w-16 h-1 bg-white/20 rounded-full mx-auto"></div>
                </div>
              </div>

              {/* Right Column - Signup Form */}
              <div className="w-full md:w-3/5 lg:w-1/2 flex flex-col justify-center p-4 sm:p-6 lg:p-8 xl:p-12">
                
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
                    Create your account
                  </h1>
                  <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 md:hidden">
                    Join thousands of professionals advancing their careers
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
                            setSuccess('Google sign-in successful!');
                            setTimeout(() => {
                              navigate('/complete-profile');
                            }, 1200);
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
                  <div className="mb-4 p-3 sm:p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg lg:rounded-xl flex items-start space-x-2 sm:space-x-3">
                    <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <span className="text-xs sm:text-sm text-red-700 dark:text-red-300 leading-relaxed">{error}</span>
                  </div>
                )}
                
                {success && (
                  <div className="mb-4 p-3 sm:p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg lg:rounded-xl flex items-start space-x-2 sm:space-x-3">
                    <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-xs sm:text-sm text-green-700 dark:text-green-300 leading-relaxed">{success}</span>
                  </div>
                )}

                {/* Signup Form */}
                <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
                  
                  {/* Name Fields */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    <div className="space-y-1 sm:space-y-2">
                      <label htmlFor="first_name" className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                        First Name
                      </label>
                      <div className="relative">
                        <User className="absolute left-3 sm:left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
                        <Input
                          id="first_name"
                          name="first_name"
                          type="text"
                          required
                          value={formData.first_name}
                          onChange={handleInputChange}
                          className={`pl-9 sm:pl-10 lg:pl-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 ${fieldErrors.first_name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'}`}
                          placeholder="First name"
                        />
                      </div>
                      {fieldErrors.first_name && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">{fieldErrors.first_name}</p>
                      )}
                    </div>

                    <div className="space-y-1 sm:space-y-2">
                      <label htmlFor="last_name" className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                        Last Name
                      </label>
                      <div className="relative">
                        <User className="absolute left-3 sm:left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
                        <Input
                          id="last_name"
                          name="last_name"
                          type="text"
                          required
                          value={formData.last_name}
                          onChange={handleInputChange}
                          className={`pl-9 sm:pl-10 lg:pl-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 ${fieldErrors.last_name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'}`}
                          placeholder="Last name"
                        />
                      </div>
                      {fieldErrors.last_name && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">{fieldErrors.last_name}</p>
                      )}
                    </div>
                  </div>

                  {/* Username Field */}
                  <div className="space-y-1 sm:space-y-2">
                    <label htmlFor="username" className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                      Username
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 sm:left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
                      <Input
                        id="username"
                        name="username"
                        type="text"
                        required
                        value={formData.username}
                        onChange={handleInputChange}
                        className={`pl-9 sm:pl-10 lg:pl-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 ${fieldErrors.username ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'}`}
                        placeholder="Choose a username"
                      />
                    </div>
                    {fieldErrors.username && (
                      <p className="text-xs text-red-600 dark:text-red-400 mt-1">{fieldErrors.username}</p>
                    )}
                  </div>

                  {/* Email Field */}
                  <div className="space-y-1 sm:space-y-2">
                    <label htmlFor="email" className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 sm:left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={handleInputChange}
                        className={`pl-9 sm:pl-10 lg:pl-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 ${fieldErrors.email ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'}`}
                        placeholder="Enter your email"
                      />
                    </div>
                    {fieldErrors.email && (
                      <p className="text-xs text-red-600 dark:text-red-400 mt-1">{fieldErrors.email}</p>
                    )}
                  </div>

                  {/* Phone Field */}
                  <div className="space-y-1 sm:space-y-2">
                    <label htmlFor="phone_number" className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                      Phone Number <span className="text-gray-400">(Optional)</span>
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 sm:left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
                      <Input
                        id="phone_number"
                        name="phone_number"
                        type="tel"
                        value={formData.phone_number}
                        onChange={handleInputChange}
                        className={`pl-9 sm:pl-10 lg:pl-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 ${fieldErrors.phone_number ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'}`}
                        placeholder="Your phone number"
                      />
                    </div>
                    {fieldErrors.phone_number && (
                      <p className="text-xs text-red-600 dark:text-red-400 mt-1">{fieldErrors.phone_number}</p>
                    )}
                  </div>

                  {/* Password Fields */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
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
                          className={`pl-9 sm:pl-10 lg:pl-11 pr-9 sm:pr-10 lg:pr-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 ${fieldErrors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'}`}
                          placeholder="Create a password"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 sm:right-3.5 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-0.5"
                        >
                          {showPassword ? <EyeOff className="w-4 h-4 sm:w-5 sm:h-5" /> : <Eye className="w-4 h-4 sm:w-5 sm:h-5" />}
                        </button>
                      </div>
                      {fieldErrors.password && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">{fieldErrors.password}</p>
                      )}
                    </div>

                    <div className="space-y-1 sm:space-y-2">
                      <label htmlFor="confirmPassword" className="block text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                        Confirm Password
                      </label>
                      <div className="relative">
                        <Lock className="absolute left-3 sm:left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
                        <Input
                          id="confirmPassword"
                          name="confirmPassword"
                          type={showConfirmPassword ? 'text' : 'password'}
                          required
                          value={formData.confirmPassword}
                          onChange={handleInputChange}
                          className={`pl-9 sm:pl-10 lg:pl-11 pr-9 sm:pr-10 lg:pr-11 h-10 sm:h-11 lg:h-12 text-sm sm:text-base rounded-lg lg:rounded-xl transition-all duration-200 ${fieldErrors.confirmPassword ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'}`}
                          placeholder="Confirm your password"
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-3 sm:right-3.5 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-0.5"
                        >
                          {showConfirmPassword ? <EyeOff className="w-4 h-4 sm:w-5 sm:h-5" /> : <Eye className="w-4 h-4 sm:w-5 sm:h-5" />}
                        </button>
                      </div>
                      {fieldErrors.confirmPassword && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">{fieldErrors.confirmPassword}</p>
                      )}
                    </div>
                  </div>

                  {/* Terms & Conditions */}
                  <div className="flex items-start space-x-3 pt-2">
                    <input
                      id="terms"
                      name="terms"
                      type="checkbox"
                      required
                      className="h-4 w-4 sm:h-4 sm:w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded mt-0.5 transition-colors"
                    />
                    <label htmlFor="terms" className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                      I agree to the{' '}
                      <Link to="/terms" className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium transition-colors">
                        Terms of Service
                      </Link>{' '}
                      and{' '}
                      <Link to="/privacy" className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium transition-colors">
                        Privacy Policy
                      </Link>
                    </label>
                  </div>

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    className="w-full h-10 sm:h-11 lg:h-12 text-sm sm:text-base font-medium rounded-lg lg:rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed mt-6"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center space-x-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Creating account...</span>
                      </div>
                    ) : (
                      'Create account'
                    )}
                  </Button>
                </form>

                {/* Sign in Link */}
                <div className="mt-6 sm:mt-8 text-center">
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                    Already have an account?{' '}
                    <Link
                      to="/signin"
                      className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors"
                    >
                      Sign in
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
