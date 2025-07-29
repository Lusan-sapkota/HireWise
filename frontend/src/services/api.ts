
import axios, { AxiosInstance, AxiosResponse } from 'axios';

// Types
export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: 'job_seeker' | 'recruiter' | 'admin';
  phone_number?: string;
  profile_picture?: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobSeekerProfile {
  id: string;
  user: string;
  location?: string;
  experience_level?: string;
  current_position?: string;
  expected_salary?: number;
  skills?: string;
  bio?: string;
  linkedin_url?: string;
  github_url?: string;
  availability: boolean;
}

export interface RecruiterProfile {
  id: string;
  user: string;
  company_name: string;
  company_website?: string;
  company_size?: string;
  industry?: string;
  company_description?: string;
  company_logo?: string;
  location?: string;
}

export interface JobPost {
  id: string;
  recruiter: string;
  title: string;
  description: string;
  requirements?: string;
  location: string;
  job_type?: string;
  experience_level?: string;
  salary_min?: number;
  salary_max?: number;
  skills_required?: string[];
  is_active: boolean;
  created_at: string;
  views_count: number;
  applications_count?: number;
}

export interface Resume {
  id: string;
  job_seeker: string;
  file: string;
  original_filename: string;
  parsed_text?: string;
  is_primary: boolean;
  uploaded_at: string;
  file_size: number;
}

export interface Application {
  id: string;
  job_seeker: string;
  job_post: string;
  resume: string;
  cover_letter?: string;
  status: 'pending' | 'reviewed' | 'interview' | 'accepted' | 'rejected';
  applied_at: string;
  match_score: number;
  recruiter_notes?: string;
}

export interface InterviewSession {
  id: string;
  application: string;
  session_type: string;
  scheduled_at?: string;
  duration_minutes?: number;
  meeting_link?: string;
  notes?: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  ai_analysis?: any;
  created_at: string;
}

export interface MatchScore {
  id: string;
  resume: string;
  job_post: string;
  score: number;
  matching_skills: string[];
  missing_skills: string[];
  recommendations?: string;
  calculated_at: string;
}

