import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { getGitHubAuthUrl, loginWithGhCLI } from '../lib/api/auth';
import { useAuth } from '../hooks/useAuth';

export default function AuthScreen() {
  const navigate = useNavigate();
  const { token, login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) navigate('/');
  }, [token, navigate]);

  const handleGitHubLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getGitHubAuthUrl();

      // If gh CLI is available, use it
      if (data.use_gh_cli) {
        const result = await loginWithGhCLI();
        if (result.token) {
          login(result.token);
          navigate('/');
        } else {
          setError('Failed to authenticate with gh CLI');
        }
      } else if (data.url) {
        window.location.href = data.url;
      } else {
        setError('GitHub authentication not available');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to initiate login');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center gradient-hero animate-fade-in"
      style={{
        background: 'var(--gradient-primary)',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Animated Background Pattern */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'radial-gradient(circle at 20% 50%, rgba(118, 75, 162, 0.3) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(102, 126, 234, 0.3) 0%, transparent 50%)',
        opacity: 0.5
      }} />

      {/* Glassmorphism Auth Card */}
      <div
        className="glass-card p-10 max-w-md w-full mx-4 animate-scale-in"
        style={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: 'var(--shadow-xl)',
          position: 'relative',
          zIndex: 10
        }}
      >
        {/* Logo/Title with Gradient */}
        <div className="text-center mb-8">
          <h1
            className="text-4xl font-bold mb-3"
            style={{
              fontFamily: 'var(--font-heading)',
              color: 'var(--color-text)',
              textShadow: '0 2px 10px rgba(0, 0, 0, 0.3)'
            }}
          >
            Agentic Orchestra
          </h1>
          <p
            className="text-lg"
            style={{
              color: 'var(--color-text-secondary)',
              fontWeight: 300
            }}
          >
            Rapid MVP Generator
          </p>
        </div>

        {/* Description */}
        <p
          className="text-center mb-8"
          style={{
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--font-size-sm)',
            lineHeight: 1.6
          }}
        >
          Turn business ideas into working prototypes. Test concepts, build mockups, and pitch MVPs to clients
        </p>

        {/* Error Message */}
        {error && (
          <div
            className="mb-6 p-4 rounded-lg animate-slide-up"
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

        {/* GitHub Login Button */}
        <Button
          onClick={handleGitHubLogin}
          disabled={loading}
          className="w-full btn-gradient focus-ring"
          style={{
            background: loading ? 'var(--color-glass)' : 'rgba(0, 0, 0, 0.8)',
            color: 'var(--color-text)',
            padding: '1rem',
            fontSize: 'var(--font-size-lg)',
            fontWeight: 600,
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            backdropFilter: 'blur(10px)',
            transition: 'var(--transition-default)',
            minHeight: '44px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Connecting...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              Connect with GitHub
            </span>
          )}
        </Button>

        {/* Footer Note */}
        <p
          className="text-center mt-6"
          style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-tertiary)',
            opacity: 0.8
          }}
        >
          Secure authentication via GitHub OAuth
        </p>
      </div>
    </div>
  );
}
