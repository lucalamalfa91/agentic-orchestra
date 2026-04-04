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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">🤖 Agentic Orchestra</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {isGenerating ? (
          <ProgressIndicator />
        ) : (
          <MVPCreationScreen />
        )}
        <ProjectHistory />
      </main>

      <footer className="mt-12 bg-white border-t">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-600">
          Built with ❤️ by Agentic Orchestra
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AIProviderProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/auth" element={<AuthScreen />} />
            <Route path="/auth/callback" element={<OAuthCallback />} />
            <Route path="/provider-setup" element={<AIProviderSetup />} />
            <Route path="/*" element={<AppContent />} />
          </Routes>
        </BrowserRouter>
      </AIProviderProvider>
    </AuthProvider>
  );
}
