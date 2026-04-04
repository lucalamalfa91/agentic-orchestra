/**
 * Hook for managing app generation lifecycle.
 */
import { useState, useCallback } from 'react';
import { generationApi, projectsApi } from '../api/client';
import type { GenerationRequest, ProgressMessage, FormData } from '../types';
import { useWebSocket } from './useWebSocket';

type GenerationState = 'idle' | 'generating' | 'completed' | 'error';

export const useGeneration = () => {
  const [state, setState] = useState<GenerationState>('idle');
  const [_generationId, setGenerationId] = useState<string | null>(null);
  const [websocketUrl, setWebsocketUrl] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [percentage, setPercentage] = useState(0);
  const [message, setMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [_projectId, setProjectId] = useState<number | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleProgressMessage = useCallback((msg: ProgressMessage) => {
    setCurrentStep(msg.step_number);
    setPercentage(msg.percentage);
    setMessage(msg.message);

    if (msg.percentage === 100) {
      setState('completed');
      // Trigger project history refresh
      setRefreshTrigger((prev) => prev + 1);
    }
  }, []);

  const handleWebSocketError = useCallback((error: Event) => {
    console.error('WebSocket error:', error);
    // Don't fail the whole generation on WebSocket error
    // The generation continues in the background
  }, []);

  const handleWebSocketClose = useCallback(() => {
    console.log('WebSocket closed');
  }, []);

  const { isConnected, disconnect } = useWebSocket(websocketUrl, {
    onMessage: handleProgressMessage,
    onError: handleWebSocketError,
    onClose: handleWebSocketClose,
  });

  const startGeneration = useCallback(
    async (formData: FormData) => {
      try {
        setState('generating');
        setError(null);
        setCurrentStep(0);
        setPercentage(0);
        setMessage('Starting generation...');

        // Parse features and user stories from newline-separated text
        const features = formData.features
          .split('\n')
          .map((f) => f.trim())
          .filter((f) => f.length > 0);

        const userStories = formData.user_stories
          ? formData.user_stories
              .split('\n')
              .map((s) => s.trim())
              .filter((s) => s.length > 0)
          : undefined;

        // Create generation request
        const request: GenerationRequest = {
          mvp_description: formData.mvp_description,
          features,
          user_stories: userStories,
          tech_stack: {
            frontend: formData.frontend,
            backend: formData.backend,
            database: formData.database,
            deploy_platform: formData.deploy_platform,
          },
        };

        // Start generation
        const response = await generationApi.startGeneration(request);
        setGenerationId(response.generation_id);
        setWebsocketUrl(response.websocket_url);

        console.log('✅ Generation started:', response);
      } catch (err: any) {
        console.error('❌ Failed to start generation:', err);
        setState('error');
        setError(err.response?.data?.detail || err.message || 'Failed to start generation');
      }
    },
    []
  );

  const reset = useCallback(() => {
    disconnect();
    setState('idle');
    setGenerationId(null);
    setWebsocketUrl(null);
    setCurrentStep(0);
    setPercentage(0);
    setMessage('');
    setError(null);
    setProjectId(null);
  }, [disconnect]);

  const loadProjectForEdit = useCallback(async (projectId: number): Promise<FormData | null> => {
    try {
      const requirements = await projectsApi.getProjectRequirements(projectId);

      // Parse features and user stories from JSON strings
      const features = JSON.parse(requirements.features || '[]').join('\n');
      const userStories = requirements.user_stories
        ? JSON.parse(requirements.user_stories).join('\n')
        : '';

      return {
        mvp_description: requirements.mvp_description,
        features,
        user_stories: userStories,
        frontend: requirements.frontend_framework || 'react',
        backend: requirements.backend_framework || 'dotnet',
        database: requirements.database_type || 'none',
        deploy_platform: requirements.deploy_platform || 'vercel',
      };
    } catch (err) {
      console.error('Failed to load project requirements:', err);
      return null;
    }
  }, []);

  return {
    // State
    state,
    isGenerating: state === 'generating',
    isCompleted: state === 'completed',
    isError: state === 'error',
    error,
    currentStep,
    percentage,
    message,
    isConnected,
    refreshTrigger,

    // Actions
    startGeneration,
    reset,
    loadProjectForEdit,
  };
};
