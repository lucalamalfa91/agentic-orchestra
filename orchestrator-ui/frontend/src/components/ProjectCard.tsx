/**
 * Project card component for displaying project info in history.
 */
import React, { useState } from 'react';
import type { Project } from '../types';
import { projectsApi } from '../api/client';

interface ProjectCardProps {
  project: Project;
  onEdit?: (projectId: number) => void;
  onViewProgress?: (projectId: string) => void;
  onStopGeneration?: (projectId: string) => void;
  onDelete?: (projectId: number) => void;
  onCardClick?: (project: Project) => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onEdit, onViewProgress, onStopGeneration, onDelete, onCardClick }) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      setIsDeleting(true);
      try {
        await fetch(`${(import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')}/api/projects/${project.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
          },
        });
        onDelete?.(project.id);
      } catch (err) {
        console.error('Failed to delete project:', err);
        alert('Failed to delete project');
      } finally {
        setIsDeleting(false);
      }
    }
  };
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
      className={`glass-card p-6 space-y-4 group project-card-luxury ${
        project.status === 'in_progress' ? 'cursor-pointer' : 'cursor-default'
      }`}
      style={{
        background: 'rgba(30, 25, 50, 0.6)',
        backdropFilter: 'blur(20px)',
        border: '1.5px solid rgba(102, 126, 234, 0.5)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(102, 126, 234, 0.25)'
      }}
      onClick={() => {
        if (project.status === 'in_progress' && onCardClick) {
          onCardClick(project);
        }
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(40, 30, 65, 0.7)';
        e.currentTarget.style.boxShadow = '0 12px 48px rgba(102, 126, 234, 0.4)';
        e.currentTarget.style.transform = 'translateY(-4px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'rgba(30, 25, 50, 0.6)';
        e.currentTarget.style.boxShadow = '0 8px 32px rgba(102, 126, 234, 0.25)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* Shimmer effect overlay on hover */}
      <div
        className="shimmer-overlay"
        style={{
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
          pointerEvents: 'none',
          zIndex: 1
        }}
      />
      {/* Header */}
      <div className="flex items-start justify-between gap-3" style={{ position: 'relative', zIndex: 2 }}>
        <div className="flex-1 min-w-0">
          <h3
            className="text-lg font-bold truncate"
            style={{
              color: '#ffffff',
              fontFamily: 'var(--font-heading)'
            }}
          >
            {project.name}
          </h3>
          <p
            className="text-sm mt-1"
            style={{
              color: 'rgba(224, 224, 255, 0.9)',
              fontSize: 'var(--font-size-sm)'
            }}
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
          style={{
            color: 'rgba(240, 240, 255, 0.85)',
            lineHeight: 1.6,
            position: 'relative',
            zIndex: 2
          }}
        >
          {project.description}
        </p>
      )}

      {/* Actions */}
      <div className="flex flex-col gap-3 pt-3" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', position: 'relative', zIndex: 2 }}>
        {/* Primary actions row */}
        <div className="flex items-center gap-3">
          {project.github_repo_url && (
            <a
              href={project.github_repo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 inline-flex items-center justify-center btn-glass focus-ring"
              style={{
                background: 'linear-gradient(135deg, rgba(50, 100, 200, 0.5), rgba(100, 50, 150, 0.4))',
                border: '1.5px solid rgba(102, 126, 234, 0.8)',
                color: '#ffffff',
                padding: '0.625rem 1rem',
                fontSize: 'var(--font-size-sm)',
                fontWeight: 600,
                borderRadius: 'var(--radius-md)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                textDecoration: 'none',
                boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(70, 120, 220, 0.7), rgba(120, 70, 180, 0.6))';
                e.currentTarget.style.boxShadow = '0 6px 25px rgba(102, 126, 234, 0.5)';
                e.currentTarget.style.transform = 'scale(1.05)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(50, 100, 200, 0.5), rgba(100, 50, 150, 0.4))';
                e.currentTarget.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.3)';
                e.currentTarget.style.transform = 'scale(1)';
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

        {/* Status-specific actions */}
        {project.status === 'in_progress' && (
          <div className="flex gap-3">
            <button
              onClick={() => onViewProgress?.(project.id.toString())}
              className="flex-1 px-3 py-2 text-xs font-semibold rounded-md"
              style={{
                background: 'rgba(59, 130, 246, 0.3)',
                border: '1px solid rgba(59, 130, 246, 0.5)',
                color: '#93c5fd',
                cursor: 'pointer',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(59, 130, 246, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(59, 130, 246, 0.3)';
              }}
            >
              View Progress
            </button>
            <button
              onClick={() => onStopGeneration?.(project.id.toString())}
              className="flex-1 px-3 py-2 text-xs font-semibold rounded-md"
              style={{
                background: 'rgba(234, 179, 8, 0.3)',
                border: '1px solid rgba(234, 179, 8, 0.5)',
                color: '#fcd34d',
                cursor: 'pointer',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(234, 179, 8, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(234, 179, 8, 0.3)';
              }}
            >
              Stop
            </button>
          </div>
        )}

        {project.status === 'failed' && (
          <div className="flex gap-3">
            <button
              onClick={async (e) => {
                e.stopPropagation();
                if (window.confirm('Resume this generation with the same requirements?')) {
                  try {
                    setIsDeleting(true);  // Reuse loading state
                    const response = await projectsApi.resumeGeneration(project.id);
                    // Notify parent to show progress viewer
                    onViewProgress?.(response.generation_id);
                  } catch (err) {
                    console.error('Failed to resume generation:', err);
                    alert('Failed to resume generation. Check console for details.');
                  } finally {
                    setIsDeleting(false);
                  }
                }
              }}
              className="flex-1 px-3 py-2 text-xs font-semibold rounded-md"
              style={{
                background: 'rgba(34, 197, 94, 0.3)',
                border: '1px solid rgba(34, 197, 94, 0.5)',
                color: '#86efac',
                cursor: 'pointer',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(34, 197, 94, 0.5)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(34, 197, 94, 0.3)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              ▶ Resume Generation
            </button>

            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="flex-1 px-3 py-2 text-xs font-semibold rounded-md"
              style={{
                background: 'rgba(239, 68, 68, 0.3)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
                color: '#fca5a5',
                cursor: isDeleting ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s',
                opacity: isDeleting ? 0.5 : 1
              }}
              onMouseEnter={(e) => {
                if (!isDeleting) {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.5)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isDeleting) {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.3)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              {isDeleting ? 'Processing...' : 'Delete'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectCard;
