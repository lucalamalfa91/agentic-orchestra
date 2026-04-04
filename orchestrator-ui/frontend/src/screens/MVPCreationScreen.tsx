import { useState } from 'react';
import { Button } from '../components/ui/button';
import PromptHero from '../components/form/PromptHero';
import AdvancedSettings from '../components/form/AdvancedSettings';
import { useGeneration } from '../hooks/useGeneration';

export default function MVPCreationScreen() {
  const { startGeneration } = useGeneration();
  const [prompt, setPrompt] = useState('');
  const [techStack, setTechStack] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (prompt.length < 20) {
      setError('Prompt must be at least 20 characters');
      return;
    }

    setLoading(true);
    try {
      await startGeneration({
        mvp_description: prompt,
        tech_stack: Object.keys(techStack).length > 0 ? techStack : null,
        auto_decide: true
      });
    } catch (err: any) {
      setError(err.message || 'Generation failed');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="space-y-4">
        <PromptHero value={prompt} onChange={setPrompt} />
        <AdvancedSettings onTechStackChange={setTechStack} />
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <Button
        onClick={handleSubmit}
        disabled={loading || prompt.length < 20}
        className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 text-lg"
      >
        {loading ? '✨ Generating...' : '✨ Generate App'}
      </Button>
    </div>
  );
}
