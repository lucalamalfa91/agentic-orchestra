/**
 * API client for communicating with backend.
 */
import axios from 'axios';
import type {
  GenerationRequest,
  GenerationStartResponse,
  PaginatedProjects,
  ProjectWithRequirements,
  ProjectRequirement,
  GenerationLog
} from '../types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
  timeout: 10000,
});

// Add request interceptor for JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message,
      code: error.code,
    });
    return Promise.reject(error);
  }
);

export const projectsApi = {
  /**
   * Get paginated list of projects.
   */
  async getProjects(page = 1, pageSize = 20): Promise<PaginatedProjects> {
    const response = await api.get<PaginatedProjects>('/api/projects/', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Get project by ID with requirements.
   */
  async getProject(projectId: number): Promise<ProjectWithRequirements> {
    const response = await api.get<ProjectWithRequirements>(`/api/projects/${projectId}`);
    return response.data;
  },

  /**
   * Get project requirements for regeneration.
   */
  async getProjectRequirements(projectId: number): Promise<ProjectRequirement> {
    const response = await api.get<ProjectRequirement>(`/api/projects/${projectId}/requirements`);
    return response.data;
  },

  /**
   * Get project logs.
   */
  async getProjectLogs(projectId: number): Promise<GenerationLog[]> {
    const response = await api.get<GenerationLog[]>(`/api/projects/${projectId}/logs`);
    return response.data;
  },

  /**
   * Update project status.
   */
  async updateProjectStatus(
    projectId: string | number,
    status: 'pending' | 'in_progress' | 'completed' | 'failed'
  ): Promise<any> {
    const response = await api.patch(`/api/projects/${projectId}/status`, {
      status,
    });
    return response.data;
  },
};

export const generationApi = {
  /**
   * Start a new app generation.
   */
  async startGeneration(request: GenerationRequest): Promise<GenerationStartResponse> {
    const response = await api.post<GenerationStartResponse>('/api/generation/start', request);
    return response.data;
  },
};

export const authApi = {
  /**
   * Get GitHub OAuth login URL.
   */
  async getGitHubAuthUrl(): Promise<{ auth_url: string }> {
    const response = await api.get<{ auth_url: string }>('/api/auth/github/login');
    return response.data;
  },
};

export const configApi = {
  /**
   * Save AI provider configuration.
   */
  async saveAIProvider(baseUrl: string, apiKey: string): Promise<{ message: string; is_configured: boolean }> {
    const response = await api.post('/api/config/ai-provider', {
      base_url: baseUrl,
      api_key: apiKey,
    });
    return response.data;
  },

  /**
   * Test AI provider connection.
   */
  async testAIProvider(baseUrl: string, apiKey: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/api/config/ai-provider/test', {
      base_url: baseUrl,
      api_key: apiKey,
    });
    return response.data;
  },

  /**
   * Get current AI provider configuration.
   */
  async getAIProviderConfig(): Promise<{ is_configured: boolean; base_url?: string }> {
    const response = await api.get('/api/config/ai-provider');
    return response.data;
  },
};

export { API_BASE_URL };
