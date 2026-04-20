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
  const [sessionExpired, setSessionExpired] = useState(false);
  const [deviceFlow, setDeviceFlow] = useState<{
    deviceCode: string;
    userCode: string;
    verificationUri: string;
    interval: number;
  } | null>(null);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    if (token) navigate('/');

    // Check if redirected due to session expiration
    const params = new URLSearchParams(window.location.search);
    if (params.get('session_expired') === 'true') {
      setSessionExpired(true);
    }
  }, [token, navigate]);

  // Poll for device flow completion
  useEffect(() => {
    if (!polling || !deviceFlow) return;

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`${(import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')}/api/auth/github/device-flow/poll`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device_code: deviceFlow.deviceCode }),
        });
        const data = await res.json();

        if (data.status === 'complete') {
          setPolling(false);
          login(data.token);
          // navigate('/') not needed - useEffect above will handle it when token updates
        } else if (data.status === 'error') {
          setPolling(false);
          setError(data.message);
          setDeviceFlow(null);
        } else if (data.status === 'pending') {
          // GitHub might have sent a new interval (slow_down)
          if (data.interval && data.interval !== deviceFlow.interval) {
            console.log(`[POLL] GitHub wants us to slow down. New interval: ${data.interval}s`);
            setDeviceFlow(prev => prev ? {...prev, interval: data.interval} : null);
          }
        }
      } catch (err: any) {
        console.error('Poll error:', err);
      }
    }, (deviceFlow?.interval || 5) * 1000); // Use interval from GitHub

    return () => clearInterval(pollInterval);
  }, [polling, deviceFlow, login, navigate]);

  const handleGitHubLogin = async () => {
    setLoading(true);
    setError('');
    setDeviceFlow(null);

    try {
      // Start device flow
      const res = await fetch(`${(import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')}/api/auth/github/device-flow/start`, {
        method: 'POST',
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to start authentication');
      }

      const data = await res.json();

      // Show device code to user
      setDeviceFlow({
        deviceCode: data.device_code,
        userCode: data.user_code,
        verificationUri: data.verification_uri,
        interval: data.interval || 5,
      });

      // Start polling for completion
      setPolling(true);
      setLoading(false);

    } catch (err: any) {
      const errorText = err.message || 'Failed to initiate login';
      setError(errorText);
      console.error(err);
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

        {/* Session Expired Warning */}
        {sessionExpired && (
          <div
            className="mb-6 p-4 rounded-lg animate-slide-up"
            style={{
              background: 'rgba(251, 191, 36, 0.1)',
              border: '1px solid rgba(251, 191, 36, 0.3)',
              color: '#fbbf24',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 500
            }}
          >
            ⚠️ Your session has expired. Please log in again.
          </div>
        )}

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
            <div className="font-semibold mb-2">Authentication Failed</div>
            <div>{error}</div>
            {error.includes('gh auth') && (
              <div className="mt-3 p-3 rounded" style={{ background: 'rgba(0, 0, 0, 0.2)' }}>
                <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                  Open a terminal and run:
                </div>
                <code className="block mt-1 text-xs" style={{ color: '#fbbf24' }}>
                  {error.includes('refresh') ? 'gh auth refresh' : 'gh auth login'}
                </code>
                <div className="text-xs mt-2" style={{ color: 'var(--color-text-secondary)' }}>
                  Then click the button above again.
                </div>
              </div>
            )}
          </div>
        )}

        {/* Device Flow Instructions */}
        {deviceFlow && (
          <div
            className="mb-6 p-6 rounded-lg animate-slide-up"
            style={{
              background: 'rgba(102, 126, 234, 0.1)',
              border: '2px solid rgba(102, 126, 234, 0.3)',
              textAlign: 'center'
            }}
          >
            <div className="mb-4">
              <div className="text-sm mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                📱 Step 1: Copy your code
              </div>
              <div
                className="text-3xl font-bold mb-4 select-all"
                style={{
                  color: '#fbbf24',
                  fontFamily: 'monospace',
                  letterSpacing: '0.1em',
                  textShadow: '0 0 10px rgba(251, 191, 36, 0.3)'
                }}
              >
                {deviceFlow.userCode}
              </div>
            </div>

            <div className="mb-4">
              <div className="text-sm mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                🌐 Step 2: Open this link
              </div>
              <a
                href={deviceFlow.verificationUri}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block px-6 py-3 rounded-lg"
                style={{
                  background: 'rgba(102, 126, 234, 0.8)',
                  color: 'white',
                  fontWeight: 600,
                  textDecoration: 'none',
                  transition: 'var(--transition-default)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(102, 126, 234, 1)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(102, 126, 234, 0.8)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                Open GitHub Authorization
              </a>
            </div>

            <div className="flex items-center justify-center gap-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Waiting for authorization...
            </div>
          </div>
        )}

        {/* GitHub Login Button */}
        {!deviceFlow && (
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
        )}

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
