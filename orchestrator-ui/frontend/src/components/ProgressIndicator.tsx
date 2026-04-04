/**
 * Progress indicator component showing 6-step generation process.
 */
import React from 'react';

interface ProgressIndicatorProps {
  currentStep: number;
  percentage: number;
  message: string;
}

const STEPS = [
  { number: 1, name: 'README', label: 'README Update' },
  { number: 2, name: 'Design', label: 'Design Phase' },
  { number: 3, name: 'Backend', label: 'Backend Code' },
  { number: 4, name: 'Frontend', label: 'Frontend Code' },
  { number: 5, name: 'DevOps', label: 'CI/CD Pipeline' },
  { number: 6, name: 'Publish', label: 'GitHub Publish' },
];

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  currentStep,
  percentage,
  message,
}) => {
  return (
    <div
      className="glass-card p-8 space-y-8 animate-scale-in"
      style={{
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: 'var(--shadow-xl)'
      }}
    >
      {/* Header */}
      <div className="text-center">
        <h2
          className="text-3xl font-bold mb-2"
          style={{
            fontFamily: 'var(--font-heading)',
            background: 'var(--gradient-primary)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}
        >
          Generating Your Application
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
          AI agents are working together to build your app
        </p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-3">
        <div className="flex justify-between text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          <span>Overall Progress</span>
          <span className="font-semibold" style={{ color: 'var(--color-text)' }}>{percentage}%</span>
        </div>
        <div
          className="w-full rounded-full h-4 overflow-hidden"
          style={{
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <div
            className="h-full transition-all duration-500 ease-out animate-pulse-glow"
            style={{
              width: `${percentage}%`,
              background: 'var(--gradient-primary)',
              boxShadow: '0 0 10px rgba(102, 126, 234, 0.5)'
            }}
          />
        </div>
      </div>

      {/* Step Indicators */}
      <div className="space-y-3">
        {STEPS.map((step, index) => {
          const isCompleted = step.number < currentStep;
          const isCurrent = step.number === currentStep;

          return (
            <div
              key={step.number}
              className="flex items-center space-x-4 p-4 rounded-lg transition-all duration-300 animate-slide-up"
              style={{
                background: isCurrent
                  ? 'rgba(102, 126, 234, 0.1)'
                  : isCompleted
                  ? 'rgba(16, 185, 129, 0.1)'
                  : 'rgba(255, 255, 255, 0.03)',
                border: isCurrent
                  ? '1px solid rgba(102, 126, 234, 0.3)'
                  : isCompleted
                  ? '1px solid rgba(16, 185, 129, 0.3)'
                  : '1px solid rgba(255, 255, 255, 0.05)',
                animationDelay: `${index * 0.1}s`
              }}
            >
              {/* Step Icon */}
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                  isCurrent ? 'animate-pulse' : ''
                }`}
                style={{
                  background: isCompleted
                    ? 'var(--color-success)'
                    : isCurrent
                    ? 'var(--gradient-primary)'
                    : 'rgba(255, 255, 255, 0.1)',
                  color: isCompleted || isCurrent ? 'var(--color-text)' : 'var(--color-text-tertiary)',
                  boxShadow: isCurrent ? 'var(--shadow-glow)' : 'none'
                }}
              >
                {isCompleted ? (
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  <span className="text-base">{step.number}</span>
                )}
              </div>

              {/* Step Label */}
              <div className="flex-1">
                <p
                  className="font-semibold text-base"
                  style={{
                    color: isCurrent
                      ? 'var(--color-text)'
                      : isCompleted
                      ? 'var(--color-success)'
                      : 'var(--color-text-secondary)'
                  }}
                >
                  {step.label}
                </p>
                <p
                  className="text-xs mt-0.5"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  {step.name}
                </p>
              </div>

              {/* Status Badge */}
              {isCurrent && (
                <span
                  className="px-3 py-1 text-xs font-semibold rounded-full"
                  style={{
                    background: 'var(--gradient-primary)',
                    color: 'var(--color-text)'
                  }}
                >
                  In Progress
                </span>
              )}
              {isCompleted && (
                <span
                  className="px-3 py-1 text-xs font-semibold rounded-full"
                  style={{
                    background: 'var(--color-success)',
                    color: 'var(--color-text)'
                  }}
                >
                  Complete
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Current Message */}
      <div
        className="p-5 rounded-lg"
        style={{
          background: 'rgba(102, 126, 234, 0.1)',
          border: '1px solid rgba(102, 126, 234, 0.3)'
        }}
      >
        <p
          className="text-sm flex items-start gap-3"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          <svg
            className="w-5 h-5 flex-shrink-0 mt-0.5 animate-pulse"
            fill="currentColor"
            viewBox="0 0 20 20"
            style={{ color: 'var(--color-primary)' }}
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <span>{message}</span>
        </p>
      </div>
    </div>
  );
};

export default ProgressIndicator;