export interface Notification {
  id: string;
  user: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  data?: any;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  user_type: 'job_seeker' | 'recruiter';
  phone_number?: string;
}

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class APIService {
  private api: AxiosInstance;
  private wsConnections: Map<string, WebSocket> = new Map();

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.data.access);
              originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            this.logout();
            window.location.href = '/signin';
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Authentication Methods
  async login(credentials: LoginCredentials): Promise<AxiosResponse<AuthTokens & { user: User }>> {
    const response = await this.api.post('/auth/jwt/login/', credentials);
    if (response.data.access) {
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    return response;
  }

  async register(data: RegisterData): Promise<AxiosResponse<{ user: User; tokens: AuthTokens }>> {
    const response = await this.api.post('/auth/jwt/register/', data);
    if (response.data.tokens?.access) {
      localStorage.setItem('access_token', response.data.tokens.access);
      localStorage.setItem('refresh_token', response.data.tokens.refresh);
    }
    return response;
  }

  async refreshToken(refresh: string): Promise<AxiosResponse<{ access: string }>> {
    return this.api.post('/auth/jwt/token/refresh/', { refresh });
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await this.api.post('/auth/jwt/logout/', { refresh: refreshToken });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      this.closeAllWebSockets();
    }
  }

  // Google OAuth Login
  async googleLogin(id_token: string): Promise<AxiosResponse<{ user: User; tokens: AuthTokens }>> {
    const response = await this.api.post('/auth/google/', { id_token });
    if (response.data.tokens?.access) {
      localStorage.setItem('access_token', response.data.tokens.access);
      localStorage.setItem('refresh_token', response.data.tokens.refresh);
    }
    return response;
  }

  async requestEmailVerification(email: string): Promise<AxiosResponse> {
    return this.api.post('/auth/request-email-verification/', { email });
  }

  async verifyEmail(token: string): Promise<AxiosResponse> {
    return this.api.post('/auth/verify-email/', { token });
  }

  async requestPasswordReset(email: string): Promise<AxiosResponse> {
    return this.api.post('/auth/request-password-reset/', { email });
  }

  async resetPassword(token: string, password: string): Promise<AxiosResponse> {
    return this.api.post('/auth/reset-password/', { token, password });
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<AxiosResponse> {
    return this.api.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  // User Profile Methods
  async getUserProfile(): Promise<AxiosResponse<User>> {
    return this.api.get('/auth/profile/');
  }

  async updateUserProfile(data: Partial<User>): Promise<AxiosResponse<User>> {
    return this.api.patch('/auth/profile/', data);
  }

  async deleteAccount(): Promise<AxiosResponse> {
    return this.api.delete('/auth/delete-account/');
  }

  // Job Seeker Profile Methods
  async getJobSeekerProfile(id?: string): Promise<AxiosResponse<JobSeekerProfile>> {
    const url = id ? `/job-seeker-profiles/${id}/` : '/job-seeker-profiles/me/';
    return this.api.get(url);
  }

  async updateJobSeekerProfile(data: Partial<JobSeekerProfile>): Promise<AxiosResponse<JobSeekerProfile>> {
    return this.api.patch('/job-seeker-profiles/me/', data);
  }

  // Recruiter Profile Methods
  async getRecruiterProfile(id?: string): Promise<AxiosResponse<RecruiterProfile>> {
    const url = id ? `/recruiter-profiles/${id}/` : '/recruiter-profiles/me/';
    return this.api.get(url);
  }

  async updateRecruiterProfile(data: Partial<RecruiterProfile>): Promise<AxiosResponse<RecruiterProfile>> {
    return this.api.patch('/recruiter-profiles/me/', data);
  }

  // Job Posts Methods
  async getJobPosts(params?: {
    search?: string;
    location?: string;
    job_type?: string;
    experience_level?: string;
    salary_min?: number;
    salary_max?: number;
    page?: number;
    page_size?: number;
  }): Promise<AxiosResponse<{ results: JobPost[]; count: number; next?: string; previous?: string }>> {
    return this.api.get('/job-posts/', { params });
  }

  async getJobPost(id: string): Promise<AxiosResponse<JobPost>> {
    return this.api.get(`/job-posts/${id}/`);
  }

  async createJobPost(data: Omit<JobPost, 'id' | 'recruiter' | 'created_at' | 'views_count'>): Promise<AxiosResponse<JobPost>> {
    return this.api.post('/job-posts/', data);
  }

  async updateJobPost(id: string, data: Partial<JobPost>): Promise<AxiosResponse<JobPost>> {
    return this.api.patch(`/job-posts/${id}/`, data);
  }

  async deleteJobPost(id: string): Promise<AxiosResponse> {
    return this.api.delete(`/job-posts/${id}/`);
  }

  // Resume Methods
  async getResumes(): Promise<AxiosResponse<Resume[]>> {
    return this.api.get('/resumes/');
  }

  async getResume(id: string): Promise<AxiosResponse<Resume>> {
    return this.api.get(`/resumes/${id}/`);
  }

  async uploadResume(file: File, isPrimary = false): Promise<AxiosResponse<Resume>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('is_primary', isPrimary.toString());
    
    return this.api.post('/files/upload-resume/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async deleteResume(id: string): Promise<AxiosResponse> {
    return this.api.delete(`/resumes/${id}/`);
  }

  async parseResume(resumeId: string): Promise<AxiosResponse<{ parsed_text: string; key_skills: string[]; summary: string }>> {
    return this.api.post(`/parse-resume/${resumeId}/`);
  }

  async parseResumeAsync(resumeId: string): Promise<AxiosResponse<{ task_id: string }>> {
    return this.api.post('/parse-resume-async/', { resume_id: resumeId });
  }

  // Application Methods
  async getApplications(params?: {
    status?: string;
    job_post?: string;
    page?: number;
  }): Promise<AxiosResponse<{ results: Application[]; count: number }>> {
    return this.api.get('/applications/', { params });
  }

  async getApplication(id: string): Promise<AxiosResponse<Application>> {
    return this.api.get(`/applications/${id}/`);
  }

  async createApplication(data: {
    job_post: string;
    resume: string;
    cover_letter?: string;
  }): Promise<AxiosResponse<Application>> {
    return this.api.post('/applications/', data);
  }

  async updateApplicationStatus(id: string, status: Application['status'], notes?: string): Promise<AxiosResponse<Application>> {
    return this.api.patch(`/applications/${id}/`, { status, recruiter_notes: notes });
  }

  // Match Score Methods
  async calculateMatchScore(resumeId: string, jobId: string): Promise<AxiosResponse<MatchScore>> {
    return this.api.post('/calculate-match-score/', {
      resume_id: resumeId,
      job_id: jobId,
    });
  }

  async getMatchScoresForResume(resumeId: string): Promise<AxiosResponse<MatchScore[]>> {
    return this.api.get(`/match-scores/resume/${resumeId}/`);
  }

  async getMatchScoresForJob(jobId: string): Promise<AxiosResponse<MatchScore[]>> {
    return this.api.get(`/match-scores/job/${jobId}/`);
  }

  // Interview Session Methods
  async getInterviewSessions(): Promise<AxiosResponse<InterviewSession[]>> {
    return this.api.get('/interview-sessions/');
  }

  async createInterviewSession(data: {
    application: string;
    session_type: string;
    scheduled_at?: string;
    duration_minutes?: number;
  }): Promise<AxiosResponse<InterviewSession>> {
    return this.api.post('/interview-sessions/', data);
  }

  async updateInterviewSession(id: string, data: Partial<InterviewSession>): Promise<AxiosResponse<InterviewSession>> {
    return this.api.patch(`/interview-sessions/${id}/`, data);
  }

  // AI Interview Methods
  async startAIInterview(data: {
    resume_source: 'profile' | 'upload';
    interview_type: string;
    difficulty: string;
    duration: number;
    focus_areas?: string[];
    resume_file?: File;
  }): Promise<AxiosResponse<{ session_id: string; questions: string[] }>> {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (key === 'resume_file' && value instanceof File) {
        formData.append(key, value);
      } else if (key === 'focus_areas' && Array.isArray(value)) {
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, value.toString());
      }
    });

    return this.api.post('/interview-sessions/ai-start/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async submitAIInterviewResponse(sessionId: string, questionIndex: number, response: {
    text?: string;
    audio_file?: File;
    video_file?: File;
  }): Promise<AxiosResponse<{ feedback: any; next_question?: string }>> {
    const formData = new FormData();
    formData.append('question_index', questionIndex.toString());
    
    if (response.text) formData.append('text', response.text);
    if (response.audio_file) formData.append('audio_file', response.audio_file);
    if (response.video_file) formData.append('video_file', response.video_file);

    return this.api.post(`/interview-sessions/${sessionId}/ai-response/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async endAIInterview(sessionId: string): Promise<AxiosResponse<{ analysis: any; score: number; recommendations: string[] }>> {
    return this.api.post(`/interview-sessions/${sessionId}/ai-end/`);
  }

  // Recommendations Methods
  async getJobRecommendations(params?: {
    limit?: number;
    min_score?: number;
  }): Promise<AxiosResponse<{ jobs: JobPost[]; scores: MatchScore[] }>> {
    return this.api.get('/recommendations/jobs/', { params });
  }

  async getCandidateRecommendations(jobId: string, params?: {
    limit?: number;
    min_score?: number;
  }): Promise<AxiosResponse<{ candidates: JobSeekerProfile[]; scores: MatchScore[] }>> {
    return this.api.get(`/recommendations/candidates/${jobId}/`, { params });
  }

  // Search Methods
  async searchJobs(params: {
    q?: string;
    location?: string;
    job_type?: string;
    experience_level?: string;
    skills?: string[];
    salary_min?: number;
    salary_max?: number;
    sort_by?: string;
    page?: number;
  }): Promise<AxiosResponse<{ results: JobPost[]; count: number; facets: any }>> {
    return this.api.get('/search/jobs/', { params });
  }

  async searchCandidates(params: {
    q?: string;
    location?: string;
    skills?: string[];
    experience_level?: string;
    sort_by?: string;
    page?: number;
  }): Promise<AxiosResponse<{ results: JobSeekerProfile[]; count: number; facets: any }>> {
    return this.api.get('/search/candidates/', { params });
  }

  // Dashboard Methods
  async getDashboardStats(): Promise<AxiosResponse<{
    profile_views: number;
    applications_sent: number;
    interview_invites: number;
    job_matches: number;
    recent_activities: any[];
  }>> {
    return this.api.get('/dashboard/stats/');
  }

  async getPersonalizedDashboard(): Promise<AxiosResponse<{
    recommended_jobs: JobPost[];
    trending_skills: string[];
    network_updates: any[];
    ai_insights: any[];
  }>> {
    return this.api.get('/dashboard/personalized/');
  }

  // Task Management Methods
  async getTaskStatus(taskId: string): Promise<AxiosResponse<{
    status: string;
    result?: any;
    error?: string;
    progress?: number;
  }>> {
    return this.api.get(`/tasks/status/${taskId}/`);
  }

  async cancelTask(taskId: string): Promise<AxiosResponse> {
    return this.api.post(`/tasks/cancel/${taskId}/`);
  }

  // File Management Methods
  async uploadFile(file: File, fileType: string): Promise<AxiosResponse<{ file_id: string; url: string }>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);
    
    return this.api.post('/files/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async deleteFile(fileId: string): Promise<AxiosResponse> {
    return this.api.delete(`/files/delete/${fileId}/`);
  }

  async getUserFiles(): Promise<AxiosResponse<any[]>> {
    return this.api.get('/files/list/');
  }

  // WebSocket Methods
  connectWebSocket(endpoint: string, onMessage?: (data: any) => void): WebSocket | null {
    try {
      const token = localStorage.getItem('access_token');
      const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/${endpoint}/?token=${token}`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log(`WebSocket connected: ${endpoint}`);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (onMessage) {
          onMessage(data);
        }
      };
      
      ws.onerror = (error) => {
        console.error(`WebSocket error on ${endpoint}:`, error);
      };
      
      ws.onclose = () => {
        console.log(`WebSocket disconnected: ${endpoint}`);
        this.wsConnections.delete(endpoint);
      };
      
      this.wsConnections.set(endpoint, ws);
      return ws;
    } catch (error) {
      console.error(`Failed to connect WebSocket ${endpoint}:`, error);
      return null;
    }
  }

  disconnectWebSocket(endpoint: string): void {
    const ws = this.wsConnections.get(endpoint);
    if (ws) {
      ws.close();
      this.wsConnections.delete(endpoint);
    }
  }

  closeAllWebSockets(): void {
    this.wsConnections.forEach((ws, endpoint) => {
      ws.close();
    });
    this.wsConnections.clear();
  }

  // Notification Methods
  async getNotifications(params?: {
    is_read?: boolean;
    notification_type?: string;
    page?: number;
  }): Promise<AxiosResponse<{ results: Notification[]; count: number }>> {
    return this.api.get('/notifications/', { params });
  }

  async markNotificationAsRead(id: string): Promise<AxiosResponse<Notification>> {
    return this.api.patch(`/notifications/${id}/`, { is_read: true });
  }

  async markAllNotificationsAsRead(): Promise<AxiosResponse> {
    return this.api.post('/notifications/mark-all-read/');
  }

  // Utility Methods
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  getAuthToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // Health Check
  async healthCheck(): Promise<AxiosResponse> {
    return this.api.get('/health/');
  }
}

// Create and export a singleton instance
export const apiService = new APIService();
export default apiService;