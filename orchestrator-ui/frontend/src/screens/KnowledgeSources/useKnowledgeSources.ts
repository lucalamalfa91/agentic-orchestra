/**
 * Custom hook for knowledge sources API operations.
 */
import { useState, useEffect, useCallback } from 'react';
import { knowledgeApi } from '../../api/client';
import type { KnowledgeSource, KnowledgeSourceCreate, IndexingStatus } from './types';

export function useSources() {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await knowledgeApi.getSources();
      setSources(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch knowledge sources');
      console.error('Failed to fetch sources:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  return { sources, loading, error, refetch: fetchSources };
}

export function useAddSource() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addSource = useCallback(async (data: KnowledgeSourceCreate): Promise<KnowledgeSource | null> => {
    try {
      setLoading(true);
      setError(null);
      const response = await knowledgeApi.createSource(data);
      return response;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create knowledge source');
      console.error('Failed to add source:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { addSource, loading, error };
}

export function useDeleteSource() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteSource = useCallback(async (sourceId: string): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);
      await knowledgeApi.deleteSource(sourceId);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete knowledge source');
      console.error('Failed to delete source:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { deleteSource, loading, error };
}

export function useIndexSource() {
  const [indexingStatuses, setIndexingStatuses] = useState<Record<string, IndexingStatus>>({});

  const startIndexing = useCallback(async (sourceId: string) => {
    try {
      // Set status to indexing
      setIndexingStatuses((prev) => ({
        ...prev,
        [sourceId]: { status: 'indexing', message: 'Starting indexing...' },
      }));

      // Trigger indexing
      await knowledgeApi.indexSource(sourceId);

      // Poll for status every 2 seconds
      const pollInterval = setInterval(async () => {
        try {
          const status = await knowledgeApi.getIndexingStatus(sourceId);

          setIndexingStatuses((prev) => ({
            ...prev,
            [sourceId]: status,
          }));

          // Stop polling if completed or failed
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval);
          }
        } catch (err) {
          console.error('Failed to poll indexing status:', err);
          clearInterval(pollInterval);
          setIndexingStatuses((prev) => ({
            ...prev,
            [sourceId]: { status: 'failed', message: 'Failed to check indexing status' },
          }));
        }
      }, 2000);

      // Auto-cleanup after 5 minutes
      setTimeout(() => clearInterval(pollInterval), 5 * 60 * 1000);
    } catch (err: any) {
      console.error('Failed to start indexing:', err);
      setIndexingStatuses((prev) => ({
        ...prev,
        [sourceId]: { status: 'failed', message: err.response?.data?.detail || 'Failed to start indexing' },
      }));
    }
  }, []);

  const getStatus = useCallback((sourceId: string): IndexingStatus => {
    return indexingStatuses[sourceId] || { status: 'idle' };
  }, [indexingStatuses]);

  return { startIndexing, getStatus };
}
