import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { getGitHubAuthUrl } from '../lib/api/auth';
import { useAuth } from '../hooks/useAuth';

export default function AuthScreen() {
  const navigate = useNavigate();
  const { token, setToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [useGhCli, setUseGhCli] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) navigate('/');
  }, [token, navigate]);

  const handleGitHubLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getGitHubAuthUrl();

      if (data.use_gh_cli) {
        // GITHUB_CLIENT_ID not configured, use gh CLI instead
        setUseGhCli(true);
      } else if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      setError('Failed to initiate login');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGhCliLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8000/api/auth/github/login-with-gh');
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'gh CLI authentication failed');
      }
      const { token: jwt_token } = await response.json();
      setToken(jwt_token);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Failed to authenticate with gh CLI');
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

        {useGhCli ? (
          <>
            <p className="text-sm text-gray-600 mb-4">
              Using your existing gh CLI authentication ({useGhCli ? '✓' : ''})
            </p>
            <Button
              onClick={handleGhCliLogin}
              disabled={loading}
              className="w-full bg-green-600 text-white hover:bg-green-700"
            >
              {loading ? 'Authenticating...' : '✓ Login with gh CLI'}
            </Button>
            <button
              onClick={() => {
                setUseGhCli(false);
                setError('');
              }}
              className="text-xs text-blue-600 hover:underline mt-2 w-full"
            >
              Use OAuth instead
            </button>
          </>
        ) : (
          <>
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
          </>
        )}
      </div>
    </div>
  );
}
