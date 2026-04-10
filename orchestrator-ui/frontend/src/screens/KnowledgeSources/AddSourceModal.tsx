/**
 * Modal for adding a new knowledge source.
 */
import React, { useState } from 'react';
import type { KnowledgeSourceType, WebSourceConfig, FileSourceConfig, ApiSourceConfig } from './types';

interface AddSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (name: string, type: KnowledgeSourceType, config: any, andIndex: boolean) => void;
  isLoading: boolean;
}

const AddSourceModal: React.FC<AddSourceModalProps> = ({ isOpen, onClose, onAdd, isLoading }) => {
  const [sourceType, setSourceType] = useState<KnowledgeSourceType>('web');
  const [name, setName] = useState('');

  // Web config
  const [webUrl, setWebUrl] = useState('');
  const [crawlDepth, setCrawlDepth] = useState(2);
  const [maxPages, setMaxPages] = useState(10);
  const [selectors, setSelectors] = useState('');

  // File config
  const [files, setFiles] = useState<File[]>([]);

  // API config
  const [apiEndpoint, setApiEndpoint] = useState('');
  const [authHeader, setAuthHeader] = useState('');
  const [authValue, setAuthValue] = useState('');

  if (!isOpen) return null;

  const resetForm = () => {
    setName('');
    setSourceType('web');
    setWebUrl('');
    setCrawlDepth(2);
    setMaxPages(10);
    setSelectors('');
    setFiles([]);
    setApiEndpoint('');
    setAuthHeader('');
    setAuthValue('');
  };

  const handleSubmit = (andIndex: boolean) => {
    let config: any = {};

    if (sourceType === 'web') {
      const webConfig: WebSourceConfig = {
        url: webUrl,
        crawl_depth: crawlDepth,
        max_pages: maxPages,
      };
      if (selectors.trim()) {
        webConfig.selectors = selectors.trim();
      }
      config = webConfig;
    } else if (sourceType === 'file') {
      const fileConfig: FileSourceConfig = {
        file_names: files.map((f) => f.name),
      };
      config = fileConfig;
      // TODO: In production, upload files to backend here
    } else if (sourceType === 'api') {
      const apiConfig: ApiSourceConfig = {
        endpoint_url: apiEndpoint,
      };
      if (authHeader.trim()) {
        apiConfig.auth_header = authHeader.trim();
      }
      if (authValue.trim()) {
        apiConfig.auth_value = authValue.trim();
      }
      config = apiConfig;
    }

    onAdd(name, sourceType, config, andIndex);
    resetForm();
  };

  const isFormValid = () => {
    if (!name.trim()) return false;
    if (sourceType === 'web' && !webUrl.trim()) return false;
    if (sourceType === 'file' && files.length === 0) return false;
    if (sourceType === 'api' && !apiEndpoint.trim()) return false;
    return true;
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{
        background: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(10px)',
      }}
      onClick={onClose}
    >
      <div
        className="glass-card p-8 space-y-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        style={{
          background: 'rgba(30, 25, 50, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2
          className="text-2xl font-bold"
          style={{
            fontFamily: 'var(--font-heading)',
            background: 'var(--gradient-primary)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Add Knowledge Source
        </h2>

        {/* Source Name */}
        <div className="space-y-2">
          <label
            className="block text-sm font-semibold"
            style={{ color: 'var(--color-text)' }}
          >
            Source Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Company Documentation"
            className="w-full px-4 py-3 rounded-lg focus-ring"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: 'var(--color-text)',
              fontSize: 'var(--font-size-base)',
              transition: 'var(--transition-default)',
            }}
          />
        </div>

        {/* Source Type Selector */}
        <div className="space-y-2">
          <label
            className="block text-sm font-semibold"
            style={{ color: 'var(--color-text)' }}
          >
            Source Type
          </label>
          <div className="grid grid-cols-3 gap-3">
            {(['web', 'file', 'api'] as KnowledgeSourceType[]).map((type) => (
              <button
                key={type}
                onClick={() => setSourceType(type)}
                className="px-4 py-3 rounded-lg text-sm font-semibold focus-ring"
                style={{
                  background: sourceType === type ? 'var(--gradient-primary)' : 'var(--color-glass)',
                  border: `1px solid ${sourceType === type ? 'rgba(102, 126, 234, 0.5)' : 'var(--color-glass-border)'}`,
                  color: 'var(--color-text)',
                  transition: 'var(--transition-default)',
                  cursor: 'pointer',
                }}
              >
                {type === 'web' && 'Web URL'}
                {type === 'file' && 'Local Files'}
                {type === 'api' && 'API Endpoint'}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Form Based on Type */}
        {sourceType === 'web' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label
                className="block text-sm font-semibold"
                style={{ color: 'var(--color-text)' }}
              >
                URL
              </label>
              <input
                type="url"
                value={webUrl}
                onChange={(e) => setWebUrl(e.target.value)}
                placeholder="https://docs.example.com"
                className="w-full px-4 py-3 rounded-lg focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: 'var(--color-text)',
                  fontSize: 'var(--font-size-base)',
                }}
              />
            </div>

            <div className="space-y-2">
              <label
                className="block text-sm font-semibold"
                style={{ color: 'var(--color-text)' }}
              >
                Crawl Depth: {crawlDepth}
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={crawlDepth}
                onChange={(e) => setCrawlDepth(Number(e.target.value))}
                className="w-full"
                style={{
                  accentColor: 'var(--color-primary)',
                }}
              />
              <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                How many levels of links to follow (1-5)
              </p>
            </div>

            <div className="space-y-2">
              <label
                className="block text-sm font-semibold"
                style={{ color: 'var(--color-text)' }}
              >
                Max Pages
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={maxPages}
                onChange={(e) => setMaxPages(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-lg focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: 'var(--color-text)',
                  fontSize: 'var(--font-size-base)',
                }}
              />
            </div>

            <div className="space-y-2">
              <label
                className="block text-sm font-semibold"
                style={{ color: 'var(--color-text)' }}
              >
                CSS Selector (optional)
              </label>
              <input
                type="text"
                value={selectors}
                onChange={(e) => setSelectors(e.target.value)}
                placeholder="e.g., article.main-content"
                className="w-full px-4 py-3 rounded-lg focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: 'var(--color-text)',
                  fontSize: 'var(--font-size-base)',
                }}
              />
              <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                Leave empty to extract all content
              </p>
            </div>
          </div>
        )}

        {sourceType === 'file' && (
          <div className="space-y-4">
            <div
              className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer"
              style={{
                borderColor: 'rgba(255, 255, 255, 0.2)',
                background: 'rgba(255, 255, 255, 0.02)',
                transition: 'var(--transition-default)',
              }}
              onDragOver={(e) => {
                e.preventDefault();
                e.currentTarget.style.borderColor = 'var(--color-primary)';
                e.currentTarget.style.background = 'rgba(102, 126, 234, 0.1)';
              }}
              onDragLeave={(e) => {
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
              }}
              onDrop={(e) => {
                e.preventDefault();
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                const droppedFiles = Array.from(e.dataTransfer.files);
                setFiles((prev) => [...prev, ...droppedFiles]);
              }}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <svg
                className="mx-auto h-12 w-12 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p style={{ color: 'var(--color-text)' }}>
                Drag and drop files here, or click to select
              </p>
              <p className="text-xs mt-2" style={{ color: 'var(--color-text-tertiary)' }}>
                Supported: .pdf, .md, .txt, .docx
              </p>
              <input
                id="file-input"
                type="file"
                multiple
                accept=".pdf,.md,.txt,.docx"
                onChange={(e) => {
                  if (e.target.files) {
                    const selectedFiles = Array.from(e.target.files);
                    setFiles((prev) => [...prev, ...selectedFiles]);
                  }
                }}
                style={{ display: 'none' }}
              />
            </div>

            {files.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>
                  Selected Files ({files.length})
                </p>
                <div className="space-y-2">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between px-4 py-2 rounded-lg"
                      style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }}
                    >
                      <span className="text-sm truncate" style={{ color: 'var(--color-text)' }}>
                        {file.name}
                      </span>
                      <button
                        onClick={() => setFiles((prev) => prev.filter((_, i) => i !== index))}
                        className="ml-2 text-xs"
                        style={{ color: 'var(--color-error)' }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {sourceType === 'api' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label
                className="block text-sm font-semibold"
                style={{ color: 'var(--color-text)' }}
              >
                Endpoint URL
              </label>
              <input
                type="url"
                value={apiEndpoint}
                onChange={(e) => setApiEndpoint(e.target.value)}
                placeholder="https://api.example.com/data"
                className="w-full px-4 py-3 rounded-lg focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: 'var(--color-text)',
                  fontSize: 'var(--font-size-base)',
                }}
              />
            </div>

            <div className="space-y-2">
              <label
                className="block text-sm font-semibold"
                style={{ color: 'var(--color-text)' }}
              >
                Auth Header Name (optional)
              </label>
              <input
                type="text"
                value={authHeader}
                onChange={(e) => setAuthHeader(e.target.value)}
                placeholder="e.g., Authorization"
                className="w-full px-4 py-3 rounded-lg focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: 'var(--color-text)',
                  fontSize: 'var(--font-size-base)',
                }}
              />
            </div>

            <div className="space-y-2">
              <label
                className="block text-sm font-semibold"
                style={{ color: 'var(--color-text)' }}
              >
                Auth Value (optional)
              </label>
              <input
                type="password"
                value={authValue}
                onChange={(e) => setAuthValue(e.target.value)}
                placeholder="e.g., Bearer token123"
                className="w-full px-4 py-3 rounded-lg focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: 'var(--color-text)',
                  fontSize: 'var(--font-size-base)',
                }}
              />
              <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                Stored encrypted in database
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 px-6 py-3 rounded-lg text-sm font-semibold focus-ring"
            style={{
              background: 'var(--color-glass)',
              border: '1px solid var(--color-glass-border)',
              color: 'var(--color-text)',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.5 : 1,
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => handleSubmit(false)}
            disabled={!isFormValid() || isLoading}
            className="flex-1 px-6 py-3 rounded-lg text-sm font-semibold focus-ring"
            style={{
              background: !isFormValid() || isLoading ? 'var(--color-glass)' : 'rgba(102, 126, 234, 0.3)',
              border: '1px solid rgba(102, 126, 234, 0.5)',
              color: 'var(--color-text)',
              cursor: !isFormValid() || isLoading ? 'not-allowed' : 'pointer',
              opacity: !isFormValid() || isLoading ? 0.5 : 1,
            }}
          >
            Save Only
          </button>
          <button
            onClick={() => handleSubmit(true)}
            disabled={!isFormValid() || isLoading}
            className="flex-1 px-6 py-3 rounded-lg text-sm font-semibold btn-gradient focus-ring"
            style={{
              background: !isFormValid() || isLoading ? 'var(--color-glass)' : 'var(--gradient-primary)',
              border: 'none',
              color: 'var(--color-text)',
              cursor: !isFormValid() || isLoading ? 'not-allowed' : 'pointer',
              opacity: !isFormValid() || isLoading ? 0.5 : 1,
              boxShadow: !isFormValid() || isLoading ? 'none' : 'var(--shadow-glow)',
            }}
          >
            {isLoading ? 'Saving...' : 'Save & Index'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddSourceModal;
