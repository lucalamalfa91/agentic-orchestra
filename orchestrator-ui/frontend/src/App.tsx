/**
 * Main Orchestrator UI Application.
 */
import { useState } from 'react';
import GenerationForm from './components/GenerationForm';
import ProgressIndicator from './components/ProgressIndicator';
import ProjectHistory from './components/ProjectHistory';
import { useGeneration } from './hooks/useGeneration';
import type { FormData } from './types';
import './App.css';

function App() {
  const {
    isGenerating,
    isCompleted,
    isError,
    error,
    currentStep,
    percentage,
    message,
    refreshTrigger,
    startGeneration,
    reset,
    loadProjectForEdit,
  } = useGeneration();

  const [formData, setFormData] = useState<Partial<FormData>>({});

  const handleFormSubmit = async (data: FormData) => {
    await startGeneration(data);
  };

  const handleEdit = async (projectId: number) => {
    const data = await loadProjectForEdit(projectId);
    if (data) {
      setFormData(data);
      // Scroll to form
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleReset = () => {
    reset();
    setFormData({});
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                🤖 Agentic Orchestra
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                AI-powered full-stack app generation
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300"
              >
                API Docs
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Error Banner */}
          {isError && error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                </div>
                <button
                  onClick={handleReset}
                  className="ml-3 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-500"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Success Banner */}
          {isCompleted && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-green-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <p className="text-sm text-green-800 dark:text-green-200">
                    🎉 App generated successfully! Check the project history below for the GitHub link.
                  </p>
                </div>
                <button
                  onClick={handleReset}
                  className="ml-3 text-sm font-medium text-green-600 dark:text-green-400 hover:text-green-500"
                >
                  Generate Another
                </button>
              </div>
            </div>
          )}

          {/* Generation Form or Progress */}
          {!isGenerating && !isCompleted ? (
            <GenerationForm
              onSubmit={handleFormSubmit}
              isGenerating={isGenerating}
              initialData={formData}
            />
          ) : (
            <ProgressIndicator
              currentStep={currentStep}
              percentage={percentage}
              message={message}
            />
          )}

          {/* Project History */}
          <ProjectHistory onEdit={handleEdit} refreshTrigger={refreshTrigger} />
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600 dark:text-gray-400">
            Built with ❤️ by the Agentic Orchestra team
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
