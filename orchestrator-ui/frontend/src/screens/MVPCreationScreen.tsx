import { useState } from 'react';
import { Button } from '../components/ui/button';
import PromptHero from '../components/form/PromptHero';
import AdvancedSettings from '../components/form/AdvancedSettings';
import { useGeneration } from '../hooks/useGeneration';

export default function MVPCreationScreen() {
  const { startGeneration } = useGeneration();
  const [prompt, setPrompt] = useState('');
  const [techStack, setTechStack] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (prompt.length < 20) {
      setError('Prompt must be at least 20 characters');
      return;
    }

    setLoading(true);
    try {
      await startGeneration({
        mvp_description: prompt,
        features: ['core-feature'], // Required field - will be auto-decided
        tech_stack: Object.keys(techStack).length > 0 ? techStack : {
          frontend: 'react',
          backend: 'node',
          database: 'postgresql',
          deploy_platform: 'vercel'
        },
        auto_decide: true
      });
    } catch (err: any) {
      setError(err.message || 'Generation failed');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Hero Title Section */}
      <div className="text-center space-y-4 animate-slide-up">
        <h2
          className="text-4xl font-bold"
          style={{
            fontFamily: 'var(--font-heading)',
            background: 'var(--gradient-primary)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}
        >
          Prototype Your Next Idea
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-lg)' }}>
          Describe your idea and get an MVP to test with users or pitch to clients
        </p>
      </div>

      {/* Glass Card Container */}
      <div
        className="glass-card p-8 space-y-6 animate-scale-in"
        style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <PromptHero value={prompt} onChange={setPrompt} />
        <AdvancedSettings onTechStackChange={setTechStack} />
      </div>

      {/* Error Message */}
      {error && (
        <div
          className="p-4 rounded-lg animate-slide-up"
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--color-error)',
            fontSize: 'var(--font-size-sm)'
          }}
        >
          {error}
        </div>
      )}

      {/* Generate Button with Gradient */}
      <Button
        onClick={handleSubmit}
        disabled={loading || prompt.length < 20}
        className="w-full btn-gradient focus-ring"
        style={{
          background: loading ? 'var(--color-glass)' : 'var(--gradient-primary)',
          color: 'var(--color-text)',
          padding: '1.25rem 2rem',
          fontSize: 'var(--font-size-xl)',
          fontWeight: 700,
          borderRadius: 'var(--radius-lg)',
          border: 'none',
          boxShadow: loading ? 'none' : 'var(--shadow-glow)',
          transition: 'var(--transition-default)',
          minHeight: '60px',
          cursor: loading || prompt.length < 20 ? 'not-allowed' : 'pointer',
          opacity: loading || prompt.length < 20 ? 0.5 : 1
        }}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-3">
            <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
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

      {/* Character Count Indicator */}
      {prompt.length > 0 && (
        <div className="text-center text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
          {prompt.length} / 20 characters minimum
        </div>
      )}
    </div>
  );
}
