import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import PromptHero from '../components/form/PromptHero';
import AdvancedSettings from '../components/form/AdvancedSettings';
import GenerationProgressViewer from '../components/GenerationProgressViewer';
import { useGeneration } from '../hooks/useGeneration';
import { knowledgeApi } from '../api/client';

export default function MVPCreationScreen() {
  const {
    startGeneration,
    currentScreen,
    generationId,
    percentage,
    currentStep,
    message,
    wsConnected,
    error: genError,
    stepLogs,
    pendingApproval,
    approve,
  } = useGeneration();

  const [prompt, setPrompt] = useState('');
  const [techStack, setTechStack] = useState({});
  const [formError, setFormError] = useState('');
  const [showViewer, setShowViewer] = useState(false);
  const [knowledgeSourceCount, setKnowledgeSourceCount] = useState<number | null>(null);

  useEffect(() => {
    // Fetch knowledge source count
    knowledgeApi.getSources().then((sources) => {
      setKnowledgeSourceCount(sources.length);
    }).catch(() => {
      setKnowledgeSourceCount(0);
    });
  }, []);

  const handleSubmit = async () => {
    if (prompt.length < 20) {
      setFormError('Prompt must be at least 20 characters');
      return;
    }
    setFormError('');
    setShowViewer(true);
    await startGeneration({
      mvp_description: prompt,
      features: ['core-feature'],
      tech_stack: Object.keys(techStack).length > 0 ? techStack : {
        frontend: 'react',
        backend: 'dotnet',
        database: 'postgresql',
        deploy_platform: 'railway',
      },
      auto_decide: true,
    });
  };

  const isLoading = currentScreen === 'progress';

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Generation Progress Overlay */}
      {showViewer && generationId && (
        <GenerationProgressViewer
          generationId={generationId}
          percentage={percentage}
          currentStep={currentStep}
          message={message}
          isConnected={wsConnected}
          error={genError}
          stepLogs={stepLogs}
          pendingApproval={pendingApproval}
          onApprove={approve}
          onClose={() => setShowViewer(false)}
        />
      )}

      {/* Hero Title Section */}
      <div className="text-center space-y-4 animate-slide-up">
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
          Prototype Your Next Idea
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-lg)' }}>
          Describe your idea and get an MVP to test with users or pitch to clients
        </p>
      </div>

      {/* Knowledge Source Context Info */}
      {knowledgeSourceCount !== null && (
        <div
          className="glass-card p-4 flex items-center justify-between animate-slide-up"
          style={{
            background: knowledgeSourceCount === 0
              ? 'rgba(239, 68, 68, 0.1)'
              : 'rgba(16, 185, 129, 0.1)',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${knowledgeSourceCount === 0 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
          }}
        >
          <div className="flex items-center gap-3">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              style={{
                color: knowledgeSourceCount === 0 ? 'var(--color-error)' : 'var(--color-success)',
              }}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <span
              style={{
                color: knowledgeSourceCount === 0 ? 'var(--color-error)' : 'var(--color-success)',
                fontSize: 'var(--font-size-sm)',
                fontWeight: 600,
              }}
            >
              {knowledgeSourceCount === 0
                ? 'No knowledge sources configured — agents will work without context'
                : `Context sources active: ${knowledgeSourceCount}`}
            </span>
          </div>
          <a
            href="/knowledge"
            className="text-sm font-semibold underline hover:no-underline"
            style={{
              color: knowledgeSourceCount === 0 ? 'var(--color-error)' : 'var(--color-success)',
            }}
          >
            {knowledgeSourceCount === 0 ? 'Add sources' : 'Manage'}
          </a>
        </div>
      )}

      {/* Glass Card Container */}
      <div
        className="glass-card p-8 space-y-6 animate-scale-in"
        style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <PromptHero value={prompt} onChange={setPrompt} />
        <AdvancedSettings onTechStackChange={setTechStack} />
      </div>

      {/* Error Messages */}
      {(formError || genError) && (
        <div
          className="p-4 rounded-lg animate-slide-up"
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--color-error)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {formError || genError}
        </div>
      )}

      {/* Generate Button */}
      <Button
        onClick={handleSubmit}
        disabled={isLoading || prompt.length < 20}
        className="w-full btn-gradient focus-ring"
        style={{
          background: isLoading ? 'var(--color-glass)' : 'var(--gradient-primary)',
          color: 'var(--color-text)',
          padding: '1.25rem 2rem',
          fontSize: 'var(--font-size-xl)',
          fontWeight: 700,
          borderRadius: 'var(--radius-lg)',
          border: 'none',
          boxShadow: isLoading ? 'none' : 'var(--shadow-glow)',
          transition: 'var(--transition-default)',
          minHeight: '60px',
          cursor: isLoading || prompt.length < 20 ? 'not-allowed' : 'pointer',
          opacity: isLoading || prompt.length < 20 ? 0.5 : 1,
        }}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-3">
            <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Generating Your MVP...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Generate MVP
          </span>
        )}
      </Button>

      {prompt.length > 0 && (
        <div className="text-center text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
          {prompt.length} / 20 characters minimum
        </div>
      )}
    </div>
  );
}
