import { useState } from 'react';
import { Button } from '../components/ui/button';

interface DeployAuthScreenProps {
  provider: string;
  onSuccess?: () => void;
}

export default function DeployAuthScreen({ provider, onSuccess }: DeployAuthScreenProps) {
  const [loading, setLoading] = useState(false);

  const handleAuthorize = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/auth/deploy/${provider}/login`);
      const data = await res.json();
      window.location.href = data.url;
    } catch (error) {
      console.error('Authorization failed:', error);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto text-center space-y-6">
      <h2 className="text-2xl font-bold">Authorize {provider}</h2>
      <p className="text-gray-600">
        {provider} authorization needed to auto-deploy your app
      </p>
      <Button onClick={handleAuthorize} disabled={loading} className="w-full">
        {loading ? 'Loading...' : `✓ Authorize ${provider}`}
      </Button>
    </div>
  );
}
