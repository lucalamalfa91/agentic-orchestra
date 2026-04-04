import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { getGitHubAuthUrl } from '../lib/api/auth';
import { useAuth } from '../hooks/useAuth';

export default function AuthScreen() {
  const navigate = useNavigate();
  const { token } = useAuth();
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
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError('GitHub OAuth not configured. Please set GITHUB_CLIENT_ID in .env');
      }
    } catch (err) {
      setError('Failed to initiate login');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-blue-500">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-center mb-4">🤖 Agentic Orchestra</h1>
        <p className="text-gray-600 text-center mb-6">
          Connect with GitHub to generate amazing apps
        </p>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        <Button
          onClick={handleGitHubLogin}
          disabled={loading}
          className="w-full bg-black text-white hover:bg-gray-800"
        >
          {loading ? '...' : '✓ Connect GitHub'}
        </Button>

        <p className="text-xs text-gray-400 text-center mt-4">
          We'll authenticate with GitHub to publish your apps
        </p>
      </div>
    </div>
  );
}
