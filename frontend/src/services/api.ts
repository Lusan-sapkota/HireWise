import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: string;
  username: string;
  email: string;
  user_type: 'job_seeker' | 'recruiter';
  first_name: string;
  last_name: string;
}

export interface JobPost {
  id: string;
  title: string;
  description: string;
  requirements: string;
  location: string;
  job_type: string;
  experience_level: string;
  salary_min?: number;
  salary_max?: number;
  skills_required: string;
  created_at: string;
  recruiter: {
    recruiter_profile: {
      company_name: string;
    };
  };
}

export interface Resume {
  id: string;
  original_filename: string;
  uploaded_at: string;
  is_primary: boolean;
  parsed_text: string;
}

export interface Application {
  id: string;
  job_post: JobPost;
  status: string;
  applied_at: string;
  match_score: number;
}

// Auth API
export const authAPI = {
  register: (userData: any) => api.post('/auth/register/', userData),
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login/', credentials),
  logout: () => api.post('/auth/logout/'),
};

// Jobs API
export const jobsAPI = {
  getJobs: (params?: any) => api.get('/jobs/', { params }),
  getJob: (id: string) => api.get(`/jobs/${id}/`),
  createJob: (jobData: any) => api.post('/jobs/', jobData),
  updateJob: (id: string, jobData: any) => api.put(`/jobs/${id}/`, jobData),
  deleteJob: (id: string) => api.delete(`/jobs/${id}/`),
  applyToJob: (jobId: string, applicationData: any) =>
    api.post(`/jobs/${jobId}/apply/`, applicationData),
};

// Resumes API
export const resumesAPI = {
  getResumes: () => api.get('/resumes/'),
  uploadResume: (formData: FormData) =>
    api.post('/resumes/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  deleteResume: (id: string) => api.delete(`/resumes/${id}/`),
  setPrimary: (id: string) => api.post(`/resumes/${id}/set_primary/`),
};

// Applications API
export const applicationsAPI = {
  getApplications: () => api.get('/applications/'),
  getApplication: (id: string) => api.get(`/applications/${id}/`),
  updateApplication: (id: string, data: any) =>
    api.put(`/applications/${id}/`, data),
};

// Profile API
export const profileAPI = {
  getProfile: () => api.get('/profile/'),
  updateProfile: (profileData: any) => api.put('/profile/', profileData),
};

export default api;
