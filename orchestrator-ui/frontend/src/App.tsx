import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AIProviderProvider } from './context/AIProviderContext';
import AuthScreen from './screens/AuthScreen';
import OAuthCallback from './screens/OAuthCallback';
import AIProviderSetup from './screens/AIProviderSetup';
import MVPCreationScreen from './screens/MVPCreationScreen';
import ProgressIndicator from './components/ProgressIndicator';
import ProjectHistory from './components/ProjectHistory';
import { useGeneration } from './hooks/useGeneration';
import { useAuth } from './hooks/useAuth';
import './App.css';

function AppContent() {
  const { user, token } = useAuth();
  const { isGenerating, isCompleted } = useGeneration();

  if (!token) return <Navigate to="/auth" />;

  return (
    <div className="min-h-screen animate-fade-in" style={{ background: 'var(--color-background)' }}>
      {/* Luxury Header with Glassmorphism */}
      <header className="glass-card border-b" style={{
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(20px)',
        borderRadius: '0',
        borderTop: 'none',
        borderLeft: 'none',
        borderRight: 'none'
      }}>
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <h1
              className="text-3xl font-bold animate-slide-up"
              style={{
                fontFamily: 'var(--font-heading)',
                background: 'var(--gradient-primary)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              Agentic Orchestra
            </h1>
            {user && (
              <div className="flex items-center gap-3">
                <div className="glass-card px-4 py-2 text-sm">
                  <span style={{ color: 'var(--color-text-secondary)' }}>
                    {user.name || user.email}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content with Premium Spacing */}
      <main className="max-w-7xl mx-auto px-6 py-12 space-y-8">
        <div className="animate-scale-in">
          {isGenerating ? (
            <ProgressIndicator />
          ) : (
            <MVPCreationScreen />
          )}
        </div>
        <div className="animate-slide-up">
          <ProjectHistory />
        </div>
      </main>

      {/* Luxury Footer */}
      <footer className="mt-16 border-t" style={{
        borderColor: 'var(--color-glass-border)',
        background: 'rgba(255, 255, 255, 0.02)'
      }}>
        <div className="max-w-7xl mx-auto px-6 py-8 text-center">
          <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
            Built with precision by Agentic Orchestra
          </p>
          <p className="text-xs mt-2" style={{ color: 'var(--color-text-tertiary)', opacity: 0.6 }}>
            Powered by AI-driven development
          </p>
        </div>
      </footer>
    </div>
  );
}

function AutoAuthWrapper() {
  const { token, setToken } = useAuth();
  const [attemptedAutoAuth, setAttemptedAutoAuth] = useState(false);

  useEffect(() => {
    if (!token && !attemptedAutoAuth) {
      attemptAutoAuth();
    }
  }, [token, attemptedAutoAuth]);

  const attemptAutoAuth = async () => {
    setAttemptedAutoAuth(true);
    try {
      // Check if gh CLI is authenticated
      const checkResponse = await fetch('http://localhost:9000/api/auth/github/check-gh');
      const checkData = await checkResponse.json();

      if (checkData.authenticated) {
        // gh CLI is authenticated, login directly
        const loginResponse = await fetch('http://localhost:9000/api/auth/github/login-with-gh');
        if (loginResponse.ok) {
          const { token: jwt_token } = await loginResponse.json();
          setToken(jwt_token);
        }
      }
    } catch (err) {
      // gh CLI not available or not authenticated, will show AuthScreen
      console.debug('Auto-auth failed, will show login screen');
    }
  };

  return (
    <Routes>
      <Route path="/auth" element={<AuthScreen />} />
      <Route path="/auth/callback" element={<OAuthCallback />} />
      <Route path="/provider-setup" element={<AIProviderSetup />} />
      <Route path="/*" element={<AppContent />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AIProviderProvider>
        <BrowserRouter>
          <AutoAuthWrapper />
        </BrowserRouter>
      </AIProviderProvider>
    </AuthProvider>
  );
}
