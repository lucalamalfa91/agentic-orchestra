/**
 * Card component for displaying a single knowledge source.
 */
import React, { useState } from 'react';
import type { KnowledgeSource, IndexingStatus } from './types';

interface KnowledgeSourceCardProps {
  source: KnowledgeSource;
  onDelete: (sourceId: string) => void;
  onReindex: (sourceId: string) => void;
  indexingStatus: IndexingStatus;
}

const KnowledgeSourceCard: React.FC<KnowledgeSourceCardProps> = ({
  source,
  onDelete,
  onReindex,
  indexingStatus,
}) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never indexed';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getTypeBadgeStyle = (type: string) => {
    switch (type) {
      case 'web':
        return {
          bg: 'rgba(59, 130, 246, 0.1)',
          border: 'rgba(59, 130, 246, 0.3)',
          text: '#93c5fd',
        };
      case 'file':
        return {
          bg: 'rgba(16, 185, 129, 0.1)',
          border: 'rgba(16, 185, 129, 0.3)',
          text: '#6ee7b7',
        };
      case 'api':
        return {
          bg: 'rgba(168, 85, 247, 0.1)',
          border: 'rgba(168, 85, 247, 0.3)',
          text: '#c084fc',
        };
      default:
        return {
          bg: 'var(--color-glass)',
          border: 'var(--color-glass-border)',
          text: 'var(--color-text-tertiary)',
        };
    }
  };

  const getStatusIndicator = () => {
    switch (indexingStatus.status) {
      case 'indexing':
        return (
          <div className="flex items-center gap-2" style={{ color: 'var(--color-primary)' }}>
            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-xs">Indexing...</span>
          </div>
        );
      case 'completed':
        return (
          <div className="flex items-center gap-2" style={{ color: 'var(--color-success)' }}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-xs">Indexed</span>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center gap-2" style={{ color: 'var(--color-error)' }}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span className="text-xs">Failed</span>
          </div>
        );
      default:
        return null;
    }
  };

  const typeBadge = getTypeBadgeStyle(source.source_type);

  return (
    <div
      className="glass-card p-6 space-y-4 group"
      style={{
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
        e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
        e.currentTarget.style.boxShadow = 'none';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3
            className="text-lg font-bold truncate"
            style={{
              color: '#ffffff',
              fontFamily: 'var(--font-heading)',
            }}
          >
            {source.name}
          </h3>
          <p
            className="text-sm mt-1"
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            Last indexed: {formatDate(source.last_indexed_at)}
          </p>
        </div>
        <span
          className="px-3 py-1 text-xs font-semibold rounded-full whitespace-nowrap"
          style={{
            background: typeBadge.bg,
            border: `1px solid ${typeBadge.border}`,
            color: typeBadge.text,
          }}
        >
          {source.source_type.toUpperCase()}
        </span>
      </div>

      {/* Status Indicator */}
      {getStatusIndicator()}

      {/* Error Message */}
      {indexingStatus.status === 'failed' && indexingStatus.message && (
        <div
          className="p-3 rounded-lg text-xs"
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--color-error)',
          }}
        >
          {indexingStatus.message}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 pt-3" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <button
          onClick={() => onReindex(source.id)}
          disabled={indexingStatus.status === 'indexing'}
          className="flex-1 btn-gradient focus-ring"
          style={{
            background: indexingStatus.status === 'indexing' ? 'var(--color-glass)' : 'var(--gradient-primary)',
            color: 'var(--color-text)',
            padding: '0.625rem 1rem',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 600,
            border: 'none',
            borderRadius: 'var(--radius-md)',
            cursor: indexingStatus.status === 'indexing' ? 'not-allowed' : 'pointer',
            transition: 'var(--transition-default)',
            opacity: indexingStatus.status === 'indexing' ? 0.5 : 1,
          }}
        >
          Re-index
        </button>
        <button
          onClick={() => setShowDeleteConfirm(true)}
          disabled={indexingStatus.status === 'indexing'}
          className="px-4 py-2 text-sm font-semibold rounded-md focus-ring"
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#fca5a5',
            cursor: indexingStatus.status === 'indexing' ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s',
            opacity: indexingStatus.status === 'indexing' ? 0.5 : 1,
          }}
          onMouseEnter={(e) => {
            if (indexingStatus.status !== 'indexing') {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.3)';
            }
          }}
          onMouseLeave={(e) => {
            if (indexingStatus.status !== 'indexing') {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
            }
          }}
        >
          Delete
        </button>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{
            background: 'rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(10px)',
          }}
          onClick={() => setShowDeleteConfirm(false)}
        >
          <div
            className="glass-card p-6 space-y-4 max-w-md"
            style={{
              background: 'rgba(30, 25, 50, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              className="text-xl font-bold"
              style={{
                color: '#ffffff',
                fontFamily: 'var(--font-heading)',
              }}
            >
              Delete Knowledge Source?
            </h3>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              Are you sure you want to delete "{source.name}"? This will remove all indexed data and cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2 text-sm font-semibold rounded-md focus-ring"
                style={{
                  background: 'var(--color-glass)',
                  border: '1px solid var(--color-glass-border)',
                  color: 'var(--color-text)',
                  cursor: 'pointer',
                  transition: 'var(--transition-default)',
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onDelete(source.id);
                  setShowDeleteConfirm(false);
                }}
                className="flex-1 px-4 py-2 text-sm font-semibold rounded-md focus-ring"
                style={{
                  background: 'rgba(239, 68, 68, 0.3)',
                  border: '1px solid rgba(239, 68, 68, 0.5)',
                  color: '#fca5a5',
                  cursor: 'pointer',
                  transition: 'var(--transition-default)',
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeSourceCard;
