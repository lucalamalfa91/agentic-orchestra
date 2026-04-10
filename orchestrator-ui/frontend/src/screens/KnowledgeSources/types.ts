/**
 * TypeScript types for Knowledge Sources management.
 */

export type KnowledgeSourceType = 'web' | 'file' | 'api';

export interface KnowledgeSource {
  id: string;
  user_id: number;
  name: string;
  source_type: KnowledgeSourceType;
  last_indexed_at: string | null;
  created_at: string;
}

export interface WebSourceConfig {
  url: string;
  crawl_depth?: number;
  max_pages?: number;
  selectors?: string;
}

export interface FileSourceConfig {
  file_names: string[];
}

export interface ApiSourceConfig {
  endpoint_url: string;
  auth_header?: string;
  auth_value?: string;
}

export type SourceConfig = WebSourceConfig | FileSourceConfig | ApiSourceConfig;

export interface KnowledgeSourceCreate {
  name: string;
  source_type: KnowledgeSourceType;
  config: SourceConfig;
}

export interface IndexingStatus {
  status: 'idle' | 'indexing' | 'completed' | 'failed';
  message?: string;
}
