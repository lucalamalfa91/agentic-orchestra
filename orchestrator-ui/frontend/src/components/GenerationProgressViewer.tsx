/**
 * Component to view generation progress in real-time.
 * No WebSocket here — progress state is passed in as props from useGeneration.
 */
import React, { useState } from 'react';

interface Step {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  message: string;
}

interface DesignSummary {
  project_name?: string;
  app_name?: string;
  tech_stack?: {
    frontend?: string;
    backend?: string;
    database?: string;
    deploy_platform?: string;
  };
  entities?: Array<{ name: string; description?: string } | string>;
  api_endpoints?: Array<{ path?: string; method?: string; description?: string } | string>;
  [key: string]: unknown;
}

interface GenerationProgressViewerProps {
  generationId: string;
  /** Overall progress percentage (0-100) */
  percentage: number;
  /** Current step number (0-6) */
  currentStep: number;
  /** Latest message from backend */
  message: string;
  /** True when the WebSocket is open */
  isConnected: boolean;
  /** Error string if WS or generation failed */
  error: string | null;
  /** Log lines accumulated per step number (1-6) */
  stepLogs?: Record<number, string[]>;
  /** Set when the graph is paused waiting for human approval */
  pendingApproval?: { design: DesignSummary | null; projectId: number | null } | null;
  /** Called when the user clicks Approve */
  onApprove?: () => void;
  onClose: () => void;
}

const STEP_NAMES = [
  'Architect Agent',
  'UXUI Agent',
  'Backend Agent',
  'Frontend Agent',
  'DevOps Agent',
  'Publish Agent',
];

