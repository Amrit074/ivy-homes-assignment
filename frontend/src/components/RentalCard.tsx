import Link from 'next/link';
import { Rental, formatPrice, formatArea, formatDate } from '@/lib/api';

interface RentalCardProps {
  rental: Rental;
}

export default function RentalCard({ rental }: RentalCardProps) {
  const rentDisplay = rental.price > 0 ? formatPrice(rental.price) : 'Rent on request';
  const depositDisplay = rental.deposit && rental.deposit > 0 ? formatPrice(rental.deposit) : null;
  const areaDisplay = rental.carpet_area > 0 ? formatArea(rental.carpet_area) : null;

  const furnishingColor: Record<string, string> = {
    Furnished: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    'Semi-Furnished': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
    Unfurnished: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
  };
  const furnishingClass = furnishingColor[rental.furnishing] ?? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400';

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden hover:shadow-md transition-shadow group">
      {/* Accent band */}
      <div className="h-1 bg-emerald-500" />

      <div className="p-4">
        {/* Header */}
        <div className="mb-2">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm leading-tight truncate group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
            {rental.apartment_name || rental.title || 'Rental Property'}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
            📍 {rental.locality}
          </p>
        </div>

        {/* Rent & Deposit */}
        <div className="mb-3">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="text-lg font-bold text-emerald-700 dark:text-emerald-400">{rentDisplay}</span>
            <span className="text-xs text-gray-400 dark:text-gray-500">/month</span>
          </div>
          {depositDisplay && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Deposit: <span className="font-medium">{depositDisplay}</span>
            </p>
          )}
          {rental.maintenance && rental.maintenance > 0 && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Maintenance: <span className="font-medium">{formatPrice(rental.maintenance)}/mo</span>
            </p>
          )}
        </div>

        {/* Specs */}
        <div className="flex flex-wrap gap-2 mb-3">
          <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
            🛏 {rental.bedroom} BHK
          </span>
          <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
            🚿 {rental.bathroom} Bath
          </span>
          {areaDisplay && (
            <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
              📐 {areaDisplay}
            </span>
          )}
          {rental.floor != null && (
            <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
              🏢 Floor {rental.floor}
            </span>
          )}
        </div>

        {/* Furnishing + Date */}
        <div className="flex items-center justify-between mb-2">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${furnishingClass}`}>
            {rental.furnishing}
          </span>
          <span className="text-xs text-gray-400 dark:text-gray-500">{formatDate(rental.posted_at)}</span>
        </div>

        {/* Posted by */}
        <div className="pt-2 border-t border-gray-100 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-500 truncate">
            By {rental.posted_by_name || rental.posted_by || 'Unknown'}
          </p>
        </div>

        {/* View Link */}
        <Link
          href={`/rentals/${rental.listing_id}`}
          className="mt-3 flex items-center justify-center w-full py-2 text-sm font-medium text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors"
        >
          View Details →
        </Link>
      </div>
    </div>
  );
}
