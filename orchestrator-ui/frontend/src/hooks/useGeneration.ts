/**
 * Hook for managing app generation lifecycle with multi-screen flow.
 */
import { useState, useCallback } from 'react';
import { useGenerationContext } from '../context/GenerationContext';

type Screen = 'creation' | 'progress' | 'confirmation' | 'deploy' | 'success';

interface GenerationState {
  currentScreen: Screen;
  generationId: string | null;
  isGenerating: boolean;
  design: any | null;
  deployProvider: string | null;
  currentStep: number;
  percentage: number;
  message: string;
  error: string | null;
}

export function useGeneration() {
  const [state, setState] = useState<GenerationState>({
    currentScreen: 'creation',
    generationId: null,
    isGenerating: false,
    design: null,
    deployProvider: null,
    currentStep: 0,
    percentage: 0,
    message: '',
    error: null,
  });

  const { setActiveGenerationId } = useGenerationContext();

  const startGeneration = useCallback(async (data: any) => {
    // Block double-click
    if (state.isGenerating) return;

    setState(prev => ({
      ...prev,
      isGenerating: true,
      currentScreen: 'progress',
      error: null,
    }));

    try {
      // Step 1: Send generation request
      const res = await fetch('http://localhost:9000/api/generation/start', {
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

      setState(prev => ({
        ...prev,
        generationId: json.generation_id,
      }));

      // Notify context so ProjectHistory can show progress
      setActiveGenerationId(json.generation_id);

      // Step 2: Connect WebSocket for progress updates
      const ws = new WebSocket(`ws://localhost:9000/ws/generation/${json.generation_id}`);

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        // Update progress
        setState(prev => ({
          ...prev,
          currentStep: msg.step || prev.currentStep,
          percentage: msg.percentage || prev.percentage,
          message: msg.message || prev.message,
        }));

        // Step 2 completed - show design confirmation
        if (msg.step === 2 && msg.status === 'completed') {
          setState(prev => ({
            ...prev,
            currentScreen: 'confirmation',
            design: msg.design,
          }));
        }

        // Step 6 - generation complete
        if (msg.step === 6) {
          setState(prev => ({
            ...prev,
            currentScreen: 'success',
            isGenerating: false,
          }));
          ws.close();
        }
      };

      ws.onerror = () => {
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error',
          isGenerating: false,
        }));
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setState(prev => ({
          ...prev,
          isGenerating: false,
        }));
      };

    } catch (err: any) {
      setState(prev => ({
        ...prev,
        error: err.message || 'Failed to start generation',
        currentScreen: 'creation',
        isGenerating: false,
      }));
    }
  }, [state.isGenerating]);

  const confirmGeneration = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentScreen: 'progress',
    }));
  }, []);

  return {
    ...state,
    startGeneration,
    confirmGeneration,
  };
}
