/**
 * DesignReviewScreen - Human-in-the-loop design approval interface
 *
 * Displays generated design (app name, stack, entities, API endpoints) for user review.
 * User can approve to continue execution or reject to cancel.
 * Advanced users can toggle JSON editor to modify design_yaml directly.
 */
import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { generationControlApi } from '../api/client';
import type { DesignStateResponse, Entity, APIEndpoint } from '../types';

interface DesignReviewScreenProps {
  projectId: string;
  onApprove: () => void;
  onReject: () => void;
}

export default function DesignReviewScreen({ projectId, onApprove, onReject }: DesignReviewScreenProps) {
  const [designState, setDesignState] = useState<DesignStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showJsonEditor, setShowJsonEditor] = useState(false);
  const [jsonEditorValue, setJsonEditorValue] = useState('');
  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);

  useEffect(() => {
    loadDesignState();
  }, [projectId]);

  const loadDesignState = async () => {
    try {
      setLoading(true);
      setError('');
      const state = await generationControlApi.getDesignState(projectId);
      setDesignState(state);
      setJsonEditorValue(JSON.stringify(state.design_yaml, null, 2));
    } catch (err: any) {
      console.error('Failed to load design state:', err);
      setError(err.response?.data?.detail || 'Failed to load design state');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      setApproving(true);
      setError('');

      let designChanges = undefined;

      // If JSON editor is active, parse and send changes
      if (showJsonEditor) {
        try {
          designChanges = JSON.parse(jsonEditorValue);
        } catch (err) {
          setError('Invalid JSON in editor');
          setApproving(false);
          return;
        }
      }

      await generationControlApi.approveDesign(projectId, designChanges);
      onApprove();
    } catch (err: any) {
      console.error('Failed to approve design:', err);
      setError(err.response?.data?.detail || 'Failed to approve design');
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async () => {
    try {
      setRejecting(true);
      setError('');
      await generationControlApi.rejectDesign(projectId);
      onReject();
    } catch (err: any) {
      console.error('Failed to reject design:', err);
      setError(err.response?.data?.detail || 'Failed to reject design');
    } finally {
      setRejecting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto p-8 space-y-6">
        <div className="glass-card p-8 text-center" style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}>
          <div className="flex items-center justify-center gap-3">
            <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span style={{ color: 'var(--color-text)', fontSize: 'var(--font-size-lg)' }}>
              Loading design...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (error && !designState) {
    return (
      <div className="max-w-5xl mx-auto p-8 space-y-6">
        <div className="glass-card p-8" style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
        }}>
          <p style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-lg)' }}>
            {error}
          </p>
          <Button onClick={loadDesignState} className="mt-4" style={{
            background: 'var(--gradient-primary)',
            color: 'var(--color-text)',
          }}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const design = designState?.design_yaml;

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6 animate-slide-up">
      {/* Header */}
      <div className="text-center space-y-4">
        <h2
          className="text-3xl font-bold"
          style={{
            fontFamily: 'var(--font-heading)',
            background: 'var(--gradient-primary)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Review Generated Design
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-base)' }}>
          Review the architecture design before we generate code
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-lg" style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: 'var(--color-error)',
        }}>
          {error}
        </div>
      )}

      {/* App Overview */}
      <div className="glass-card p-6 space-y-4" style={{
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}>
        <h3 className="text-xl font-semibold" style={{ color: 'var(--color-text)' }}>
          Application Overview
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>App Name</p>
            <p className="text-lg font-medium" style={{ color: 'var(--color-text)' }}>
              {design?.app_name || 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Description</p>
            <p className="text-base" style={{ color: 'var(--color-text-secondary)' }}>
              {design?.description || 'N/A'}
            </p>
          </div>
        </div>

        {/* Tech Stack */}
        {design?.stack && (
          <div className="pt-4 border-t" style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
            <p className="text-sm mb-3" style={{ color: 'var(--color-text-tertiary)' }}>Tech Stack</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(design.stack).map(([key, value]) => (
                <span
                  key={key}
                  className="px-3 py-1 rounded-full text-sm"
                  style={{
                    background: 'rgba(102, 126, 234, 0.2)',
                    border: '1px solid rgba(102, 126, 234, 0.3)',
                    color: 'var(--color-primary)',
                  }}
                >
                  {String(value)}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Entities Table */}
      {design?.entities && design.entities.length > 0 && (
        <div className="glass-card p-6 space-y-4" style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}>
          <h3 className="text-xl font-semibold" style={{ color: 'var(--color-text)' }}>
            Database Entities ({design.entities.length})
          </h3>

          <div className="space-y-4">
            {design.entities.map((entity: Entity, idx: number) => (
              <div
                key={idx}
                className="p-4 rounded-lg"
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <h4 className="font-semibold mb-2" style={{ color: 'var(--color-text)' }}>
                  {entity.name}
                </h4>
                {entity.description && (
                  <p className="text-sm mb-3" style={{ color: 'var(--color-text-secondary)' }}>
                    {entity.description}
                  </p>
                )}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                        <th className="text-left py-2 px-3" style={{ color: 'var(--color-text-tertiary)' }}>Field</th>
                        <th className="text-left py-2 px-3" style={{ color: 'var(--color-text-tertiary)' }}>Type</th>
                        <th className="text-left py-2 px-3" style={{ color: 'var(--color-text-tertiary)' }}>Required</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entity.fields.map((field, fieldIdx) => (
                        <tr key={fieldIdx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                          <td className="py-2 px-3" style={{ color: 'var(--color-text)' }}>{field.name}</td>
                          <td className="py-2 px-3" style={{ color: 'var(--color-text-secondary)' }}>{field.type}</td>
                          <td className="py-2 px-3" style={{ color: 'var(--color-text-secondary)' }}>
                            {field.required ? '✓' : '✗'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* API Endpoints */}
      {design?.api_endpoints && design.api_endpoints.length > 0 && (
        <div className="glass-card p-6 space-y-4" style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}>
          <h3 className="text-xl font-semibold" style={{ color: 'var(--color-text)' }}>
            API Endpoints ({design.api_endpoints.length})
          </h3>

          <div className="space-y-2">
            {design.api_endpoints.map((endpoint: APIEndpoint, idx: number) => (
              <div
                key={idx}
                className="p-3 rounded flex items-start gap-3"
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <span
                  className="px-2 py-1 rounded text-xs font-mono"
                  style={{
                    background: getMethodColor(endpoint.method),
                    color: 'white',
                    minWidth: '60px',
                    textAlign: 'center',
                  }}
                >
                  {endpoint.method}
                </span>
                <div className="flex-1">
                  <p className="font-mono" style={{ color: 'var(--color-text)' }}>
                    {endpoint.path}
                  </p>
                  <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                    {endpoint.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* JSON Editor Toggle */}
      <div className="glass-card p-6 space-y-4" style={{
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold" style={{ color: 'var(--color-text)' }}>
            Advanced: Edit Design JSON
          </h3>
          <button
            onClick={() => setShowJsonEditor(!showJsonEditor)}
            className="px-4 py-2 rounded transition-all"
            style={{
              background: showJsonEditor ? 'var(--gradient-primary)' : 'rgba(255, 255, 255, 0.1)',
              color: 'var(--color-text)',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            {showJsonEditor ? 'Hide' : 'Show'} JSON Editor
          </button>
        </div>

        {showJsonEditor && (
          <textarea
            value={jsonEditorValue}
            onChange={(e) => setJsonEditorValue(e.target.value)}
            className="w-full font-mono text-sm p-4 rounded-lg"
            rows={20}
            style={{
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: 'var(--color-text)',
              outline: 'none',
              resize: 'vertical',
            }}
          />
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-end">
        <Button
          onClick={handleReject}
          disabled={rejecting || approving}
          className="px-6 py-3 transition-all"
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            color: '#ef4444',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            fontWeight: 600,
            cursor: rejecting || approving ? 'not-allowed' : 'pointer',
            opacity: rejecting || approving ? 0.5 : 1,
          }}
        >
          {rejecting ? 'Rejecting...' : 'Reject Design'}
        </Button>

        <Button
          onClick={handleApprove}
          disabled={approving || rejecting}
          className="px-6 py-3 btn-gradient focus-ring"
          style={{
            background: approving ? 'var(--color-glass)' : 'var(--gradient-primary)',
            color: 'var(--color-text)',
            fontWeight: 700,
            border: 'none',
            boxShadow: approving ? 'none' : 'var(--shadow-glow)',
            cursor: approving || rejecting ? 'not-allowed' : 'pointer',
            opacity: approving || rejecting ? 0.5 : 1,
          }}
        >
          {approving ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Approving...
            </span>
          ) : (
            'Approve & Continue'
          )}
        </Button>
      </div>
    </div>
  );
}

// Helper function to get color for HTTP method
function getMethodColor(method: string): string {
  const colors: Record<string, string> = {
    GET: '#10b981',
    POST: '#3b82f6',
    PUT: '#f59e0b',
    PATCH: '#8b5cf6',
    DELETE: '#ef4444',
  };
  return colors[method.toUpperCase()] || '#6b7280';
}