const GenerationProgressViewer: React.FC<GenerationProgressViewerProps> = ({
  generationId,
  percentage,
  currentStep,
  message,
  isConnected,
  error,
  stepLogs = {},
  pendingApproval,
  onApprove,
  onClose,
}) => {
  // Track which steps have their log section expanded (running step auto-expands)
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps(prev => ({ ...prev, [stepNumber]: !prev[stepNumber] }));
  };

  const isExpanded = (stepNumber: number, status: string) =>
    status === 'running' ? (expandedSteps[stepNumber] ?? true) : (expandedSteps[stepNumber] ?? false);

  // Derive per-step status from currentStep + percentage
  const steps: Step[] = STEP_NAMES.map((name, i) => {
    const stepNumber = i + 1;
    let status: Step['status'] = 'pending';
    if (stepNumber < currentStep) status = 'completed';
    else if (stepNumber === currentStep) status = percentage >= 100 ? 'completed' : 'running';
    return { name, status, message: stepNumber === currentStep ? message : '' };
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'running':   return '#3b82f6';
      case 'failed':    return '#ef4444';
      default:          return '#9ca3af';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return 'OK';
      case 'running':   return '...';
      case 'failed':    return 'X';
      default:          return '-';
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(0, 0, 0, 0.7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'rgba(20, 15, 40, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(102, 126, 234, 0.3)',
          borderRadius: '12px',
          padding: '2rem',
          maxWidth: '500px',
          width: '90%',
          maxHeight: '80vh',
          overflow: 'auto',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Human-in-the-loop approval overlay */}
        {pendingApproval && (
          <div style={{
            marginBottom: '2rem',
            padding: '1.5rem',
            background: 'rgba(102, 126, 234, 0.08)',
            border: '1px solid rgba(102, 126, 234, 0.5)',
            borderRadius: '10px',
          }}>
            <h3 style={{ color: '#a5b4fc', fontSize: '1.1rem', fontWeight: 700, margin: '0 0 1rem 0' }}>
              Design Ready — Approve to Generate Code
            </h3>

            {pendingApproval.design && (() => {
              const d = pendingApproval.design as DesignSummary;
              const name = d.project_name ?? d.app_name;
              const stack = d.tech_stack;
              const entities = d.entities ?? [];
              const endpoints = d.api_endpoints ?? [];
              return (
                <>
                  {name && (
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span style={{ color: '#9ca3af', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>App</span>
                      <div style={{ color: '#ffffff', fontWeight: 600, marginTop: '0.25rem' }}>{name}</div>
                    </div>
                  )}

                  {stack && (
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span style={{ color: '#9ca3af', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Tech Stack</span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.25rem' }}>
                        {Object.entries(stack).filter(([, v]) => v).map(([k, v]) => (
                          <span key={k} style={{
                            background: 'rgba(102, 126, 234, 0.2)',
                            border: '1px solid rgba(102, 126, 234, 0.3)',
                            borderRadius: '4px',
                            color: '#c4b5fd',
                            fontSize: '0.75rem',
                            padding: '0.15rem 0.5rem',
                          }}>
                            {k}: {String(v)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {entities.length > 0 && (
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span style={{ color: '#9ca3af', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Entities ({entities.length})
                      </span>
                      <div style={{ marginTop: '0.25rem', display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                        {entities.slice(0, 8).map((e, i) => (
                          <span key={i} style={{
                            background: 'rgba(16, 185, 129, 0.1)',
                            border: '1px solid rgba(16, 185, 129, 0.3)',
                            borderRadius: '4px',
                            color: '#6ee7b7',
                            fontSize: '0.75rem',
                            padding: '0.15rem 0.5rem',
                          }}>
                            {typeof e === 'string' ? e : e.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {endpoints.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <span style={{ color: '#9ca3af', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        API Endpoints ({endpoints.length})
                      </span>
                      <div style={{ marginTop: '0.25rem', fontFamily: 'monospace', fontSize: '0.72rem', color: '#94a3b8', lineHeight: 1.8 }}>
                        {endpoints.slice(0, 6).map((ep, i) => (
                          <div key={i}>
                            {typeof ep === 'string' ? ep : `${ep.method ?? 'GET'} ${ep.path ?? ''}`}
                          </div>
                        ))}
                        {endpoints.length > 6 && <div style={{ color: '#6b7280' }}>+ {endpoints.length - 6} more</div>}
                      </div>
                    </div>
                  )}
                </>
              );
            })()}

            <button
              onClick={onApprove}
              style={{
                width: '100%',
                padding: '0.75rem',
                background: 'linear-gradient(90deg, #667eea, #764ba2)',
                border: 'none',
                borderRadius: '8px',
                color: '#ffffff',
                fontSize: '0.95rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
                transition: 'opacity 0.2s',
              }}
              onMouseEnter={e => (e.currentTarget.style.opacity = '0.85')}
              onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
            >
              Approve and Generate Code
            </button>
          </div>
        )}

        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ color: '#ffffff', fontSize: '1.5rem', fontWeight: 'bold', margin: 0 }}>
              Generation Progress
            </h2>
            <button
              onClick={onClose}
              style={{ background: 'transparent', border: 'none', color: '#ffffff', fontSize: '1.5rem', cursor: 'pointer' }}
            >
              X
            </button>
          </div>
          <p style={{ color: '#9ca3af', margin: '0.5rem 0 0 0' }}>ID: {generationId}</p>
        </div>

        {/* Connection Status */}
        <div
          style={{
            marginBottom: '1.5rem',
            padding: '0.75rem 1rem',
            background: isConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${isConnected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '8px',
            color: isConnected ? '#86efac' : '#fca5a5',
            fontSize: '0.875rem',
          }}
        >
          {isConnected ? '[OK] Connected' : '[X] Disconnected'}
        </div>

        {/* Overall Progress Bar */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ color: '#e0e0ff', fontSize: '0.875rem', fontWeight: '500' }}>Overall Progress</span>
            <span style={{ color: '#667eea', fontSize: '0.875rem', fontWeight: 'bold' }}>{Math.round(percentage)}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: 'rgba(102, 126, 234, 0.2)', borderRadius: '4px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${percentage}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #667eea, #764ba2)',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {steps.map((step, index) => {
            const stepNumber = index + 1;
            const logs = stepLogs[stepNumber] ?? [];
            const expanded = isExpanded(stepNumber, step.status);
            return (
              <div
                key={index}
                style={{
                  padding: '1rem',
                  background: 'rgba(40, 30, 65, 0.5)',
                  border: `1px solid ${
                    step.status === 'running'   ? 'rgba(102, 126, 234, 0.6)' :
                    step.status === 'completed' ? 'rgba(16, 185, 129, 0.4)' :
                                                 'rgba(102, 126, 234, 0.2)'
                  }`,
                  borderRadius: '8px',
                  transition: 'all 0.3s',
                }}
              >
                {/* Step header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{
                    color: getStatusColor(step.status),
                    fontSize: '0.875rem', fontWeight: 'bold',
                    minWidth: '30px', padding: '0.25rem 0.5rem',
                    background: 'rgba(102, 126, 234, 0.2)', borderRadius: '4px',
                  }}>
                    {getStatusIcon(step.status)}
                  </span>
                  <span style={{ color: '#ffffff', fontSize: '1rem', fontWeight: '500', flex: 1 }}>
                    {step.name}
                  </span>
                  <span style={{ color: getStatusColor(step.status), fontSize: '0.75rem', fontWeight: '600', textTransform: 'uppercase' }}>
                    {step.status}
                  </span>
                  {/* Log toggle button */}
                  {logs.length > 0 && (
                    <button
                      onClick={() => toggleStep(stepNumber)}
                      style={{
                        background: 'rgba(102, 126, 234, 0.15)',
                        border: '1px solid rgba(102, 126, 234, 0.3)',
                        borderRadius: '4px',
                        color: '#a5b4fc',
                        fontSize: '0.7rem',
                        padding: '0.2rem 0.5rem',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {expanded ? '▲' : '▼'} Logs ({logs.length})
                    </button>
                  )}
                </div>

                {/* Expandable log section */}
                {expanded && logs.length > 0 && (
                  <div style={{
                    marginTop: '0.75rem',
                    marginLeft: '2.5rem',
                    padding: '0.5rem 0.75rem',
                    background: 'rgba(0, 0, 0, 0.3)',
                    borderRadius: '6px',
                    borderLeft: '2px solid rgba(102, 126, 234, 0.4)',
                    maxHeight: '180px',
                    overflowY: 'auto',
                  }}>
                    {logs.map((line, i) => (
                      <div key={i} style={{
                        fontFamily: 'monospace',
                        fontSize: '0.72rem',
                        color: '#94a3b8',
                        lineHeight: '1.6',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}>
                        {line}
                      </div>
                    ))}
                  </div>
                )}

                {step.message && !expanded && (
                  <p style={{ color: '#9ca3af', fontSize: '0.875rem', margin: '0.5rem 0 0 2.5rem', fontStyle: 'italic' }}>
                    {step.message}
                  </p>
                )}
              </div>
            );
          })}
        </div>

        {error && (
          <div style={{
            marginTop: '1.5rem', padding: '0.75rem 1rem',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px', color: '#fca5a5', fontSize: '0.875rem',
          }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default GenerationProgressViewer;
