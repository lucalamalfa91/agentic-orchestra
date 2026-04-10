/**
 * Main screen for managing knowledge sources.
 */
import React, { useState } from 'react';
import KnowledgeSourceCard from './KnowledgeSourceCard';
import AddSourceModal from './AddSourceModal';
import { useSources, useAddSource, useDeleteSource, useIndexSource } from './useKnowledgeSources';
import type { KnowledgeSourceType } from './types';

const KnowledgeSourcesScreen: React.FC = () => {
  const { sources, loading, error, refetch } = useSources();
  const { addSource, loading: addLoading } = useAddSource();
  const { deleteSource } = useDeleteSource();
  const { startIndexing, getStatus } = useIndexSource();

  const [showAddModal, setShowAddModal] = useState(false);

  const handleAddSource = async (
    name: string,
    type: KnowledgeSourceType,
    config: any,
    andIndex: boolean
  ) => {
    const result = await addSource({ name, source_type: type, config });
    if (result) {
      setShowAddModal(false);
      refetch();
      if (andIndex) {
        startIndexing(result.id);
      }
    }
  };

  const handleDeleteSource = async (sourceId: string) => {
    const success = await deleteSource(sourceId);
    if (success) {
      refetch();
    }
  };

  const handleReindex = (sourceId: string) => {
    startIndexing(sourceId);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between animate-slide-up">
        <div>
          <h2
            className="text-4xl font-bold"
            style={{
              fontFamily: 'var(--font-heading)',
              background: 'var(--gradient-primary)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Knowledge Sources
          </h2>
          <p
            className="mt-2"
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-lg)',
            }}
          >
            Configure context sources for your AI agents
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-gradient focus-ring"
          style={{
            background: 'var(--gradient-primary)',
            color: 'var(--color-text)',
            padding: '0.875rem 1.5rem',
            fontSize: 'var(--font-size-base)',
            fontWeight: 600,
            border: 'none',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-glow)',
            transition: 'var(--transition-default)',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 12px 40px rgba(102, 126, 234, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
          }}
        >
          <svg
            className="inline-block w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Source
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div
          className="p-4 rounded-lg animate-slide-up"
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--color-error)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <svg
            className="animate-spin h-8 w-8"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            style={{ color: 'var(--color-primary)' }}
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      )}

      {/* Empty State */}
      {!loading && sources.length === 0 && (
        <div
          className="glass-card p-12 text-center space-y-4 animate-scale-in"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <svg
            className="mx-auto h-16 w-16"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3
            className="text-xl font-bold"
            style={{
              color: 'var(--color-text)',
              fontFamily: 'var(--font-heading)',
            }}
          >
            No sources yet
          </h3>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Add a knowledge source to give your agents context about your domain,
            company, or technical documentation.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-gradient focus-ring mt-4"
            style={{
              background: 'var(--gradient-primary)',
              color: 'var(--color-text)',
              padding: '0.75rem 1.5rem',
              fontSize: 'var(--font-size-base)',
              fontWeight: 600,
              border: 'none',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-glow)',
              transition: 'var(--transition-default)',
              cursor: 'pointer',
            }}
          >
            Add Your First Source
          </button>
        </div>
      )}

      {/* Sources Grid */}
      {!loading && sources.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-scale-in">
          {sources.map((source) => (
            <KnowledgeSourceCard
              key={source.id}
              source={source}
              onDelete={handleDeleteSource}
              onReindex={handleReindex}
              indexingStatus={getStatus(source.id)}
            />
          ))}
        </div>
      )}

      {/* Add Source Modal */}
      <AddSourceModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddSource}
        isLoading={addLoading}
      />
    </div>
  );
};

export default KnowledgeSourcesScreen;
