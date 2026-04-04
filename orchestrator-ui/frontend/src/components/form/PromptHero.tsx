import { Textarea } from '../ui/textarea';

export default function PromptHero({ value, onChange }: any) {
  return (
    <div className="space-y-2">
      <label className="text-lg font-bold">✨ What app do you want to build?</label>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Describe your app idea... e.g., 'Todo app with user authentication'"
        className="min-h-40 text-lg"
      />
      <p className="text-xs text-gray-500">{value.length} characters</p>
    </div>
  );
}
