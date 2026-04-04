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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Generation Progress</h2>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
          <span>Progress</span>
          <span>{percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-purple-500 to-purple-600 h-full transition-all duration-500 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Step Indicators */}
      <div className="space-y-3">
        {STEPS.map((step) => {
          const isCompleted = step.number < currentStep;
          const isCurrent = step.number === currentStep;

          return (
            <div
              key={step.number}
              className={`flex items-center space-x-3 p-3 rounded-md transition-colors ${
                isCurrent
                  ? 'bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700'
                  : isCompleted
                  ? 'bg-green-50 dark:bg-green-900/20'
                  : 'bg-gray-50 dark:bg-gray-700/50'
              }`}
            >
              {/* Step Icon */}
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
                  isCompleted
                    ? 'bg-green-500 text-white'
                    : isCurrent
                    ? 'bg-purple-600 text-white animate-pulse'
                    : 'bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400'
                }`}
              >
                {isCompleted ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  <span className="text-sm">{step.number}</span>
                )}
              </div>

              {/* Step Label */}
              <div className="flex-1">
                <p
                  className={`font-medium ${
                    isCurrent
                      ? 'text-purple-900 dark:text-purple-100'
                      : isCompleted
                      ? 'text-green-900 dark:text-green-100'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {step.label}
                </p>
              </div>

              {/* Status Badge */}
              {isCurrent && (
                <span className="px-2 py-1 text-xs font-medium bg-purple-600 text-white rounded-full">
                  In Progress
                </span>
              )}
              {isCompleted && (
                <span className="px-2 py-1 text-xs font-medium bg-green-600 text-white rounded-full">
                  Done
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Current Message */}
      <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-md">
        <p className="text-sm text-blue-900 dark:text-blue-100 flex items-start">
          <svg
            className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
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
