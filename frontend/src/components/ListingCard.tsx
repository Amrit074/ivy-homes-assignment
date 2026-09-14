import Link from 'next/link';
import { Listing, formatPrice, formatArea, formatDate } from '@/lib/api';

interface ListingCardProps {
  listing: Listing;
  onSave?: (id: string) => void;
  onUnsave?: (id: string) => void;
  onToggleSave?: () => void;
  isSaved?: boolean;
}

export default function ListingCard({ listing, onSave, onUnsave, onToggleSave, isSaved }: ListingCardProps) {
  const priceDisplay = listing.price > 0 ? formatPrice(listing.price) : 'Price on request';
  const areaDisplay = listing.carpet_area > 0 ? formatArea(listing.carpet_area) : null;
  const pricePerSqft =
    listing.price > 0 && listing.carpet_area > 0
      ? `₹${Math.round(listing.price / listing.carpet_area).toLocaleString('en-IN')}/sqft`
      : null;

  const furnishingColor: Record<string, string> = {
    Furnished: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    'Semi-Furnished': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
    Unfurnished: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
  };
  const furnishingClass = furnishingColor[listing.furnishing] ?? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400';

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden hover:shadow-md dark:hover:shadow-gray-900 transition-shadow group">
      {/* Color band */}
      <div className={`h-1 ${listing.is_live ? 'bg-teal-500' : 'bg-gray-400'}`} />

      <div className="p-4">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm leading-tight truncate group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
              {listing.apartment_name || 'Unknown Property'}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
              📍 {listing.locality}
            </p>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            {!listing.is_live && (
              <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 rounded-full">
                Inactive
              </span>
            )}
            {(onSave || onUnsave || onToggleSave) && (
              <button
                onClick={() => {
                  if (onToggleSave) onToggleSave();
                  else if (isSaved) onUnsave?.(listing.listing_id);
                  else onSave?.(listing.listing_id);
                }}
                className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                title={isSaved ? 'Remove from saved' : 'Save listing'}
              >
                <svg
                  className={`w-4 h-4 transition-colors ${isSaved ? 'text-red-500 fill-red-500' : 'text-gray-400 hover:text-red-400'}`}
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  fill="none"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Price */}
        <div className="mb-3">
          <span className="text-lg font-bold text-teal-700 dark:text-teal-400">{priceDisplay}</span>
          {pricePerSqft && <span className="text-xs text-gray-400 dark:text-gray-500 ml-2">{pricePerSqft}</span>}
        </div>

        {/* Specs */}
        <div className="flex flex-wrap gap-2 mb-3">
          <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
            🛏 {listing.bedroom} BHK
          </span>
          <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
            🚿 {listing.bathroom} Bath
          </span>
          {areaDisplay && (
            <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
              📐 {areaDisplay}
            </span>
          )}
          {listing.floor != null && (
            <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-md">
              🏢 Floor {listing.floor}
            </span>
          )}
        </div>

        {/* Furnishing + Posted by */}
        <div className="flex items-center justify-between">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${furnishingClass}`}>
            {listing.furnishing}
          </span>
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {formatDate(listing.posted_at)}
          </span>
        </div>

        {/* Posted by */}
        <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-500 truncate">
            By {listing.posted_by_name || listing.posted_by || 'Unknown'}
          </p>
        </div>

        {/* View Details link */}
        <Link
          href={`/listings/${listing.listing_id}`}
          className="mt-3 flex items-center justify-center w-full py-2 text-sm font-medium text-teal-600 dark:text-teal-400 border border-teal-200 dark:border-teal-800 rounded-lg hover:bg-teal-50 dark:hover:bg-teal-900/20 transition-colors"
        >
          View Details →
        </Link>
      </div>
    </div>
  );
}
