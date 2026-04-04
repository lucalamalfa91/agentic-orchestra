import { useState } from 'react';

interface TechStackSelectorProps {
  onChange: (value: any) => void;
}

interface TechOption {
  value: string;
  label: string;
  icon?: string;
}

const techOptions = {
  frontend: [
    { value: 'react', label: 'React', icon: '⚛️' },
    { value: 'vue', label: 'Vue', icon: '💚' },
    { value: 'angular', label: 'Angular', icon: '🅰️' },
  ],
  backend: [
    { value: 'dotnet', label: '.NET', icon: '🔷' },
    { value: 'node', label: 'Node.js', icon: '🟢' },
    { value: 'python', label: 'Python', icon: '🐍' },
  ],
  database: [
    { value: 'postgresql', label: 'PostgreSQL', icon: '🐘' },
    { value: 'mysql', label: 'MySQL', icon: '🐬' },
    { value: 'mongodb', label: 'MongoDB', icon: '🍃' },
  ],
  deploy: [
    { value: 'vercel', label: 'Vercel', icon: '▲' },
    { value: 'railway', label: 'Railway', icon: '🚂' },
    { value: 'render', label: 'Render', icon: '🎨' },
  ],
};

export default function TechStackSelector({ onChange }: TechStackSelectorProps) {
  const [selected, setSelected] = useState({
    frontend: 'react',
    backend: 'dotnet',
    database: 'postgresql',
    deploy: 'vercel',
  });

  const handleSelect = (category: keyof typeof selected, value: string) => {
    const newSelected = { ...selected, [category]: value };
    setSelected(newSelected);
    onChange({ [category]: value });
  };

  const renderTechButton = (category: keyof typeof selected, option: TechOption) => {
    const isSelected = selected[category] === option.value;

    return (
      <button
        key={option.value}
        type="button"
        onClick={() => handleSelect(category, option.value)}
        data-selected={isSelected}
        className="tech-option-button focus-ring"
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-sm)',
          padding: 'var(--spacing-md)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid',
          borderColor: isSelected ? 'var(--color-primary)' : 'var(--color-glass-border)',
          background: isSelected
            ? 'var(--gradient-primary)'
            : 'rgba(255, 255, 255, 0.03)',
          color: 'var(--color-text)',
          fontSize: 'var(--font-size-sm)',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'var(--transition-default)',
          minHeight: '44px',
          width: '100%',
          textAlign: 'left',
          overflow: 'hidden',
        }}
      >
        {/* Icon */}
        {option.icon && (
          <span style={{ fontSize: '1.25rem', lineHeight: 1 }}>{option.icon}</span>
        )}

        {/* Label */}
        <span style={{ flex: 1 }}>{option.label}</span>

        {/* Check icon for selected state */}
        {isSelected && (
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            style={{ flexShrink: 0 }}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2.5}
              d="M5 13l4 4L19 7"
            />
          </svg>
        )}
      </button>
    );
  };

  return (
    <div className="space-y-6">
      {/* Frontend */}
      <div>
        <label
          className="block text-sm font-semibold mb-3"
          style={{
            color: 'var(--color-text-secondary)',
            fontFamily: 'var(--font-heading)',
          }}
        >
          Frontend Framework
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {techOptions.frontend.map((option) =>
            renderTechButton('frontend', option)
          )}
        </div>
      </div>

      {/* Backend */}
      <div>
        <label
          className="block text-sm font-semibold mb-3"
          style={{
            color: 'var(--color-text-secondary)',
            fontFamily: 'var(--font-heading)',
          }}
        >
          Backend Framework
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {techOptions.backend.map((option) =>
            renderTechButton('backend', option)
          )}
        </div>
      </div>

      {/* Database */}
      <div>
        <label
          className="block text-sm font-semibold mb-3"
          style={{
            color: 'var(--color-text-secondary)',
            fontFamily: 'var(--font-heading)',
          }}
        >
          Database
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {techOptions.database.map((option) =>
            renderTechButton('database', option)
          )}
        </div>
      </div>

      {/* Deploy */}
      <div>
        <label
          className="block text-sm font-semibold mb-3"
          style={{
            color: 'var(--color-text-secondary)',
            fontFamily: 'var(--font-heading)',
          }}
        >
          Deployment Platform
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {techOptions.deploy.map((option) =>
            renderTechButton('deploy', option)
          )}
        </div>
      </div>
    </div>
  );
}
