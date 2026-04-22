import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { saveAIProvider, testAIProvider, getAIProviderConfig, testCurrentAIProvider } from '../lib/api/auth';
import { useAuth } from '../hooks/useAuth';

export default function AIProviderSetup() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [provider, setProvider] = useState<'openai' | 'anthropic' | 'custom'>('anthropic');
  const [baseUrl, setBaseUrl] = useState('https://api.anthropic.com');
  const [apiKey, setApiKey] = useState('');
  const [aiModel, setAiModel] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [hasExistingConfig, setHasExistingConfig] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);

  const ANTHROPIC_MODELS = [
    { value: 'claude-sonnet-4-6',          label: 'Claude Sonnet 4.6 (Recommended)' },
    { value: 'claude-opus-4-7',            label: 'Claude Opus 4.7' },
    { value: 'claude-haiku-4-5-20251001',  label: 'Claude Haiku 4.5 (Fast)' },
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
    { value: 'claude-3-5-haiku-20241022',  label: 'Claude 3.5 Haiku' },
  ];

  const OPENAI_MODELS = [
    { value: 'gpt-4o',       label: 'GPT-4o (Recommended)' },
    { value: 'gpt-4o-mini',  label: 'GPT-4o Mini (Fast)' },
    { value: 'gpt-4-turbo',  label: 'GPT-4 Turbo' },
    { value: 'o1',           label: 'o1' },
    { value: 'o3-mini',      label: 'o3-mini' },
  ];

  const modelOptions = provider === 'anthropic' ? ANTHROPIC_MODELS : provider === 'openai' ? OPENAI_MODELS : [];

  // Load existing configuration on mount
  useEffect(() => {
    console.log('[Settings] User object:', user);
    console.log('[Settings] User ID:', user?.id);

    if (user?.id) {
      loadExistingConfig();
    } else {
      console.warn('[Settings] No user ID found - cannot load config');
    }
  }, [user?.id]);

  const loadExistingConfig = async () => {
    if (!user?.id) return;

    try {
      const config = await getAIProviderConfig(user.id);
      if (config.configured && config.base_url) {
        setHasExistingConfig(true);
        setBaseUrl(config.base_url);

        // Detect provider from base_url or use returned ai_provider
        const detectedProvider = config.ai_provider || detectProviderFromUrl(config.base_url);
        setProvider(detectedProvider as 'openai' | 'anthropic' | 'custom');

        if (config.ai_model) setAiModel(config.ai_model);

        // Test existing configuration automatically
        setIsTestingConnection(true);
        setMessage('Testing saved configuration...');

        try {
          const testResult = await testCurrentAIProvider(user.id);
          if (testResult.success) {
            setMessage(`✓ Saved configuration is working! Provider: ${testResult.provider}, URL: ${testResult.base_url}`);
          } else {
            setMessage(`⚠ Saved configuration has issues: ${testResult.message}. Please update your settings.`);
          }
        } catch (error) {
          console.error('Failed to test current config:', error);
          setMessage('⚠ Could not test saved configuration. You may need to update your API key.');
        } finally {
          setIsTestingConnection(false);
        }
      }
    } catch (error) {
      console.error('Failed to load existing config:', error);
    }
  };

  const detectProviderFromUrl = (url: string): string => {
    if (url.includes('anthropic.com')) return 'anthropic';
    if (url.includes('openai.com')) return 'openai';
    return 'custom';
  };

  // Update base URL when provider changes
  const handleProviderChange = (newProvider: 'openai' | 'anthropic' | 'custom') => {
    setProvider(newProvider);
    setAiModel(''); // reset model when switching provider
    if (newProvider === 'anthropic') {
      setBaseUrl('https://api.anthropic.com');
    } else if (newProvider === 'openai') {
      setBaseUrl('https://api.openai.com/v1');
    } else {
      setBaseUrl('');
    }
  };

  const handleTest = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await testAIProvider(baseUrl, apiKey, provider, aiModel);
      setMessage(res.success ? res.message || '✓ Connection successful!' : `✗ ${res.message || 'Connection failed'}`);
    } catch (error) {
      setMessage(`✗ Error testing connection: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    setLoading(false);
  };

  const handleSave = async () => {
    if (!user?.id) {
      setMessage('✗ User not authenticated');
      return;
    }

    if (!baseUrl || !apiKey) {
      setMessage('✗ Please fill in all required fields');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      console.log('Saving AI provider config:', { provider, baseUrl: baseUrl.substring(0, 30), hasKey: !!apiKey, aiModel });
      const result = await saveAIProvider(user.id, baseUrl, apiKey, provider, aiModel);
      console.log('Save result:', result);

      setMessage('✓ Configuration saved successfully!');
      setHasExistingConfig(true);

      // Navigate after short delay to show success message
      setTimeout(() => navigate('/'), 1500);
    } catch (error) {
      console.error('Save failed:', error);
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      setMessage(`✗ Failed to save: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
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
          {/* Existing Configuration Status */}
          {hasExistingConfig && (
            <div
              className="p-4 rounded-lg border animate-slide-up"
              style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: 'var(--color-success)'
              }}
            >
              <div className="flex items-start gap-3">
                <div className="text-xl">✓</div>
                <div>
                  <div className="font-semibold mb-1">Active Configuration Found</div>
                  <div className="text-sm opacity-90">
                    You already have an AI provider configured. Update the fields below to modify your configuration.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Provider Selection */}
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              AI Provider
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                onClick={() => handleProviderChange('anthropic')}
                className="p-3 rounded-lg transition-all focus-ring"
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
                  <div className="text-sm">Anthropic</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
                    Claude
                  </div>
                </div>
              </button>
              <button
                onClick={() => handleProviderChange('openai')}
                className="p-3 rounded-lg transition-all focus-ring"
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
                  <div className="text-sm">OpenAI</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
                    GPT
                  </div>
                </div>
              </button>
              <button
                onClick={() => handleProviderChange('custom')}
                className="p-3 rounded-lg transition-all focus-ring"
                style={{
                  background: provider === 'custom' ? 'var(--gradient-primary)' : 'rgba(255, 255, 255, 0.05)',
                  border: `1px solid ${provider === 'custom' ? 'rgba(102, 126, 234, 0.5)' : 'rgba(255, 255, 255, 0.2)'}`,
                  color: 'var(--color-text)',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <div className="text-center">
                  <div className="text-lg mb-1">🔌</div>
                  <div className="text-sm">Custom</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
                    Hub/Proxy
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
              {provider === 'custom' && (
                <span className="ml-2 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                  (e.g., LiteLLM proxy, Adesso Hub)
                </span>
              )}
            </label>
            <Input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder={
                provider === 'anthropic'
                  ? 'https://api.anthropic.com'
                  : provider === 'openai'
                  ? 'https://api.openai.com/v1'
                  : 'https://your-proxy.com/v1'
              }
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
            {provider === 'custom' && (
              <p className="text-xs mt-2" style={{ color: 'var(--color-text-tertiary)' }}>
                💡 Enter the base URL of your AI hub/proxy (LiteLLM, Adesso, etc.)
              </p>
            )}
          </div>

          {/* API Key Input */}
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              API Key
              {provider === 'anthropic' && (
                <span className="ml-2 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                  (starts with sk-ant-...)
                </span>
              )}
            </label>
            <div className="flex gap-2">
              <Input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={
                  provider === 'anthropic'
                    ? 'sk-ant-api-...'
                    : provider === 'openai'
                    ? 'sk-...'
                    : 'Your hub token'
                }
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

          {/* Model Selection (shown only for anthropic/openai) */}
          {modelOptions.length > 0 && (
            <div>
              <label
                className="block text-sm font-medium mb-2"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                Model
                <span className="ml-2 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                  (optional — leave blank to use default)
                </span>
              </label>
              <select
                value={aiModel}
                onChange={(e) => setAiModel(e.target.value)}
                className="w-full focus-ring"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  color: aiModel ? 'var(--color-text)' : 'var(--color-text-tertiary)',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--font-size-base)',
                  appearance: 'none',
                  cursor: 'pointer',
                }}
              >
                <option value="" style={{ background: '#1a1a2e', color: '#ccc' }}>
                  — Use provider default —
                </option>
                {modelOptions.map((m) => (
                  <option key={m.value} value={m.value} style={{ background: '#1a1a2e', color: '#fff' }}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
          )}

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
