import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function OAuthCallback() {
  const navigate = useNavigate();
  const { setToken } = useAuth();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (!code) {
      setError('Missing OAuth code');
      return;
    }

    async function handleCallback() {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/github/callback?code=${code}`);
        const data = await res.json();

        if (data.token) {
          localStorage.setItem('jwt_token', data.token);
          setToken(data.token);
          navigate('/provider-setup');
        } else {
          setError('Failed to authenticate');
        }
      } catch (err) {
        setError('Error during authentication');
      }
    }

    handleCallback();
  }, [searchParams, setToken, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        {error ? (
          <>
            <p className="text-red-600 mb-4">{error}</p>
            <button onClick={() => window.location.href = '/auth'}>
              Back to login
            </button>
          </>
        ) : (
          <p className="text-gray-600">Authenticating...</p>
        )}
      </div>
    </div>
  );
}
