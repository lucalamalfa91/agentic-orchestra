const API = (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api";

export async function getGitHubAuthUrl() {
  const res = await fetch(`${API}/auth/github/login`);
  return res.json();
}

export async function loginWithGhCLI() {
  const res = await fetch(`${API}/auth/github/login-with-gh`);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function getAIProviderConfig(userId: number) {
  const res = await fetch(`${API}/config/ai-provider?user_id=${userId}`);
  return res.json();
}

export async function saveAIProvider(userId: number, baseUrl: string, apiKey: string, provider: 'openai' | 'anthropic' | 'custom' = 'openai') {
  const res = await fetch(`${API}/config/ai-provider`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, base_url: baseUrl, api_key: apiKey, ai_provider: provider })
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}: Failed to save configuration`);
  }

  return res.json();
}

export async function testAIProvider(baseUrl: string, apiKey: string, provider: 'openai' | 'anthropic' | 'custom' = 'openai') {
  const res = await fetch(`${API}/config/ai-provider/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ base_url: baseUrl, api_key: apiKey, ai_provider: provider })
  });
  return res.json();
}

export async function testCurrentAIProvider(userId: number) {
  const res = await fetch(`${API}/config/ai-provider/test-current?user_id=${userId}`);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}: Failed to test configuration`);
  }
  return res.json();
}
