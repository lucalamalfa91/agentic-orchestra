/**
 * Hook for managing app generation lifecycle with multi-screen flow.
 * Owns the single WebSocket connection for a generation session.
 */
import { useState, useCallback, useRef } from 'react';
import { useGenerationContext } from '../context/GenerationContext';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const WS_BASE  = API_BASE.replace(/^http/, 'ws');

type Screen = 'creation' | 'progress' | 'confirmation' | 'approval' | 'deploy' | 'success';

interface ApprovalData {
  design: any;
  projectId: number | null;
}

interface GenerationState {
  currentScreen: Screen;
  generationId: string | null;
  isGenerating: boolean;
  wsConnected: boolean;
  design: any | null;
  deployProvider: string | null;
  currentStep: number;
  percentage: number;
  message: string;
  error: string | null;
  stepLogs: Record<number, string[]>;
  pendingApproval: ApprovalData | null;
}

export function useGeneration() {
  const [state, setState] = useState<GenerationState>({
    currentScreen: 'creation',
    generationId: null,
    isGenerating: false,
    wsConnected: false,
    design: null,
    deployProvider: null,
    currentStep: 0,
    percentage: 0,
    message: '',
    error: null,
    stepLogs: {},
    pendingApproval: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const { setActiveGenerationId } = useGenerationContext();

  const startGeneration = useCallback(async (data: any) => {
    if (state.isGenerating) return;

    setState(prev => ({
      ...prev,
      isGenerating: true,
      currentScreen: 'progress',
      error: null,
      wsConnected: false,
      currentStep: 0,
      percentage: 0,
      message: '',
      stepLogs: {},
    }));

    try {
      const res = await fetch(`${API_BASE}/api/generation/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
        },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to start generation');
      }

      const json = await res.json();
      const wsUrl: string = json.websocket_url || `${WS_BASE}/ws/generation/${json.generation_id}`;

      console.log('[WS] Connecting to:', wsUrl);

      setState(prev => ({ ...prev, generationId: json.generation_id }));
      setActiveGenerationId(json.generation_id);

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected');
        setState(prev => ({ ...prev, wsConnected: true }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          console.log('[WS] message:', msg);

          // Human-in-the-loop: design ready, waiting for user approval
          if (msg.type === 'approval_required') {
            setState(prev => ({
              ...prev,
              currentScreen: 'approval',
              pendingApproval: {
                design: msg.design ?? null,
                projectId: msg.project_id ?? null,
              },
            }));
            return;
          }

          // Accumulate log entries per step (from log_entry broadcasts)
          if (msg.type === 'log_entry' && typeof msg.step_number === 'number' && msg.text) {
            setState(prev => {
              const existing = prev.stepLogs[msg.step_number] ?? [];
              return {
                ...prev,
                stepLogs: {
                  ...prev.stepLogs,
                  [msg.step_number]: [...existing, msg.text as string],
                },
              };
            });
            return;
          }

          // Skip heartbeat messages silently
          if (msg.type === 'heartbeat') return;

          // Progress message: update step/percentage/message + append to step log
          setState(prev => {
            const stepNum: number = typeof msg.step_number === 'number'
              ? msg.step_number
              : prev.currentStep;
            const newLogs = (msg.message && stepNum > 0)
              ? {
                  ...prev.stepLogs,
                  [stepNum]: [...(prev.stepLogs[stepNum] ?? []), msg.message as string],
                }
              : prev.stepLogs;
            return {
              ...prev,
              currentStep: msg.step_number ?? prev.currentStep,
              percentage: msg.percentage ?? prev.percentage,
              message: msg.message ?? prev.message,
              stepLogs: newLogs,
            };
          });

          // Design confirmation screen
          if (msg.step_number === 2 && msg.status === 'completed') {
            setState(prev => ({
              ...prev,
              currentScreen: 'confirmation',
              design: msg.design ?? null,
            }));
          }

          // Generation fully complete
          if (msg.step_number === 6 || msg.step === 'complete') {
            setState(prev => ({
              ...prev,
              currentScreen: 'success',
              isGenerating: false,
              percentage: 100,
            }));
            ws.close();
            wsRef.current = null;
          }

          // Error from backend
          if (msg.step === 'error') {
            console.error('[WS] backend error:', msg.message);
            setState(prev => ({
              ...prev,
              error: msg.message || 'Generation failed',
              isGenerating: false,
              wsConnected: false,
            }));
            ws.close();
            wsRef.current = null;
          }
        } catch (e) {
          console.error('[WS] parse error:', e, '| raw data:', event.data);
        }
      };

      ws.onerror = (event: Event) => {
        // The WebSocket API gives very little detail in onerror by design
        // (browsers hide it for security). What we CAN log:
        // - event.type (always 'error')
        // - ws.readyState: 0=CONNECTING 1=OPEN 2=CLOSING 3=CLOSED
        // - ws.url: the URL we tried
        // The real cause will appear in onclose.code (see below).
        console.error(
          '[WS] onerror — type:', event.type,
          '| readyState:', ws.readyState,
          '| url:', ws.url,
          '| (real cause is in onclose.code)'
        );
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error — check backend console for details',
          isGenerating: false,
          wsConnected: false,
        }));
      };

      ws.onclose = (event: CloseEvent) => {
        // Close codes: 1000=normal, 1001=going away, 1006=abnormal (server crash/unreachable)
        // 1006 with no reason = backend closed the socket without a proper close frame,
        // usually means the Python process crashed or the ASGI handler threw.
        const abnormal = event.code !== 1000 && event.code !== 1001;
        const logFn = abnormal ? console.error : console.log;
        logFn(
          '[WS] closed — code:', event.code,
          '| reason:', event.reason || '(none)',
          '| wasClean:', event.wasClean
        );
        if (event.code === 1006) {
          console.error(
            '[WS] code 1006 = abnormal close. Likely causes:',
            '(1) backend crashed mid-generation (check [STDERR] in Python console)',
            '(2) backend was restarted while WS was open',
            '(3) CORS/proxy blocked the WS upgrade'
          );
        }
        setState(prev => ({ ...prev, wsConnected: false, isGenerating: false }));
        wsRef.current = null;
      };

    } catch (err: any) {
      setState(prev => ({
        ...prev,
        error: err.message || 'Failed to start generation',
        currentScreen: 'creation',
        isGenerating: false,
        wsConnected: false,
      }));
    }
  }, [state.isGenerating]);

  const confirmGeneration = useCallback(() => {
    setState(prev => ({ ...prev, currentScreen: 'progress' }));
  }, []);

  const approve = useCallback(async () => {
    const { generationId } = state;
    if (!generationId) return;
    setState(prev => ({
      ...prev,
      currentScreen: 'progress',
      pendingApproval: null,
    }));
    try {
      const res = await fetch(`${API_BASE}/api/generation/${generationId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('jwt_token')}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setState(prev => ({ ...prev, error: err.detail || 'Approval failed' }));
      }
    } catch (err: any) {
      setState(prev => ({ ...prev, error: err.message || 'Approval request failed' }));
    }
  }, [state.generationId]);

  return {
    ...state,
    startGeneration,
    confirmGeneration,
    approve,
  };
}
