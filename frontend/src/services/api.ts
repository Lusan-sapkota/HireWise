import axios, { AxiosInstance, AxiosResponse } from "axios";

// Types
export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: "job_seeker" | "recruiter" | "admin";
  phone_number?: string;
  profile_picture?: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

// Enhanced profile data models
export interface Skill {
  id?: string;
  name: string;
  proficiency_level: "beginner" | "intermediate" | "advanced" | "expert";
  years_of_experience?: number;
}

export interface Education {
  id?: string;
  institution: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date?: string;
  is_current: boolean;
  gpa?: number;
  description?: string;
}

export interface WorkExperience {
  id?: string;
  company: string;
  position: string;
  start_date: string;
  end_date?: string;
  is_current: boolean;
  description?: string;
  location?: string;
  achievements?: string[];
}

export interface Project {
  id?: string;
  title: string;
  description: string;
  technologies_used: string[];
  start_date: string;
  end_date?: string;
  is_ongoing: boolean;
  project_url?: string;
  github_url?: string;
  role?: string;
}

export interface Certification {
  id?: string;
  name: string;
  issuing_organization: string;
  issue_date: string;
  expiry_date?: string;
  credential_id?: string;
  credential_url?: string;
}

export interface Award {
  id?: string;
  title: string;
  issuer: string;
  date_received: string;
  description?: string;
}

export interface VolunteerExperience {
  id?: string;
  organization: string;
  role: string;
  start_date: string;
  end_date?: string;
  is_current: boolean;
  description?: string;
  cause?: string;
}

export interface JobSeekerProfile {
  id: string;
  user: string;
  location?: string;
  experience_level?:
    | "entry"
    | "junior"
    | "mid"
    | "senior"
    | "lead"
    | "executive";
  current_position?: string;
  expected_salary?: number;
  bio?: string;
  professional_summary?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  availability?:
    | "immediately"
    | "within_2_weeks"
    | "within_month"
    | "not_looking";
  skills: Skill[];
  education: Education[];
  work_experience: WorkExperience[];
  projects: Project[];
  certifications: Certification[];
  awards: Award[];
  volunteer_experience: VolunteerExperience[];
  created_at?: string;
  updated_at?: string;
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
  status: "pending" | "reviewed" | "interview" | "accepted" | "rejected";
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
  status: "scheduled" | "completed" | "cancelled";
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
  user_type: "job_seeker" | "recruiter";
  phone_number?: string;
}

// API Configuration
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000/ws";

// Enhanced error types
export interface APIError {
  message: string;
  status: number;
  code?: string;
  details?: any;
}

export class AuthenticationError extends Error {
  constructor(message: string, public status: number = 401) {
    super(message);
    this.name = "AuthenticationError";
  }
}

export class AuthorizationError extends Error {
  constructor(message: string, public status: number = 403) {
    super(message);
    this.name = "AuthorizationError";
  }
}

export class ValidationError extends Error {
  constructor(message: string, public errors: any = {}) {
    super(message);
    this.name = "ValidationError";
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}

// Token management interface
interface TokenManager {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(access: string, refresh: string): void;
  clearTokens(): void;
  isTokenExpired(token: string): boolean;
}

class LocalStorageTokenManager implements TokenManager {
  getAccessToken(): string | null {
    return localStorage.getItem("access_token");
  }

  getRefreshToken(): string | null {
    return localStorage.getItem("refresh_token");
  }

  setTokens(access: string, refresh: string): void {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }

  clearTokens(): void {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch {
      return true;
    }
  }
}

// WebSocket connection manager
interface WebSocketConnection {
  ws: WebSocket;
  endpoint: string;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  reconnectInterval: number;
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
}

class APIService {
  private api: AxiosInstance;
  private wsConnections: Map<string, WebSocketConnection> = new Map();
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();
  private tokenManager: TokenManager;
  private refreshPromise: Promise<string> | null = null;
  private authEventListeners: Set<(isAuthenticated: boolean) => void> =
    new Set();

