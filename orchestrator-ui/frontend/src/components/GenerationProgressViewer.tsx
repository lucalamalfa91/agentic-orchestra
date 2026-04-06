/**
 * Component to view generation progress in real-time via WebSocket.
 */
import React, { useEffect, useState } from 'react';

interface Step {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  percentage: number;
  message: string;
}

interface GenerationProgressViewerProps {
  generationId: string;
  /** Full WebSocket URL returned by /api/generation/start (e.g. ws://host:port/ws/generation/<id>).
   *  If omitted, the URL is derived automatically from window.location so it always
   *  points to the same host/port the frontend is talking to. */
  websocketUrl?: string;
  onClose: () => void;
}

/** Derive the WS URL from the current page location as a safe fallback.
 *  Works regardless of port, hostname or protocol (http → ws, https → wss). */
function deriveWsUrl(generationId: string): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.hostname;
  // Vite dev-proxy forwards /api and /ws to the backend on VITE_API_PORT (default 8000).
  // If a proxy is set up the same origin works; otherwise fall back to :8000.
  const port = window.location.port || '8000';
  return `${proto}://${host}:${port}/ws/generation/${generationId}`;
}

const GenerationProgressViewer: React.FC<GenerationProgressViewerProps> = ({
  generationId,
  websocketUrl,
  onClose,
}) => {
  const [steps, setSteps] = useState<Step[]>([
    { name: 'Architect Agent', status: 'pending', percentage: 0, message: 'Waiting...' },
    { name: 'UXUI Agent', status: 'pending', percentage: 0, message: 'Waiting...' },
    { name: 'Backend Agent', status: 'pending', percentage: 0, message: 'Waiting...' },
    { name: 'Frontend Agent', status: 'pending', percentage: 0, message: 'Waiting...' },
    { name: 'DevOps Agent', status: 'pending', percentage: 0, message: 'Waiting...' },
    { name: 'Publish Agent', status: 'pending', percentage: 0, message: 'Waiting...' },
  ]);
  const [overallProgress, setOverallProgress] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    // Prefer the URL from the API response; fall back to auto-derived URL.
    const wsUrl = websocketUrl || deriveWsUrl(generationId);
    console.log('[WS] Connecting to:', wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      if (cancelled) { ws.close(); return; }
      setIsConnected(true);
      console.log('Connected to generation WebSocket');
    };

    ws.onmessage = (event) => {
      if (cancelled) return;
      try {
        const msg = JSON.parse(event.data);
        console.log('WebSocket message:', msg);

        setOverallProgress(msg.percentage || 0);

        if (msg.message) {
          setSteps((prev) => {
            const updated = [...prev];
            const stepIndex = Math.min(
              Math.floor((msg.percentage || 0) / 20),
              updated.length - 1
            );

            if (stepIndex >= 0) {
              updated[stepIndex] = {
                ...updated[stepIndex],
                status: msg.step === 6 ? 'completed' : 'running',
                percentage: msg.percentage || 0,
                message: msg.message,
              };

              for (let i = 0; i < stepIndex; i++) {
                if (updated[i].status === 'running') {
                  updated[i].status = 'completed';
                }
              }
            }

            return updated;
          });
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onerror = () => {
      if (cancelled) return;
      setError('WebSocket connection error');
    };

    ws.onclose = () => {
      if (cancelled) return;
      setIsConnected(false);
    };

    return () => {
      cancelled = true;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [generationId, websocketUrl]);

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
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
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
            <span style={{ color: '#667eea', fontSize: '0.875rem', fontWeight: 'bold' }}>{Math.round(overallProgress)}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: 'rgba(102, 126, 234, 0.2)', borderRadius: '4px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${overallProgress}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #667eea, #764ba2)',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {steps.map((step, index) => (
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span
                  style={{
                    color: getStatusColor(step.status),
                    fontSize: '0.875rem',
                    fontWeight: 'bold',
                    minWidth: '30px',
                    padding: '0.25rem 0.5rem',
                    background: 'rgba(102, 126, 234, 0.2)',
                    borderRadius: '4px',
                  }}
                >
                  {getStatusIcon(step.status)}
                </span>
                <span style={{ color: '#ffffff', fontSize: '1rem', fontWeight: '500', flex: 1 }}>
                  {step.name}
                </span>
                <span style={{ color: getStatusColor(step.status), fontSize: '0.75rem', fontWeight: '600', textTransform: 'uppercase' }}>
                  {step.status}
                </span>
              </div>
              {step.message && (
                <p style={{ color: '#9ca3af', fontSize: '0.875rem', margin: '0.5rem 0 0 2.5rem', fontStyle: 'italic' }}>
                  {step.message}
                </p>
              )}
            </div>
          ))}
        </div>

        {error && (
          <div
            style={{
              marginTop: '1.5rem',
              padding: '0.75rem 1rem',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              color: '#fca5a5',
              fontSize: '0.875rem',
            }}
          >
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default GenerationProgressViewer;
