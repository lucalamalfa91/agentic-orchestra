import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { saveAIProvider, testAIProvider } from '../lib/api/auth';
import { useAuth } from '../hooks/useAuth';

export default function AIProviderSetup() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [baseUrl, setBaseUrl] = useState('https://api.openai.com/v1');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleTest = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await testAIProvider(baseUrl, apiKey);
      setMessage(res.success ? '✓ Connection successful!' : '✗ Connection failed');
    } catch {
      setMessage('✗ Error testing connection');
    }
    setLoading(false);
  };

  const handleSave = async () => {
    if (!user?.id) {
      setMessage('✗ User not authenticated');
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      await saveAIProvider(user.id, baseUrl, apiKey);
      navigate('/');
    } catch {
      setMessage('✗ Error saving configuration');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 max-w-md w-full">
        <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Configure AI Provider</h1>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Base URL</label>
            <Input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.openai.com/v1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">API Key</label>
            <div className="flex gap-2">
              <Input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                className="flex-1"
              />
              <Button
                variant="outline"
                onClick={() => setShowKey(!showKey)}
                className="px-4"
              >
                {showKey ? 'Hide' : 'Show'}
              </Button>
            </div>
          </div>

          {message && (
            <p className={`text-sm ${message.startsWith('✓') ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {message}
            </p>
          )}

          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              onClick={handleTest}
              disabled={loading || !baseUrl || !apiKey}
            >
              Test
            </Button>
            <Button
              onClick={handleSave}
              disabled={loading || !baseUrl || !apiKey}
              className="flex-1"
            >
              Save & Continue
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
