/**
 * Project card component for displaying project info in history.
 */
import React from 'react';
import type { Project } from '../types';

interface ProjectCardProps {
  project: Project;
  onEdit?: (projectId: number) => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onEdit }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const getStatusColorLuxury = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          bg: 'rgba(16, 185, 129, 0.1)',
          border: 'rgba(16, 185, 129, 0.3)',
          text: 'var(--color-success)'
        };
      case 'in_progress':
        return {
          bg: 'rgba(102, 126, 234, 0.1)',
          border: 'rgba(102, 126, 234, 0.3)',
          text: 'var(--color-primary)'
        };
      case 'failed':
        return {
          bg: 'rgba(239, 68, 68, 0.1)',
          border: 'rgba(239, 68, 68, 0.3)',
          text: 'var(--color-error)'
        };
      default:
        return {
          bg: 'var(--color-glass)',
          border: 'var(--color-glass-border)',
          text: 'var(--color-text-tertiary)'
        };
    }
  };

  const statusStyle = getStatusColorLuxury(project.status);

  return (
    <div
      className="glass-card p-6 space-y-4 group"
      style={{
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        transition: 'var(--transition-default)'
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3
            className="text-lg font-semibold truncate"
            style={{
              color: 'var(--color-text)',
              fontFamily: 'var(--font-heading)'
            }}
          >
            {project.name}
          </h3>
          <p
            className="text-sm mt-1"
            style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}
          >
            {formatDate(project.created_at)}
          </p>
        </div>
        <span
          className="px-3 py-1 text-xs font-semibold rounded-full whitespace-nowrap"
          style={{
            background: statusStyle.bg,
            border: `1px solid ${statusStyle.border}`,
            color: statusStyle.text
          }}
        >
          {project.status.replace('_', ' ')}
        </span>
      </div>

      {/* Description */}
      {project.description && (
        <p
          className="text-sm line-clamp-2"
          style={{ color: 'var(--color-text-secondary)', lineHeight: 1.6 }}
        >
          {project.description}
        </p>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3 pt-3" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
        {project.github_repo_url && (
          <a
            href={project.github_repo_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 inline-flex items-center justify-center btn-glass focus-ring"
            style={{
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: 'var(--color-text)',
              padding: '0.625rem 1rem',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 600,
              borderRadius: 'var(--radius-md)',
              transition: 'var(--transition-default)',
              textDecoration: 'none'
            }}
          >
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            GitHub
          </a>
        )}

        {onEdit && (
          <button
            onClick={() => onEdit(project.id)}
            className="btn-gradient focus-ring"
            style={{
              background: 'var(--gradient-primary)',
              color: 'var(--color-text)',
              padding: '0.625rem 1rem',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 600,
              border: 'none',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              transition: 'var(--transition-default)'
            }}
          >
            Edit
          </button>
        )}
      </div>
    </div>
  );
};

export default ProjectCard;
