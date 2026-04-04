/**
 * Form component for configuring app generation.
 */
import React, { useState } from 'react';
import type { FormData } from '../types';

interface GenerationFormProps {
  onSubmit: (data: FormData) => void;
  isGenerating: boolean;
  initialData?: Partial<FormData>;
}

const GenerationForm: React.FC<GenerationFormProps> = ({
  onSubmit,
  isGenerating,
  initialData,
}) => {
  const [formData, setFormData] = useState<FormData>({
    mvp_description: initialData?.mvp_description || '',
    features: initialData?.features || '',
    user_stories: initialData?.user_stories || '',
    frontend: initialData?.frontend || 'react',
    backend: initialData?.backend || 'dotnet',
    database: initialData?.database || 'none',
    deploy_platform: initialData?.deploy_platform || 'vercel',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.mvp_description || formData.mvp_description.trim().length < 10) {
      newErrors.mvp_description = 'MVP description must be at least 10 characters';
    }

    if (!formData.features || formData.features.trim().length === 0) {
      newErrors.features = 'At least one feature is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Configure Your App</h2>

      {/* MVP Description */}
      <div>
        <label htmlFor="mvp_description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          MVP Description *
        </label>
        <textarea
          id="mvp_description"
          value={formData.mvp_description}
          onChange={(e) => handleChange('mvp_description', e.target.value)}
          rows={3}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white ${
            errors.mvp_description ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
          }`}
          placeholder="Describe your application in one or two sentences..."
          disabled={isGenerating}
        />
        {errors.mvp_description && (
          <p className="mt-1 text-sm text-red-600">{errors.mvp_description}</p>
        )}
      </div>

      {/* Features */}
      <div>
        <label htmlFor="features" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Features * <span className="text-xs text-gray-500">(one per line)</span>
        </label>
        <textarea
          id="features"
          value={formData.features}
          onChange={(e) => handleChange('features', e.target.value)}
          rows={5}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white ${
            errors.features ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
          }`}
          placeholder="User authentication&#10;Dashboard with analytics&#10;Real-time notifications&#10;..."
          disabled={isGenerating}
        />
        {errors.features && (
          <p className="mt-1 text-sm text-red-600">{errors.features}</p>
        )}
      </div>

      {/* User Stories (Optional) */}
      <div>
        <label htmlFor="user_stories" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          User Stories <span className="text-xs text-gray-500">(optional, one per line)</span>
        </label>
        <textarea
          id="user_stories"
          value={formData.user_stories}
          onChange={(e) => handleChange('user_stories', e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
          placeholder="As a user, I want to log in so that I can access my data&#10;As an admin, I want to view analytics..."
          disabled={isGenerating}
        />
      </div>

      {/* Tech Stack */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Frontend */}
        <div>
          <label htmlFor="frontend" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Frontend Framework
          </label>
          <select
            id="frontend"
            value={formData.frontend}
            onChange={(e) => handleChange('frontend', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
            disabled={isGenerating}
          >
            <option value="react">React</option>
            <option value="vue">Vue</option>
            <option value="angular">Angular</option>
          </select>
        </div>

        {/* Backend */}
        <div>
          <label htmlFor="backend" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Backend Framework
          </label>
          <select
            id="backend"
            value={formData.backend}
            onChange={(e) => handleChange('backend', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
            disabled={isGenerating}
          >
            <option value="dotnet">.NET</option>
            <option value="node">Node.js</option>
            <option value="python">Python</option>
            <option value="none">None (static site)</option>
          </select>
        </div>

        {/* Database */}
        <div>
          <label htmlFor="database" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Database
          </label>
          <select
            id="database"
            value={formData.database}
            onChange={(e) => handleChange('database', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
            disabled={isGenerating}
          >
            <option value="postgresql">PostgreSQL</option>
            <option value="mysql">MySQL</option>
            <option value="mongodb">MongoDB</option>
            <option value="none">None</option>
          </select>
        </div>

        {/* Deploy Platform */}
        <div>
          <label htmlFor="deploy_platform" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Deployment Platform
          </label>
          <select
            id="deploy_platform"
            value={formData.deploy_platform}
            onChange={(e) => handleChange('deploy_platform', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
            disabled={isGenerating}
          >
            <option value="vercel">Vercel (FREE)</option>
            <option value="railway">Railway ($5 credit/month)</option>
            <option value="render">Render (FREE with cold starts)</option>
            <option value="github-pages">GitHub Pages (static only)</option>
            <option value="azure-free">Azure Free Tier</option>
          </select>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isGenerating}
        className={`w-full py-3 px-4 rounded-md font-semibold text-white transition-colors ${
          isGenerating
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500'
        }`}
      >
        {isGenerating ? 'Generating...' : 'Generate App'}
      </button>
    </form>
  );
};

export default GenerationForm;
