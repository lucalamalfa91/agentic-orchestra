import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AIProviderProvider } from './context/AIProviderContext';
import { GenerationProvider } from './context/GenerationContext';
import AuthScreen from './screens/AuthScreen';
import OAuthCallback from './screens/OAuthCallback';
import AIProviderSetup from './screens/AIProviderSetup';
import MVPCreationScreen from './screens/MVPCreationScreen';
import KnowledgeSourcesScreen from './screens/KnowledgeSources';
import ProgressIndicator from './components/ProgressIndicator';
import ProjectHistory from './components/ProjectHistory';
import { useGeneration } from './hooks/useGeneration';
import { useAuth } from './hooks/useAuth';
import './App.css';

function AppContent() {
  const { user, token } = useAuth();
  const { isGenerating, currentStep, percentage, message } = useGeneration();
  const location = useLocation();

  if (!token) return <Navigate to="/auth" />;

  const isKnowledgePage = location.pathname === '/knowledge';

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
          {/* Navigation Tabs */}
          <nav className="flex gap-4 mt-6">
            <Link
              to="/"
              className="px-4 py-2 rounded-lg text-sm font-semibold transition-all focus-ring"
              style={{
                background: location.pathname === '/' ? 'var(--gradient-primary)' : 'var(--color-glass)',
                border: `1px solid ${location.pathname === '/' ? 'rgba(102, 126, 234, 0.5)' : 'var(--color-glass-border)'}`,
                color: 'var(--color-text)',
              }}
            >
              Create MVP
            </Link>
            <Link
              to="/knowledge"
              className="px-4 py-2 rounded-lg text-sm font-semibold transition-all focus-ring"
              style={{
                background: location.pathname === '/knowledge' ? 'var(--gradient-primary)' : 'var(--color-glass)',
                border: `1px solid ${location.pathname === '/knowledge' ? 'rgba(102, 126, 234, 0.5)' : 'var(--color-glass-border)'}`,
                color: 'var(--color-text)',
              }}
            >
              Knowledge Sources
            </Link>
            <Link
              to="/settings"
              className="px-4 py-2 rounded-lg text-sm font-semibold transition-all focus-ring"
              style={{
                background: location.pathname === '/settings' ? 'var(--gradient-primary)' : 'var(--color-glass)',
                border: `1px solid ${location.pathname === '/settings' ? 'rgba(102, 126, 234, 0.5)' : 'var(--color-glass-border)'}`,
                color: 'var(--color-text)',
              }}
            >
              ⚙️ Settings
            </Link>
          </nav>
        </div>
      </header>

      {/* Main Content with Premium Spacing */}
      <main className="max-w-7xl mx-auto px-6 py-12 space-y-8">
        <Routes>
          <Route
            path="/"
            element={
              <>
                <div className="animate-scale-in">
                  {isGenerating ? (
                    <ProgressIndicator
                      currentStep={currentStep}
                      percentage={percentage}
                      message={message}
                    />
                  ) : (
                    <MVPCreationScreen />
                  )}
                </div>
                <div className="animate-slide-up">
                  <ProjectHistory onEdit={(id) => console.log('Edit project:', id)} />
                </div>
              </>
            }
          />
          <Route path="/knowledge" element={<KnowledgeSourcesScreen />} />
          <Route path="/settings" element={<AIProviderSetup />} />
        </Routes>
      </main>

      {/* Luxury Footer */}
      <footer className="mt-16 border-t" style={{
        borderColor: 'var(--color-glass-border)',
        background: 'rgba(255, 255, 255, 0.02)'
      }}>
        <div className="max-w-7xl mx-auto px-6 py-8 text-center">
          <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
            From idea to MVP in minutes
          </p>
          <p className="text-xs mt-2" style={{ color: 'var(--color-text-tertiary)', opacity: 0.6 }}>
            Validate your business ideas with AI-generated prototypes
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
      const _apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const checkResponse = await fetch(`${_apiBase}/api/auth/github/check-gh`);
      const checkData = await checkResponse.json();

      if (checkData.authenticated) {
        // gh CLI is authenticated, login directly
        const loginResponse = await fetch(`${_apiBase}/api/auth/github/login-with-gh`);
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
      <Route path="*" element={<AppContent />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AIProviderProvider>
        <GenerationProvider>
          <BrowserRouter>
            <AutoAuthWrapper />
          </BrowserRouter>
        </GenerationProvider>
      </AIProviderProvider>
    </AuthProvider>
  );
}
