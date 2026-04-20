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
  GenerationLog,
  DesignStateResponse,
  DesignApprovalRequest,
  KnowledgeSource,
  KnowledgeSourceCreate,
  IndexingStatusResponse
} from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

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

    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      // Clear invalid token
      localStorage.removeItem('jwt_token');

      // Only redirect if not already on auth page
      if (!window.location.pathname.startsWith('/auth')) {
        // Store intended destination for redirect after login
        sessionStorage.setItem('auth_redirect', window.location.pathname);

        // Redirect to auth page
        window.location.href = '/auth?session_expired=true';
      }
    }

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

  /**
   * Resume a failed generation with same requirements.
   */
  async resumeGeneration(projectId: number): Promise<GenerationStartResponse> {
    const response = await api.post<GenerationStartResponse>(
      `/api/projects/${projectId}/resume`
    );
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

export const generationControlApi = {
  /**
   * Get current design state from checkpoint (for review).
   */
  async getDesignState(projectId: string): Promise<DesignStateResponse> {
    const response = await api.get<DesignStateResponse>(`/api/generation/${projectId}/state`);
    return response.data;
  },

  /**
   * Approve design with optional modifications and resume execution.
   */
  async approveDesign(projectId: string, designChanges?: Record<string, any>): Promise<{ message: string }> {
    const body: DesignApprovalRequest = designChanges ? { design_changes: designChanges } : {};
    const response = await api.post(`/api/generation/${projectId}/approve`, body);
    return response.data;
  },

  /**
   * Reject design and cancel generation.
   */
  async rejectDesign(projectId: string): Promise<{ message: string }> {
    const response = await api.post(`/api/generation/${projectId}/reject`);
    return response.data;
  },

  /**
   * Cancel an in-progress generation.
   */
  async cancelGeneration(projectId: string): Promise<{ message: string }> {
    const response = await api.post(`/api/generation/${projectId}/cancel`);
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

export const knowledgeApi = {
  /**
   * Get all knowledge sources for current user.
   */
  async getSources(): Promise<KnowledgeSource[]> {
    const response = await api.get<KnowledgeSource[]>('/api/knowledge/sources');
    return response.data;
  },

  /**
   * Create a new knowledge source.
   */
  async createSource(data: KnowledgeSourceCreate): Promise<KnowledgeSource> {
    const response = await api.post<KnowledgeSource>('/api/knowledge/sources', data);
    return response.data;
  },

  /**
   * Delete a knowledge source.
   */
  async deleteSource(sourceId: string): Promise<{ message: string }> {
    const response = await api.delete(`/api/knowledge/sources/${sourceId}`);
    return response.data;
  },

  /**
   * Trigger re-indexing of a knowledge source.
   */
  async indexSource(sourceId: string): Promise<{ message: string }> {
    const response = await api.post(`/api/knowledge/index/${sourceId}`);
    return response.data;
  },

  /**
   * Get indexing status for a knowledge source.
   */
  async getIndexingStatus(sourceId: string): Promise<IndexingStatusResponse> {
    const response = await api.get<IndexingStatusResponse>(`/api/knowledge/index/${sourceId}/status`);
    return response.data;
  },
};

export { API_BASE_URL };
