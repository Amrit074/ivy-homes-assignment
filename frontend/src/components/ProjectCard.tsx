import Link from 'next/link';
import { Project, formatProjectPrice, formatArea } from '@/lib/api';

interface ProjectCardProps {
  project: Project;
}

const STATUS_COLORS: Record<string, string> = {
  'Under Construction': 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
  'Ready to Move': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  'New Launch': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  'Completed': 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300',
};

export default function ProjectCard({ project }: ProjectCardProps) {
  const statusClass = STATUS_COLORS[project.project_status] ?? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400';

  const priceRange =
    project.price_min != null && project.price_max != null
      ? `${formatProjectPrice(project.price_min)} – ${formatProjectPrice(project.price_max)}`
      : project.price_min != null
      ? `From ${formatProjectPrice(project.price_min)}`
      : project.price_max != null
      ? `Up to ${formatProjectPrice(project.price_max)}`
      : null;

  const areaRange =
    project.min_area_sqft != null && project.max_area_sqft != null
      ? `${project.min_area_sqft.toLocaleString('en-IN')} – ${formatArea(project.max_area_sqft)}`
      : project.min_area_sqft != null
      ? `From ${formatArea(project.min_area_sqft)}`
      : null;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden hover:shadow-md transition-shadow group">
      {/* Accent */}
      <div className="h-1 bg-violet-500" />

      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm leading-tight truncate group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
              {project.apartment_name}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              by {project.developer_name}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              📍 {project.locality}
            </p>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${statusClass}`}>
            {project.project_status}
          </span>
        </div>

        {/* Price in Crores */}
        {priceRange && (
          <div className="mb-3">
            <span className="text-lg font-bold text-violet-700 dark:text-violet-400">{priceRange}</span>
            <span className="text-xs text-gray-400 ml-1">(in crores)</span>
          </div>
        )}

        {/* Stats */}
        <div className="flex flex-wrap gap-2 mb-3">
          {project.total_units != null && (
            <span className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
              🏘 {project.total_units.toLocaleString('en-IN')} Units
            </span>
          )}
          {project.total_towers != null && (
            <span className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
              🏢 {project.total_towers} Towers
            </span>
          )}
          {project.total_floors != null && (
            <span className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
              ⬆ {project.total_floors} Floors
            </span>
          )}
          {areaRange && (
            <span className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
              📐 {areaRange}
            </span>
          )}
        </div>

        {/* RERA + Possession */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3">
          {project.rera_number && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              RERA: <span className="font-mono font-medium">{project.rera_number}</span>
            </p>
          )}
          {project.possession_date && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Possession: <span className="font-medium">{project.possession_date}</span>
            </p>
          )}
          {project.total_listings != null && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {project.total_listings} listing{project.total_listings !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        {/* Amenities preview */}
        {project.amenities && project.amenities.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {project.amenities.slice(0, 4).map((a) => (
              <span key={a} className="text-xs bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-300 px-2 py-0.5 rounded-full">
                {a}
              </span>
            ))}
            {project.amenities.length > 4 && (
              <span className="text-xs text-gray-400 dark:text-gray-500 px-1">+{project.amenities.length - 4} more</span>
            )}
          </div>
        )}

        {/* View Link */}
        <Link
          href={`/projects/${project.project_id}`}
          className="flex items-center justify-center w-full py-2 text-sm font-medium text-violet-600 dark:text-violet-400 border border-violet-200 dark:border-violet-800 rounded-lg hover:bg-violet-50 dark:hover:bg-violet-900/20 transition-colors"
        >
          View Project →
        </Link>
      </div>
    </div>
  );
}
