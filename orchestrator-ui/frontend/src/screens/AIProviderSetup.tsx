import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { saveAIProvider, testAIProvider } from '../lib/api/auth';
import { useAuth } from '../hooks/useAuth';

export default function AIProviderSetup() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [provider, setProvider] = useState<'openai' | 'anthropic'>('anthropic');
  const [baseUrl, setBaseUrl] = useState('https://api.anthropic.com');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Update base URL when provider changes
  const handleProviderChange = (newProvider: 'openai' | 'anthropic') => {
    setProvider(newProvider);
    if (newProvider === 'anthropic') {
      setBaseUrl('https://api.anthropic.com');
    } else {
      setBaseUrl('https://api.openai.com/v1');
    }
  };

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
      await saveAIProvider(user.id, baseUrl, apiKey, provider);
      setMessage('✓ Configuration saved successfully!');
      setTimeout(() => navigate('/'), 1000);
    } catch {
      setMessage('✗ Error saving configuration');
    }
    setLoading(false);
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center animate-fade-in"
      style={{
        background: 'var(--color-background)',
        position: 'relative'
      }}
    >
      {/* Background Gradient Overlay */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'radial-gradient(circle at 30% 20%, rgba(102, 126, 234, 0.1) 0%, transparent 50%)',
        opacity: 0.3
      }} />

      {/* Glass Card */}
      <div
        className="glass-card p-10 max-w-lg w-full mx-4 animate-scale-in"
        style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: 'var(--shadow-xl)',
          position: 'relative',
          zIndex: 10
        }}
      >
        {/* Title */}
        <div className="text-center mb-8">
          <h1
            className="text-3xl font-bold mb-3"
            style={{
              fontFamily: 'var(--font-heading)',
              color: 'var(--color-text)'
            }}
          >
            Configure AI Provider
          </h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            Connect your AI provider to start generating MVPs
          </p>
        </div>

        <div className="space-y-6">
          {/* AI Provider Selection */}
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              AI Provider
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handleProviderChange('anthropic')}
                className="p-4 rounded-lg transition-all focus-ring"
                style={{
                  background: provider === 'anthropic' ? 'var(--gradient-primary)' : 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${provider === 'anthropic' ? 'rgba(102, 126, 234, 0.5)' : 'rgba(255, 255, 255, 0.2)'}`,
                  color: 'var(--color-text)',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <div className="text-center">
                  <div className="text-lg mb-1">🤖</div>
                  <div>Anthropic</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
                    Claude API
                  </div>
                </div>
              </button>
              <button
                onClick={() => handleProviderChange('openai')}
                className="p-4 rounded-lg transition-all focus-ring"
                style={{
                  background: provider === 'openai' ? 'var(--gradient-primary)' : 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${provider === 'openai' ? 'rgba(102, 126, 234, 0.5)' : 'rgba(255, 255, 255, 0.2)'}`,
                  color: 'var(--color-text)',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <div className="text-center">
                  <div className="text-lg mb-1">✨</div>
                  <div>OpenAI</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
                    GPT API
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Base URL Input */}
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              Base URL
            </label>
            <Input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.openai.com/v1"
              className="input-glass w-full focus-ring"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'var(--color-text)',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)'
              }}
            />
          </div>

          {/* API Key Input */}
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              API Key
            </label>
            <div className="flex gap-2">
              <Input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                className="input-glass flex-1 focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  color: 'var(--color-text)',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--font-size-base)'
                }}
              />
              <Button
                variant="outline"
                onClick={() => setShowKey(!showKey)}
                className="btn-glass focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  color: 'var(--color-text)',
                  padding: '0 1.5rem',
                  minWidth: '80px'
                }}
              >
                {showKey ? 'Hide' : 'Show'}
              </Button>
            </div>
          </div>

          {/* Status Message */}
          {message && (
            <div
              className="p-4 rounded-lg text-sm animate-slide-up"
              style={{
                background: message.startsWith('✓')
                  ? 'rgba(16, 185, 129, 0.1)'
                  : 'rgba(239, 68, 68, 0.1)',
                border: message.startsWith('✓')
                  ? '1px solid rgba(16, 185, 129, 0.3)'
                  : '1px solid rgba(239, 68, 68, 0.3)',
                color: message.startsWith('✓') ? 'var(--color-success)' : 'var(--color-error)'
              }}
            >
              {message}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="outline"
              onClick={handleTest}
              disabled={loading || !baseUrl || !apiKey}
              className="btn-glass focus-ring flex-1"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'var(--color-text)',
                padding: '0.875rem 1.5rem',
                fontWeight: 600,
                opacity: loading || !baseUrl || !apiKey ? 0.5 : 1,
                cursor: loading || !baseUrl || !apiKey ? 'not-allowed' : 'pointer'
              }}
            >
              Test Connection
            </Button>
            <Button
              onClick={handleSave}
              disabled={loading || !baseUrl || !apiKey}
              className="btn-gradient focus-ring flex-1"
              style={{
                background: loading || !baseUrl || !apiKey ? 'var(--color-glass)' : 'var(--gradient-primary)',
                color: 'var(--color-text)',
                padding: '0.875rem 1.5rem',
                fontWeight: 600,
                border: 'none',
                boxShadow: loading || !baseUrl || !apiKey ? 'none' : 'var(--shadow-glow)',
                opacity: loading || !baseUrl || !apiKey ? 0.5 : 1,
                cursor: loading || !baseUrl || !apiKey ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Saving...' : 'Save & Continue'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
