import { Textarea } from '../ui/textarea';

export default function PromptHero({ value, onChange }: any) {
  return (
    <div className="space-y-3">
      <label
        className="text-xl font-bold block"
        style={{
          fontFamily: 'var(--font-heading)',
          color: 'var(--color-text)',
          fontSize: 'var(--font-size-xl)'
        }}
      >
        What app do you want to build?
      </label>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Describe your app idea in detail... For example: 'A task management app with user authentication, real-time collaboration, email notifications, and mobile responsive design'"
        className="input-glass min-h-48 text-lg focus-ring resize-y"
        style={{
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem',
          color: 'var(--color-text)',
          fontSize: 'var(--font-size-lg)',
          lineHeight: 1.6,
          transition: 'var(--transition-default)'
        }}
      />
      <div className="flex items-center justify-between">
        <p
          className="text-sm"
          style={{
            color: value.length >= 20 ? 'var(--color-success)' : 'var(--color-text-tertiary)',
            fontSize: 'var(--font-size-sm)'
          }}
        >
          {value.length} characters {value.length < 20 && `(${20 - value.length} more needed)`}
        </p>
        {value.length >= 20 && (
          <span
            className="text-sm flex items-center gap-1"
            style={{ color: 'var(--color-success)' }}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Ready
          </span>
        )}
      </div>
    </div>
  );
}
