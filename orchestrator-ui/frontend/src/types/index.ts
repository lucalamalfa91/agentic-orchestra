/**
 * TypeScript type definitions for Orchestrator UI.
 */

export interface TechStack {
  frontend: string;
  backend: string;
  database: string;
  deploy_platform: string;
}

export interface GenerationRequest {
  mvp_description: string;
  features: string[];
  user_stories?: string[];
  tech_stack: TechStack;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  github_repo_url?: string;
  status: string;
  created_at: string;
  generation_attempt: number;
}

export interface ProjectRequirement {
  id: number;
  project_id: number;
  mvp_description: string;
  features: string; // JSON string
  user_stories?: string; // JSON string
  frontend_framework?: string;
  backend_framework?: string;
  database_type?: string;
  deploy_platform?: string;
  requirements_text: string;
}

export interface ProjectWithRequirements extends Project {
  requirements?: ProjectRequirement;
}

export interface PaginatedProjects {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GenerationLog {
  id: number;
  project_id?: number;
  step_name?: string;
  status: string;
  message?: string;
  created_at: string;
  generation_attempt: number;
}

export interface GenerationStatus {
  generation_id: string;
  project_id?: number;
  status: string;
  current_step?: string;
  percentage: number;
  message?: string;
}

export interface GenerationStartResponse {
  generation_id: string;
  message: string;
  websocket_url: string;
}

export interface ProgressMessage {
  type: 'progress';
  step: string;
  step_number: number;
  percentage: number;
  message: string;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

// Form state
export interface FormData {
  mvp_description: string;
  features: string; // Newline-separated features
  user_stories: string; // Newline-separated user stories
  frontend: string;
  backend: string;
  database: string;
  deploy_platform: string;
}

// Auth types
export interface User {
  id: number;
  github_username: string;
  github_id: string;
}

export interface AIProviderConfig {
  base_url: string;
  api_key_set: boolean;
}

// Design state types (for human-in-the-loop approval)
export interface EntityField {
  name: string;
  type: string;
  required?: boolean;
  description?: string;
}

export interface Entity {
  name: string;
  fields: EntityField[];
  description?: string;
}

export interface APIEndpoint {
  method: string;
  path: string;
  description: string;
  entity?: string;
}

export interface DesignYaml {
  app_name?: string;
  description?: string;
  stack?: {
    frontend?: string;
    backend?: string;
    database?: string;
    deploy_platform?: string;
  };
  entities?: Entity[];
  api_endpoints?: APIEndpoint[];
  [key: string]: any; // Allow additional properties
}

export interface DesignStateResponse {
  project_id: string;
  current_step: string;
  design_yaml?: DesignYaml | null;
  api_schema?: any;
  db_schema?: any;
  errors: Record<string, string>;
  agent_statuses: Record<string, string>;
  completed_steps: string[];
}

export interface DesignApprovalRequest {
  design_changes?: Record<string, any>;
}

// Knowledge Sources types
export type KnowledgeSourceType = 'web' | 'file' | 'api';

export interface KnowledgeSource {
  id: string;
  user_id: number;
  name: string;
  source_type: KnowledgeSourceType;
  last_indexed_at: string | null;
  created_at: string;
}

export interface KnowledgeSourceCreate {
  name: string;
  source_type: KnowledgeSourceType;
  config: Record<string, any>;
}

export interface IndexingStatusResponse {
  status: 'idle' | 'indexing' | 'completed' | 'failed';
  message?: string;
}
