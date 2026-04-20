/**
 * Project history component showing all generated apps.
 */
import React, { useEffect, useState, useRef } from 'react';
import { projectsApi, generationControlApi } from '../api/client';
import type { Project } from '../types';
import ProjectCard from './ProjectCard';
import GenerationProgressViewer from './GenerationProgressViewer';
import { useGenerationContext } from '../context/GenerationContext';

const WS_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '').replace(/^http/, 'ws');

interface ProjectHistoryProps {
  onEdit: (projectId: number) => void;
  refreshTrigger?: number; // Used to trigger refresh when new project is created
}

const ProjectHistory: React.FC<ProjectHistoryProps> = ({ onEdit, refreshTrigger }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [progressGenerationId, setProgressGenerationId] = useState<string | null>(null);
  const { activeGenerationId } = useGenerationContext();

  // WebSocket state for progress viewer
  const [wsConnected, setWsConnected] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [percentage, setPercentage] = useState(0);
  const [message, setMessage] = useState('');
  const [wsError, setWsError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (activeGenerationId) {
      setProgressGenerationId(activeGenerationId);
    }
  }, [activeGenerationId]);

  // Connect to WebSocket when progressGenerationId is set
  useEffect(() => {
    if (!progressGenerationId) {
      // Cleanup when modal is closed
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setWsConnected(false);
      setCurrentStep(0);
      setPercentage(0);
      setMessage('');
      setWsError(null);
      return;
    }

    // Connect to WebSocket
    const wsUrl = `${WS_BASE}/ws/generation/${progressGenerationId}`;
    console.log('[ProjectHistory WS] Connecting to:', wsUrl);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[ProjectHistory WS] Connected');
      setWsConnected(true);
      setWsError(null);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log('[ProjectHistory WS] message:', msg);

        setCurrentStep(msg.step_number ?? msg.step ?? 0);
        setPercentage(msg.percentage ?? 0);
        setMessage(msg.message ?? '');

        // Handle error messages
        if (msg.step === 'error') {
          console.error('[ProjectHistory WS] backend error:', msg.message);
          setWsError(msg.message || 'Generation failed');
          ws.close();
        }

        // Handle completion
        if (msg.step_number === 6 || msg.step === 'complete') {
          console.log('[ProjectHistory WS] Generation complete');
          setPercentage(100);
          setTimeout(() => {
            setProgressGenerationId(null);
            fetchProjects(); // Refresh project list
          }, 2000);
        }
      } catch (e) {
        console.error('[ProjectHistory WS] parse error:', e, '| raw data:', event.data);
      }
    };

    ws.onerror = (event: Event) => {
      console.error('[ProjectHistory WS] onerror — readyState:', ws.readyState, '| url:', ws.url);
      setWsError('WebSocket connection error');
      setWsConnected(false);
    };

    ws.onclose = (event: CloseEvent) => {
      console.log('[ProjectHistory WS] closed — code:', event.code, '| reason:', event.reason || '(none)');
      setWsConnected(false);
      wsRef.current = null;
    };

    // Cleanup on unmount or when progressGenerationId changes
    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [progressGenerationId]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await projectsApi.getProjects(page, 20);
      setProjects(response.items);
      setTotalPages(response.total_pages);
    } catch (err) {
      console.error('Error fetching projects:', err);
      setError('Failed to load projects. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [page, refreshTrigger]);

  const filteredProjects = projects.filter(
    (project) =>
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (project.description &&
        project.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleViewProgress = (projectId: string) => {
    setProgressGenerationId(projectId);
  };

  const handleStopGeneration = async (projectId: string) => {
    if (!window.confirm('Stop generation for this project?')) {
      return;
    }

    try {
      await generationControlApi.cancelGeneration(projectId);
      await fetchProjects(); // Refresh list
    } catch (err: any) {
      console.error('Failed to stop generation:', err);
      const errorMessage = err?.response?.data?.detail || 'Failed to stop generation. Please try again.';
      alert(errorMessage);
    }
  };

  const handleCardClick = async (project: Project) => {
    if (project.status !== 'in_progress') return;

    try {
      // Immediate status change to failed (NO confirmation dialog)
      await projectsApi.updateProjectStatus(project.id.toString(), 'failed');
      // Refresh project list
      await fetchProjects();
    } catch (error) {
      console.error('Failed to update project status:', error);
      alert('Failed to update project status');
    }
  };

  const handleDelete = () => {
    fetchProjects(); // Refresh list after delete
  };

  if (loading && projects.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-400">Loading projects...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-6">
        <p className="text-red-800 dark:text-red-200">{error}</p>
        <button
          onClick={fetchProjects}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Project History</h2>
        <button
          onClick={fetchProjects}
          className="px-4 py-2 text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors"
        >
          <svg className="w-5 h-5 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {/* Search */}
      <div>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search projects..."
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
        />
      </div>

      {/* Projects Grid */}
      {filteredProjects.length === 0 ? (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No projects</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {searchTerm ? 'No projects match your search.' : 'Generate your first MVP to get started!'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onEdit={onEdit}
              onViewProgress={handleViewProgress}
              onStopGeneration={handleStopGeneration}
              onDelete={handleDelete}
              onCardClick={handleCardClick}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}

      {progressGenerationId && (
        <GenerationProgressViewer
          generationId={progressGenerationId}
          percentage={percentage}
          currentStep={currentStep}
          message={message}
          isConnected={wsConnected}
          error={wsError}
          onClose={() => setProgressGenerationId(null)}
        />
      )}
    </div>
  );
};

export default ProjectHistory;
