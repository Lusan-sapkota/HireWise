import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { 
  apiService, 
  User, 
  JobSeekerProfile, 
  RecruiterProfile, 
  AuthenticationError,
  AuthorizationError,
  ValidationError,
  NetworkError
} from '../services/api';

interface AuthContextType {
  user: User | null;
  userProfile: JobSeekerProfile | RecruiterProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  userRole: 'job_seeker' | 'recruiter' | 'admin' | null;
  login: (username: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  updateProfile: (data: any) => Promise<void>;
  refreshUser: () => Promise<void>;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<JobSeekerProfile | RecruiterProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializeAuth();
    
    // Set up authentication listener
    const handleAuthChange = (isAuthenticated: boolean) => {
      if (!isAuthenticated) {
        setUser(null);
        setUserProfile(null);
      }
    };
    
    apiService.addAuthListener(handleAuthChange);
    
    return () => {
      apiService.removeAuthListener(handleAuthChange);
    };
  }, []);

  const initializeAuth = async () => {
    try {
      setError(null);
      if (apiService.isAuthenticated()) {
        const response = await apiService.getUserProfile();
        setUser(response.data);
        await loadUserProfile(response.data);
      }
    } catch (error) {
      console.error('Failed to initialize auth:', error);
      handleAuthError(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthError = (error: any) => {
    if (error instanceof AuthenticationError) {
      setError('Authentication failed. Please log in again.');
    } else if (error instanceof AuthorizationError) {
      setError('You do not have permission to access this resource.');
    } else if (error instanceof ValidationError) {
      setError('Please check your input and try again.');
    } else if (error instanceof NetworkError) {
      setError('Network connection failed. Please check your internet connection.');
    } else {
      setError(error.message || 'An unexpected error occurred.');
    }
  };

  const clearError = () => {
    setError(null);
  };

  const loadUserProfile = async (userData: User) => {
    try {
      if (userData.user_type === 'job_seeker') {
        const profileResponse = await apiService.getJobSeekerProfile();
        setUserProfile(profileResponse.data);
      } else if (userData.user_type === 'recruiter') {
        const profileResponse = await apiService.getRecruiterProfile();
        setUserProfile(profileResponse.data);
      }
    } catch (error: any) {
      // Profile might not exist yet, which is fine for new users
      if (error.response?.status === 404) {
        console.log('Profile not found, user may need to complete profile setup');
      } else {
        console.warn('Failed to load user profile:', error.message);
      }
      setUserProfile(null);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      setError(null);
      const response = await apiService.login({ username, password });
      setUser(response.data.user);
      await loadUserProfile(response.data.user);
    } catch (error) {
      handleAuthError(error);
      throw error;
    }
  };

  const register = async (data: any) => {
    try {
      setError(null);
      const response = await apiService.register(data);
      setUser(response.data.user);
      // Profile won't exist yet for new users, so we don't load it
      setUserProfile(null);
    } catch (error) {
      handleAuthError(error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await apiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setUserProfile(null);
    }
  };

  const updateUser = async (data: Partial<User>) => {
    try {
      const response = await apiService.updateUserProfile(data);
      setUser(response.data);
    } catch (error) {
      throw error;
    }
  };

  const refreshUser = async () => {
    try {
      const response = await apiService.getUserProfile();
      setUser(response.data);
      await loadUserProfile(response.data);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  const updateProfile = async (data: any) => {
    try {
      if (!user) throw new Error('User not authenticated');
      
      let response;
      if (user.user_type === 'job_seeker') {
        response = await apiService.updateJobSeekerProfile(data);
      } else if (user.user_type === 'recruiter') {
        response = await apiService.updateRecruiterProfile(data);
      } else {
        throw new Error('Invalid user type');
      }
      
      setUserProfile(response.data);
    } catch (error) {
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    userProfile,
    isAuthenticated: !!user,
    isLoading,
    userRole: user?.user_type || null,
    login,
    register,
    logout,
    updateUser,
    updateProfile,
    refreshUser,
    error,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};