'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getProject, formatProjectPrice, formatArea, Project } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  'Under Construction': 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
  'Ready to Move': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  'New Launch': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  'Completed': 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300',
};

export default function ProjectDetailPage() {
  const { getValidToken } = useAuth();
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      const token = await getValidToken();
      if (!token) { router.replace('/login'); return; }
      setLoading(true);
      setError('');
      try {
        const data = await getProject(token, id);
        setProject(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load project');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, getValidToken, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] gap-4">
        <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400">Loading project...</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <p className="text-red-500">{error || 'Project not found'}</p>
        <button onClick={() => router.back()} className="px-4 py-2 bg-violet-600 text-white rounded-lg text-sm">← Go back</button>
      </div>
    );
  }

  const statusClass = STATUS_COLORS[project.project_status] ?? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400';

  const priceRange =
    project.price_min != null && project.price_max != null
      ? `${formatProjectPrice(project.price_min)} – ${formatProjectPrice(project.price_max)}`
      : project.price_min != null
      ? `From ${formatProjectPrice(project.price_min)}`
      : project.price_max != null
      ? `Up to ${formatProjectPrice(project.price_max)}`
      : null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <nav className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
        <button onClick={() => router.push('/projects')} className="hover:text-violet-600 dark:hover:text-violet-400">Projects</button>
        <span>/</span>
        <span className="text-gray-900 dark:text-gray-100 truncate max-w-xs">{project.apartment_name}</span>
      </nav>

      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
        <div className="h-2 bg-violet-500" />
        <div className="p-6 sm:p-8">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 mb-2">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{project.apartment_name}</h1>
              <p className="text-gray-500 dark:text-gray-400 text-sm">by {project.developer_name}</p>
              <p className="text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-1 text-sm">
                <span>📍</span> {project.locality}
              </p>
            </div>
            <span className={`text-sm px-3 py-1 rounded-full font-medium flex-shrink-0 ${statusClass}`}>
              {project.project_status}
            </span>
          </div>

          {/* Price */}
          {priceRange && (
            <div className="mb-6 p-4 bg-violet-50 dark:bg-violet-900/20 rounded-xl">
              <p className="text-xs text-violet-600 dark:text-violet-400 font-medium uppercase tracking-wider mb-1">
                Price Range (in crores)
              </p>
              <span className="text-3xl font-bold text-violet-700 dark:text-violet-400">{priceRange}</span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                ⚠️ Prices are in crores (₹ Cr), not rupees
              </p>
            </div>
          )}

          {/* Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Total Units', value: project.total_units?.toLocaleString('en-IN') ?? '—', icon: '🏘' },
              { label: 'Towers', value: project.total_towers ?? '—', icon: '🏢' },
              { label: 'Floors', value: project.total_floors ?? '—', icon: '⬆' },
              { label: 'Min Area', value: project.min_area_sqft ? formatArea(project.min_area_sqft) : '—', icon: '📐' },
              { label: 'Max Area', value: project.max_area_sqft ? formatArea(project.max_area_sqft) : '—', icon: '📏' },
              { label: 'Launch Date', value: project.launch_date ?? '—', icon: '📅' },
              { label: 'Possession', value: project.possession_date ?? '—', icon: '🗓' },
              { label: 'Listings', value: project.total_listings ?? '—', icon: '📋' },
            ].map(item => (
              <div key={item.label} className="bg-gray-50 dark:bg-gray-800 rounded-xl p-3">
                <p className="text-xs text-gray-400 dark:text-gray-500 mb-0.5">{item.icon} {item.label}</p>
                <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">{String(item.value)}</p>
              </div>
            ))}
          </div>

          {/* RERA */}
          {project.rera_number && (
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
              <p className="text-xs text-gray-400 dark:text-gray-500 mb-1">RERA Number</p>
              <p className="font-mono text-sm font-semibold text-gray-800 dark:text-gray-200">{project.rera_number}</p>
            </div>
          )}

          {/* Amenities */}
          {project.amenities && project.amenities.length > 0 && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Amenities</h2>
              <div className="flex flex-wrap gap-2">
                {project.amenities.map(a => (
                  <span
                    key={a}
                    className="px-3 py-1.5 text-sm bg-violet-50 dark:bg-violet-900/20 text-violet-700 dark:text-violet-300 rounded-full border border-violet-200 dark:border-violet-800"
                  >
                    {a}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Map coordinates */}
          {project.latitude && project.longitude && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Location</h2>
              <a
                href={`https://maps.google.com/?q=${project.latitude},${project.longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/20 transition-colors"
              >
                📍 View on Google Maps
              </a>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800 flex flex-wrap gap-x-6 gap-y-2 text-xs text-gray-400">
            <span>ID: <code className="font-mono">{project.project_id}</code></span>
            {project.project_url && (
              <a href={project.project_url} target="_blank" rel="noopener noreferrer" className="text-violet-500 hover:underline">
                View original project ↗
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