  constructor() {
    this.tokenManager = new LocalStorageTokenManager();
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 30000, // 30 second timeout
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor to add auth token and handle role-based routing
    this.api.interceptors.request.use(
      (config) => {
        const token = this.tokenManager.getAccessToken();
        if (token && !this.tokenManager.isTokenExpired(token)) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request ID for tracking
        config.headers["X-Request-ID"] = this.generateRequestId();

        return config;
      },
      (error) => {
        console.error("Request interceptor error:", error);
        return Promise.reject(this.handleError(error));
      }
    );

    // Response interceptor with enhanced error handling and automatic token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Handle network errors
        if (!error.response) {
          throw new NetworkError(
            "Network connection failed. Please check your internet connection."
          );
        }

        const { status } = error.response;

        // Handle authentication errors with automatic token refresh
        if (status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newAccessToken = await this.handleTokenRefresh();
            if (newAccessToken) {
              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            this.handleAuthenticationFailure();
            throw new AuthenticationError(
              "Session expired. Please log in again."
            );
          }
        }

        // Handle other status codes
        if (status === 403) {
          throw new AuthorizationError(
            "You do not have permission to perform this action."
          );
        }

        if (status === 422 || status === 400) {
          const validationErrors =
            error.response.data?.errors || error.response.data;
          throw new ValidationError("Validation failed", validationErrors);
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  private async handleTokenRefresh(): Promise<string | null> {
    // Prevent multiple simultaneous refresh requests
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.tokenManager.getRefreshToken();
    if (!refreshToken || this.tokenManager.isTokenExpired(refreshToken)) {
      throw new AuthenticationError("Refresh token expired");
    }

    this.refreshPromise = this.performTokenRefresh(refreshToken);

    try {
      const newAccessToken = await this.refreshPromise;
      return newAccessToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(refreshToken: string): Promise<string> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/auth/jwt/token/refresh/`,
        {
          refresh: refreshToken,
        }
      );

      const { access } = response.data;
      this.tokenManager.setTokens(access, refreshToken);
      return access;
    } catch (error) {
      this.tokenManager.clearTokens();
      throw error;
    }
  }

  private handleAuthenticationFailure(): void {
    this.tokenManager.clearTokens();
    this.closeAllWebSockets();
    this.notifyAuthListeners(false);

    // Redirect to login page if not already there
    if (window.location.pathname !== "/signin") {
      window.location.href = "/signin";
    }
  }

  private handleError(error: any): APIError {
    if (error.response) {
      return {
        message:
          error.response.data?.message ||
          error.response.data?.detail ||
          "An error occurred",
        status: error.response.status,
        code: error.response.data?.code,
        details: error.response.data,
      };
    } else if (error.request) {
      return {
        message: "Network error - please check your connection",
        status: 0,
      };
    } else {
      return {
        message: error.message || "An unexpected error occurred",
        status: 0,
      };
    }
  }

  private generateRequestId(): string {
    return (
      Math.random().toString(36).substring(2, 15) +
      Math.random().toString(36).substring(2, 15)
    );
  }

  // Authentication event listeners
  public addAuthListener(listener: (isAuthenticated: boolean) => void): void {
    this.authEventListeners.add(listener);
  }

  public removeAuthListener(
    listener: (isAuthenticated: boolean) => void
  ): void {
    this.authEventListeners.delete(listener);
  }

  private notifyAuthListeners(isAuthenticated: boolean): void {
    this.authEventListeners.forEach((listener) => {
      try {
        listener(isAuthenticated);
      } catch (error) {
        console.error("Error in auth listener:", error);
      }
    });
  }

  // Role-based API endpoint routing
  private getRoleBasedEndpoint(
    baseEndpoint: string,
    userRole?: string
  ): string {
    if (!userRole) return baseEndpoint;

    const roleEndpoints: Record<string, Record<string, string>> = {
      job_seeker: {
        "/dashboard/": "/dashboard/job-seeker/",
        "/profile/": "/job-seeker-profiles/me/",
        "/applications/": "/applications/job-seeker/",
      },
      recruiter: {
        "/dashboard/": "/dashboard/recruiter/",
        "/profile/": "/recruiter-profiles/me/",
        "/applications/": "/applications/recruiter/",
      },
    };

    return roleEndpoints[userRole]?.[baseEndpoint] || baseEndpoint;
  }

  // Authentication Methods
  async login(
    credentials: LoginCredentials
  ): Promise<AxiosResponse<AuthTokens & { user: User }>> {
    try {
      const response = await this.api.post("/auth/jwt/login/", credentials);
      if (response.data.access && response.data.refresh) {
        this.tokenManager.setTokens(
          response.data.access,
          response.data.refresh
        );
        this.notifyAuthListeners(true);
      }
      return response;
    } catch (error) {
      this.tokenManager.clearTokens();
      throw error;
    }
  }

  async register(
    data: RegisterData
  ): Promise<AxiosResponse<{ user: User; tokens: AuthTokens }>> {
    try {
      const response = await this.api.post("/auth/jwt/register/", data);
      if (response.data.tokens?.access && response.data.tokens?.refresh) {
        this.tokenManager.setTokens(
          response.data.tokens.access,
          response.data.tokens.refresh
        );
        this.notifyAuthListeners(true);
      }
      return response;
    } catch (error) {
      this.tokenManager.clearTokens();
      throw error;
    }
  }

  async refreshToken(
    refresh: string
  ): Promise<AxiosResponse<{ access: string }>> {
    return this.api.post("/auth/jwt/token/refresh/", { refresh });
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = this.tokenManager.getRefreshToken();
      if (refreshToken) {
        await this.api.post("/auth/jwt/logout/", { refresh: refreshToken });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      this.tokenManager.clearTokens();
      this.closeAllWebSockets();
      this.notifyAuthListeners(false);
    }
  }

  // Google OAuth Login
  async googleLogin(
    id_token: string
  ): Promise<AxiosResponse<{ user: User; tokens: AuthTokens }>> {
    try {
      const response = await this.api.post("/auth/google/", { id_token });
      if (response.data.tokens?.access && response.data.tokens?.refresh) {
        this.tokenManager.setTokens(
          response.data.tokens.access,
          response.data.tokens.refresh
        );
        this.notifyAuthListeners(true);
      }
      return response;
    } catch (error) {
      this.tokenManager.clearTokens();
      throw error;
    }
  }

  async requestEmailVerification(email: string): Promise<AxiosResponse> {
    return this.api.post("/auth/request-email-verification/", { email });
  }

  async verifyEmail(token: string): Promise<AxiosResponse> {
    return this.api.post("/auth/verify-email/", { token });
  }

  async requestPasswordReset(email: string): Promise<AxiosResponse> {
    return this.api.post("/auth/request-password-reset/", { email });
  }

  async resetPassword(token: string, password: string): Promise<AxiosResponse> {
    return this.api.post("/auth/reset-password/", { token, password });
  }

  async changePassword(
    oldPassword: string,
    newPassword: string
  ): Promise<AxiosResponse> {
    return this.api.post("/auth/change-password/", {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  // OTP Verification Methods
  async sendOTP(phoneNumber: string, purpose: 'signup' | 'login' | 'password_reset' = 'signup'): Promise<AxiosResponse> {
    return this.api.post("/auth/send-otp/", { 
      phone_number: phoneNumber,
      purpose 
    });
  }

  async verifyOTP(phoneNumber: string, otp: string, purpose: 'signup' | 'login' | 'password_reset' = 'signup'): Promise<AxiosResponse> {
    return this.api.post("/auth/verify-otp/", { 
      phone_number: phoneNumber,
      otp,
      purpose 
    });
  }

  async resendOTP(phoneNumber: string, purpose: 'signup' | 'login' | 'password_reset' = 'signup'): Promise<AxiosResponse> {
    return this.api.post("/auth/resend-otp/", { 
      phone_number: phoneNumber,
      purpose 
    });
  }

  // Enhanced Registration with OTP
  async registerWithOTP(data: RegisterData & { otp: string }): Promise<AxiosResponse<{ user: User; tokens: AuthTokens }>> {
    try {
      const response = await this.api.post("/auth/register-with-otp/", data);
      if (response.data.tokens?.access && response.data.tokens?.refresh) {
        this.tokenManager.setTokens(
          response.data.tokens.access,
          response.data.tokens.refresh
        );
        this.notifyAuthListeners(true);
      }
      return response;
    } catch (error) {
      this.tokenManager.clearTokens();
      throw error;
    }
  }

  // Forgot Password with OTP
  async forgotPasswordWithOTP(phoneNumber: string): Promise<AxiosResponse> {
    return this.api.post("/auth/forgot-password-otp/", { phone_number: phoneNumber });
  }

  async resetPasswordWithOTP(phoneNumber: string, otp: string, newPassword: string): Promise<AxiosResponse> {
    return this.api.post("/auth/reset-password-otp/", { 
      phone_number: phoneNumber,
      otp,
      new_password: newPassword 
    });
  }

  // Email Notification Methods
  async getEmailNotificationSettings(): Promise<AxiosResponse<any>> {
    return this.api.get("/notifications/email-settings/");
  }

  async updateEmailNotificationSettings(settings: {
    interview_reminders?: boolean;
    application_updates?: boolean;
    job_matches?: boolean;
    network_updates?: boolean;
    ai_insights?: boolean;
    weekly_digest?: boolean;
  }): Promise<AxiosResponse<any>> {
    return this.api.patch("/notifications/email-settings/", settings);
  }

  async sendTestEmail(emailType: string): Promise<AxiosResponse> {
    return this.api.post("/notifications/send-test-email/", { email_type: emailType });
  }

  // User Profile Methods
  async getUserProfile(): Promise<AxiosResponse<User>> {
    return this.api.get("/auth/profile/");
  }

  async updateUserProfile(data: Partial<User>): Promise<AxiosResponse<User>> {
    return this.api.patch("/auth/profile/", data);
  }

  async deleteAccount(): Promise<AxiosResponse> {
    return this.api.delete("/auth/delete-account/");
  }

  // Enhanced Job Seeker Profile Methods
  async getJobSeekerProfile(
    id?: string
  ): Promise<AxiosResponse<JobSeekerProfile>> {
    const url = id ? `/job-seeker-profiles/${id}/` : "/job-seeker-profiles/me/";
    return this.api.get(url);
  }

  async createJobSeekerProfile(
    data: Partial<JobSeekerProfile>
  ): Promise<AxiosResponse<JobSeekerProfile>> {
    return this.api.post("/job-seeker-profiles/", data);
  }

  async updateJobSeekerProfile(
    data: Partial<JobSeekerProfile>
  ): Promise<AxiosResponse<JobSeekerProfile>> {
    return this.api.patch("/job-seeker-profiles/me/", data);
  }

  // Skills management
  async addSkill(skillData: Omit<Skill, "id">): Promise<AxiosResponse<Skill>> {
    return this.api.post("/job-seeker-profiles/me/skills/", skillData);
  }

  async updateSkill(
    skillId: string,
    skillData: Partial<Skill>
  ): Promise<AxiosResponse<Skill>> {
    return this.api.patch(
      `/job-seeker-profiles/me/skills/${skillId}/`,
      skillData
    );
  }

  async deleteSkill(skillId: string): Promise<AxiosResponse> {
    return this.api.delete(`/job-seeker-profiles/me/skills/${skillId}/`);
  }

  // Work experience management
  async addWorkExperience(
    experienceData: Omit<WorkExperience, "id">
  ): Promise<AxiosResponse<WorkExperience>> {
    return this.api.post(
      "/job-seeker-profiles/me/work-experience/",
      experienceData
    );
  }

  async updateWorkExperience(
    experienceId: string,
    experienceData: Partial<WorkExperience>
  ): Promise<AxiosResponse<WorkExperience>> {
    return this.api.patch(
      `/job-seeker-profiles/me/work-experience/${experienceId}/`,
      experienceData
    );
  }

  async deleteWorkExperience(experienceId: string): Promise<AxiosResponse> {
    return this.api.delete(
      `/job-seeker-profiles/me/work-experience/${experienceId}/`
    );
  }

  // Education management
  async addEducation(
    educationData: Omit<Education, "id">
  ): Promise<AxiosResponse<Education>> {
    return this.api.post("/job-seeker-profiles/me/education/", educationData);
  }

  async updateEducation(
    educationId: string,
    educationData: Partial<Education>
  ): Promise<AxiosResponse<Education>> {
    return this.api.patch(
      `/job-seeker-profiles/me/education/${educationId}/`,
      educationData
    );
  }

  async deleteEducation(educationId: string): Promise<AxiosResponse> {
    return this.api.delete(`/job-seeker-profiles/me/education/${educationId}/`);
  }

  // Projects management
  async addProject(
    projectData: Omit<Project, "id">
  ): Promise<AxiosResponse<Project>> {
    return this.api.post("/job-seeker-profiles/me/projects/", projectData);
  }

  async updateProject(
    projectId: string,
    projectData: Partial<Project>
  ): Promise<AxiosResponse<Project>> {
    return this.api.patch(
      `/job-seeker-profiles/me/projects/${projectId}/`,
      projectData
    );
  }

  async deleteProject(projectId: string): Promise<AxiosResponse> {
    return this.api.delete(`/job-seeker-profiles/me/projects/${projectId}/`);
  }

  // Certifications management
  async addCertification(
    certificationData: Omit<Certification, "id">
  ): Promise<AxiosResponse<Certification>> {
    return this.api.post(
      "/job-seeker-profiles/me/certifications/",
      certificationData
    );
  }

  async updateCertification(
    certificationId: string,
    certificationData: Partial<Certification>
  ): Promise<AxiosResponse<Certification>> {
    return this.api.patch(
      `/job-seeker-profiles/me/certifications/${certificationId}/`,
      certificationData
    );
  }

  async deleteCertification(certificationId: string): Promise<AxiosResponse> {
    return this.api.delete(
      `/job-seeker-profiles/me/certifications/${certificationId}/`
    );
  }

  // Awards management
  async addAward(awardData: Omit<Award, "id">): Promise<AxiosResponse<Award>> {
    return this.api.post("/job-seeker-profiles/me/awards/", awardData);
  }

  async updateAward(
    awardId: string,
    awardData: Partial<Award>
  ): Promise<AxiosResponse<Award>> {
    return this.api.patch(
      `/job-seeker-profiles/me/awards/${awardId}/`,
      awardData
    );
  }

  async deleteAward(awardId: string): Promise<AxiosResponse> {
    return this.api.delete(`/job-seeker-profiles/me/awards/${awardId}/`);
  }

  // Volunteer experience management
  async addVolunteerExperience(
    volunteerData: Omit<VolunteerExperience, "id">
  ): Promise<AxiosResponse<VolunteerExperience>> {
    return this.api.post(
      "/job-seeker-profiles/me/volunteer-experience/",
      volunteerData
    );
  }

  async updateVolunteerExperience(
    volunteerId: string,
    volunteerData: Partial<VolunteerExperience>
  ): Promise<AxiosResponse<VolunteerExperience>> {
    return this.api.patch(
      `/job-seeker-profiles/me/volunteer-experience/${volunteerId}/`,
      volunteerData
    );
  }

  async deleteVolunteerExperience(volunteerId: string): Promise<AxiosResponse> {
    return this.api.delete(
      `/job-seeker-profiles/me/volunteer-experience/${volunteerId}/`
    );
  }

  // Recruiter Profile Methods
  async getRecruiterProfile(
    id?: string
  ): Promise<AxiosResponse<RecruiterProfile>> {
    const url = id ? `/recruiter-profiles/${id}/` : "/recruiter-profiles/me/";
    return this.api.get(url);
  }

  async createRecruiterProfile(
    data: Partial<RecruiterProfile>
  ): Promise<AxiosResponse<RecruiterProfile>> {
    return this.api.post("/recruiter-profiles/", data);
  }

  async updateRecruiterProfile(
    data: Partial<RecruiterProfile>
  ): Promise<AxiosResponse<RecruiterProfile>> {
    return this.api.patch("/recruiter-profiles/me/", data);
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
  }): Promise<
    AxiosResponse<{
      results: JobPost[];
      count: number;
      next?: string;
      previous?: string;
    }>
  > {
    return this.api.get("/job-posts/", { params });
  }

  async getJobPost(id: string): Promise<AxiosResponse<JobPost>> {
    return this.api.get(`/job-posts/${id}/`);
  }

  async createJobPost(
    data: Omit<JobPost, "id" | "recruiter" | "created_at" | "views_count">
  ): Promise<AxiosResponse<JobPost>> {
    return this.api.post("/job-posts/", data);
  }

  async updateJobPost(
    id: string,
    data: Partial<JobPost>
  ): Promise<AxiosResponse<JobPost>> {
    return this.api.patch(`/job-posts/${id}/`, data);
  }

  async deleteJobPost(id: string): Promise<AxiosResponse> {
    return this.api.delete(`/job-posts/${id}/`);
  }

  // Resume Methods
  async getResumes(): Promise<AxiosResponse<Resume[]>> {
    return this.api.get("/resumes/");
  }

  async getResume(id: string): Promise<AxiosResponse<Resume>> {
    return this.api.get(`/resumes/${id}/`);
  }

  async uploadResume(formData: FormData): Promise<AxiosResponse<Resume>> {
    return this.api.post("/files/upload-resume/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  }

  async deleteResume(id: string): Promise<AxiosResponse> {
    return this.api.delete(`/resumes/${id}/`);
  }

  async parseResume(resumeId: string): Promise<
    AxiosResponse<{
      parsed_text: string;
      key_skills: string[];
      summary: string;
    }>
  > {
    return this.api.post(`/parse-resume/${resumeId}/`);
  }

  async parseResumeAsync(
    resumeId: string
  ): Promise<AxiosResponse<{ task_id: string }>> {
    return this.api.post("/parse-resume-async/", { resume_id: resumeId });
  }

  // Application Methods
  async getApplications(params?: {
    status?: string;
    job_post?: string;
    page?: number;
  }): Promise<AxiosResponse<{ results: Application[]; count: number }>> {
    return this.api.get("/applications/", { params });
  }

  async getApplication(id: string): Promise<AxiosResponse<Application>> {
    return this.api.get(`/applications/${id}/`);
  }

  async createApplication(data: {
    job_post: string;
    resume: string;
    cover_letter?: string;
  }): Promise<AxiosResponse<Application>> {
    return this.api.post("/applications/", data);
  }

  async updateApplicationStatus(
    id: string,
    status: Application["status"],
    notes?: string
  ): Promise<AxiosResponse<Application>> {
    return this.api.patch(`/applications/${id}/`, {
      status,
      recruiter_notes: notes,
    });
  }

  // Match Score Methods
  async calculateMatchScore(
    resumeId: string,
    jobId: string
  ): Promise<AxiosResponse<MatchScore>> {
    return this.api.post("/calculate-match-score/", {
      resume_id: resumeId,
      job_id: jobId,
    });
  }

  async getMatchScoresForResume(
    resumeId: string
  ): Promise<AxiosResponse<MatchScore[]>> {
    return this.api.get(`/match-scores/resume/${resumeId}/`);
  }

  async getMatchScoresForJob(
    jobId: string
  ): Promise<AxiosResponse<MatchScore[]>> {
    return this.api.get(`/match-scores/job/${jobId}/`);
  }

  // Interview Session Methods
  async getInterviewSessions(): Promise<AxiosResponse<InterviewSession[]>> {
    return this.api.get("/interview-sessions/");
  }

  async createInterviewSession(data: {
    application: string;
    session_type: string;
    scheduled_at?: string;
    duration_minutes?: number;
  }): Promise<AxiosResponse<InterviewSession>> {
    return this.api.post("/interview-sessions/", data);
  }

  async updateInterviewSession(
    id: string,
    data: Partial<InterviewSession>
  ): Promise<AxiosResponse<InterviewSession>> {
    return this.api.patch(`/interview-sessions/${id}/`, data);
  }

  // AI Interview Methods
  async startAIInterview(data: {
    resume_source: "profile" | "upload";
    interview_type: string;
    difficulty: string;
    duration: number;
    focus_areas?: string[];
    resume_file?: File;
  }): Promise<AxiosResponse<{ session_id: string; questions: string[] }>> {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (key === "resume_file" && value instanceof File) {
        formData.append(key, value);
      } else if (key === "focus_areas" && Array.isArray(value)) {
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, value.toString());
      }
    });

    return this.api.post("/interview-sessions/ai-start/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  }

  async submitAIInterviewResponse(
    sessionId: string,
    questionIndex: number,
    response: {
      text?: string;
      audio_file?: File;
      video_file?: File;
    }
  ): Promise<AxiosResponse<{ feedback: any; next_question?: string }>> {
    const formData = new FormData();
    formData.append("question_index", questionIndex.toString());

    if (response.text) formData.append("text", response.text);
    if (response.audio_file) formData.append("audio_file", response.audio_file);
    if (response.video_file) formData.append("video_file", response.video_file);

    return this.api.post(
      `/interview-sessions/${sessionId}/ai-response/`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
  }

  async endAIInterview(
    sessionId: string
  ): Promise<
    AxiosResponse<{ analysis: any; score: number; recommendations: string[] }>
  > {
    return this.api.post(`/interview-sessions/${sessionId}/ai-end/`);
  }

  // Recommendations Methods
  async getJobRecommendations(params?: {
    limit?: number;
    min_score?: number;
  }): Promise<AxiosResponse<{ jobs: JobPost[]; scores: MatchScore[] }>> {
    return this.api.get("/recommendations/jobs/", { params });
  }

  async getCandidateRecommendations(
    jobId: string,
    params?: {
      limit?: number;
      min_score?: number;
    }
  ): Promise<
    AxiosResponse<{ candidates: JobSeekerProfile[]; scores: MatchScore[] }>
  > {
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
  }): Promise<
    AxiosResponse<{ results: JobPost[]; count: number; facets: any }>
  > {
    return this.api.get("/search/jobs/", { params });
  }

  async searchCandidates(params: {
    q?: string;
    location?: string;
    skills?: string[];
    experience_level?: string;
    sort_by?: string;
    page?: number;
  }): Promise<
    AxiosResponse<{ results: JobSeekerProfile[]; count: number; facets: any }>
  > {
    return this.api.get("/search/candidates/", { params });
  }

  // Dashboard Methods
  async getDashboardStats(): Promise<
    AxiosResponse<{
      profile_views: number;
      applications_sent: number;
      interview_invites: number;
      job_matches: number;
      recent_activities: any[];
    }>
  > {
    return this.api.get("/dashboard/stats/");
  }

  async getPersonalizedDashboard(): Promise<
    AxiosResponse<{
      recommended_jobs: JobPost[];
      trending_skills: string[];
      network_updates: any[];
      ai_insights: any[];
    }>
  > {
    return this.api.get("/dashboard/personalized/");
  }

  // Task Management Methods
  async getTaskStatus(taskId: string): Promise<
    AxiosResponse<{
      status: string;
      result?: any;
      error?: string;
      progress?: number;
    }>
  > {
    return this.api.get(`/tasks/status/${taskId}/`);
  }

  async cancelTask(taskId: string): Promise<AxiosResponse> {
    return this.api.post(`/tasks/cancel/${taskId}/`);
  }

  // Enhanced File Management Methods
  async uploadFile(
    file: File,
    fileType: string
  ): Promise<AxiosResponse<{ file_id: string; url: string }>> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("file_type", fileType);

    return this.api.post("/files/upload/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  }

  // Profile picture upload for users
  async uploadProfilePicture(
    file: File
  ): Promise<AxiosResponse<{ url: string; file_id: string }>> {
    const formData = new FormData();
    formData.append("profile_picture", file);

    return this.api.post("/auth/profile/upload-picture/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  }

  // Company logo upload for recruiters
  async uploadCompanyLogo(
    file: File
  ): Promise<AxiosResponse<{ url: string; file_id: string }>> {
    const formData = new FormData();
    formData.append("company_logo", file);

    return this.api.post("/recruiter-profiles/me/upload-logo/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  }

  // Generic file upload with progress tracking
  async uploadFileWithProgress(
    file: File,
    fileType: string,
    onProgress?: (progress: number) => void
  ): Promise<AxiosResponse<{ file_id: string; url: string }>> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("file_type", fileType);

    return this.api.post("/files/upload/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });
  }

  async deleteFile(fileId: string): Promise<AxiosResponse> {
    return this.api.delete(`/files/delete/${fileId}/`);
  }

  async getUserFiles(): Promise<AxiosResponse<any[]>> {
    return this.api.get("/files/list/");
  }

  // Enhanced WebSocket Methods with Authentication and Reconnection
  connectWebSocket(
    endpoint: string,
    options: {
      onMessage?: (data: any) => void;
      onError?: (error: Event) => void;
      onClose?: () => void;
      maxReconnectAttempts?: number;
      reconnectInterval?: number;
    } = {}
  ): WebSocket | null {
    const {
      onMessage,
      onError,
      onClose,
      maxReconnectAttempts = 5,
      reconnectInterval = 3000,
    } = options;

    // Check if connection already exists
    if (this.wsConnections.has(endpoint)) {
      console.warn(
        `WebSocket connection already exists for endpoint: ${endpoint}`
      );
      return this.wsConnections.get(endpoint)?.ws || null;
    }

    try {
      const token = this.tokenManager.getAccessToken();
      if (!token || this.tokenManager.isTokenExpired(token)) {
        console.error(
          "Cannot connect WebSocket: No valid authentication token"
        );
        return null;
      }

      const wsUrl = `${WS_BASE_URL}/${endpoint}/?token=${token}`;
      const ws = new WebSocket(wsUrl);

      const connection: WebSocketConnection = {
        ws,
        endpoint,
        reconnectAttempts: 0,
        maxReconnectAttempts,
        reconnectInterval,
        onMessage,
        onError,
        onClose,
      };

      ws.onopen = () => {
        console.log(`WebSocket connected: ${endpoint}`);
        connection.reconnectAttempts = 0; // Reset reconnect attempts on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) {
            onMessage(data);
          }
        } catch (error) {
          console.error(
            `Error parsing WebSocket message for ${endpoint}:`,
            error
          );
        }
      };

      ws.onerror = (error) => {
        console.warn(
          `WebSocket connection failed for ${endpoint}. Will use polling fallback.`
        );
        if (onError) {
          onError(error);
        }
        // Set up polling fallback on connection error
        this.setupPollingFallback(endpoint, onMessage);
      };

      ws.onclose = (event) => {
        console.log(
          `WebSocket disconnected: ${endpoint}, code: ${event.code}, reason: ${event.reason}`
        );
        this.wsConnections.delete(endpoint);

        if (onClose) {
          onClose();
        }

        // Attempt reconnection if not a normal closure and we haven't exceeded max attempts
        if (
          event.code !== 1000 &&
          connection.reconnectAttempts < connection.maxReconnectAttempts
        ) {
          this.scheduleWebSocketReconnect(connection);
        }
      };

      this.wsConnections.set(endpoint, connection);
      return ws;
    } catch (error) {
      console.error(`Failed to connect WebSocket ${endpoint}:`, error);
      return null;
    }
  }

  private scheduleWebSocketReconnect(connection: WebSocketConnection): void {
    connection.reconnectAttempts++;
    console.log(
      `Scheduling WebSocket reconnect for ${connection.endpoint}, attempt ${connection.reconnectAttempts}/${connection.maxReconnectAttempts}`
    );

    setTimeout(() => {
      if (connection.reconnectAttempts <= connection.maxReconnectAttempts) {
        console.log(
          `Attempting to reconnect WebSocket: ${connection.endpoint}`
        );
        this.connectWebSocket(connection.endpoint, {
          onMessage: connection.onMessage,
          onError: connection.onError,
          onClose: connection.onClose,
          maxReconnectAttempts: connection.maxReconnectAttempts,
          reconnectInterval: connection.reconnectInterval,
        });
      }
    }, connection.reconnectInterval);
  }

  disconnectWebSocket(endpoint: string): void {
    const connection = this.wsConnections.get(endpoint);
    if (connection) {
      // Set max attempts to 0 to prevent reconnection
      connection.maxReconnectAttempts = 0;
      connection.ws.close(1000, "Manual disconnect");
      this.wsConnections.delete(endpoint);
    }
  }

  closeAllWebSockets(): void {
    this.wsConnections.forEach((connection, endpoint) => {
      connection.maxReconnectAttempts = 0; // Prevent reconnection
      connection.ws.close(1000, "Closing all connections");
    });
    this.wsConnections.clear();

    // Clear all polling intervals
    this.pollingIntervals.forEach((interval) => {
      clearInterval(interval);
    });
    this.pollingIntervals.clear();
  }

  // Polling fallback methods
  private setupPollingFallback(
    endpoint: string,
    onMessage?: (data: any) => void
  ): void {
    // Clear existing polling for this endpoint
    this.clearPollingFallback(endpoint);

    if (!onMessage) return;

    console.log(`Setting up polling fallback for ${endpoint}`);

    const pollFunction = async () => {
      try {
        let data = null;

        // Different polling endpoints based on WebSocket endpoint
        switch (endpoint) {
          case "notifications":
            const notifResponse = await this.getNotifications();
            data = {
              type: "notifications_update",
              notifications: notifResponse.data.results || [],
            };
            break;

          case "dashboard":
            const statsResponse = await this.getDashboardStats();
            data = {
              type: "stats_update",
              stats: statsResponse.data,
            };
            break;

          default:
            // Generic polling - just return empty data
            data = { type: "polling_update", endpoint };
        }

        if (data && onMessage) {
          onMessage(data);
        }
      } catch (error) {
        console.warn(`Polling failed for ${endpoint}:`, error);
      }
    };

    // Initial poll
    pollFunction();

    // Set up interval polling (every 30 seconds to avoid overwhelming the server)
    const interval = setInterval(pollFunction, 30000);
    this.pollingIntervals.set(endpoint, interval);
  }

  private clearPollingFallback(endpoint: string): void {
    const interval = this.pollingIntervals.get(endpoint);
    if (interval) {
      clearInterval(interval);
      this.pollingIntervals.delete(endpoint);
    }
  }

  // Get WebSocket connection status
  getWebSocketStatus(
    endpoint: string
  ): "connecting" | "open" | "closing" | "closed" | "not_found" {
    const connection = this.wsConnections.get(endpoint);
    if (!connection) return "not_found";

    switch (connection.ws.readyState) {
      case WebSocket.CONNECTING:
        return "connecting";
      case WebSocket.OPEN:
        return "open";
      case WebSocket.CLOSING:
        return "closing";
      case WebSocket.CLOSED:
        return "closed";
      default:
        return "not_found";
    }
  }

  // Send message through WebSocket
  sendWebSocketMessage(endpoint: string, message: any): boolean {
    const connection = this.wsConnections.get(endpoint);
    if (!connection || connection.ws.readyState !== WebSocket.OPEN) {
      console.error(
        `Cannot send message: WebSocket ${endpoint} is not connected`
      );
      return false;
    }

    try {
      connection.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error(`Error sending WebSocket message to ${endpoint}:`, error);
      return false;
    }
  }

  // Notification Methods
  async getNotifications(params?: {
    is_read?: boolean;
    notification_type?: string;
    page?: number;
  }): Promise<AxiosResponse<{ results: Notification[]; count: number }>> {
    return this.api.get("/notifications/", { params });
  }

  async markNotificationAsRead(
    id: string
  ): Promise<AxiosResponse<Notification>> {
    return this.api.patch(`/notifications/${id}/`, { is_read: true });
  }

  async markAllNotificationsAsRead(): Promise<AxiosResponse> {
    return this.api.post("/notifications/mark-all-read/");
  }

  // Network/Connection Methods
  async getConnections(): Promise<AxiosResponse<any>> {
    return this.api.get("/connections/");
  }

  async getSuggestedConnections(): Promise<AxiosResponse<any>> {
    return this.api.get("/connections/suggestions/");
  }

  async sendConnectionRequest(userId: string): Promise<AxiosResponse<any>> {
    return this.api.post("/connections/request/", { user_id: userId });
  }

  async acceptConnectionRequest(requestId: string): Promise<AxiosResponse<any>> {
    return this.api.post(`/connections/accept/${requestId}/`);
  }

  async rejectConnectionRequest(requestId: string): Promise<AxiosResponse<any>> {
    return this.api.post(`/connections/reject/${requestId}/`);
  }

  async removeConnection(connectionId: string): Promise<AxiosResponse<any>> {
    return this.api.delete(`/connections/${connectionId}/`);
  }

  async getNetworkActivity(): Promise<AxiosResponse<any>> {
    return this.api.get("/network/activity/");
  }

  async searchProfessionals(query: string, filters?: any): Promise<AxiosResponse<any>> {
    const params = new URLSearchParams({ q: query });
    if (filters) {
      Object.keys(filters).forEach(key => {
        if (filters[key]) params.append(key, filters[key]);
      });
    }
    return this.api.get(`/professionals/search/?${params.toString()}`);
  }

  // Messages/Chat Methods
  async getConversations(): Promise<AxiosResponse<any>> {
    return this.api.get("/messages/conversations/");
  }

  async getMessages(conversationId: string): Promise<AxiosResponse<any>> {
    return this.api.get(`/messages/conversations/${conversationId}/messages/`);
  }

  async sendMessage(conversationId: string, content: string, messageType: string = 'text'): Promise<AxiosResponse<any>> {
    return this.api.post(`/messages/conversations/${conversationId}/messages/`, {
      content,
      message_type: messageType
    });
  }

  async markMessageAsRead(messageId: string): Promise<AxiosResponse<any>> {
    return this.api.patch(`/messages/${messageId}/`, { is_read: true });
  }

  async createConversation(participantId: string): Promise<AxiosResponse<any>> {
    return this.api.post("/messages/conversations/", { participant_id: participantId });
  }

  // Utility Methods
  isAuthenticated(): boolean {
    const token = this.tokenManager.getAccessToken();
    return !!token && !this.tokenManager.isTokenExpired(token);
  }

  getAuthToken(): string | null {
    return this.tokenManager.getAccessToken();
  }

  // Get current user role from token
  getCurrentUserRole(): "job_seeker" | "recruiter" | "admin" | null {
    const token = this.tokenManager.getAccessToken();
    if (!token || this.tokenManager.isTokenExpired(token)) {
      return null;
    }

    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.user_type || null;
    } catch {
      return null;
    }
  }

  // Get current user ID from token
  getCurrentUserId(): string | null {
    const token = this.tokenManager.getAccessToken();
    if (!token || this.tokenManager.isTokenExpired(token)) {
      return null;
    }

    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.user_id || payload.sub || null;
    } catch {
      return null;
    }
  }

  // Health Check
  async healthCheck(): Promise<AxiosResponse> {
    return this.api.get("/health/");
  }
}

// Create and export a singleton instance
export const apiService = new APIService();
export default apiService;
