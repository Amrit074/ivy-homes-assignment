'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getListing, addSaved, removeSaved, getSaved, formatPrice, formatArea, formatDate, type Listing } from '@/lib/api';

export default function ListingDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const { user, getValidToken, isLoading } = useAuth();
  const router = useRouter();
  
  const [listing, setListing] = useState<Listing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isSaved, setIsSaved] = useState(false);
  const [savingToggle, setSavingToggle] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) router.push('/login');
  }, [user, isLoading, router]);

  useEffect(() => {
    if (!user || !id) return;
    const load = async () => {
      const token = await getValidToken();
      if (!token) { router.push('/login'); return; }
      setLoading(true);
      try {
        const [data, saved] = await Promise.all([
          getListing(token, id),
          getSaved(token)
        ]);
        setListing(data);
        setIsSaved(saved.results.some(l => l.listing_id === id));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load listing');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user, id, getValidToken, router]);

  const toggleSave = async () => {
    const token = await getValidToken();
    if (!token || !listing) return;
    setSavingToggle(true);
    try {
      if (isSaved) {
        await removeSaved(token, listing.listing_id);
        setIsSaved(false);
      } else {
        await addSaved(token, listing.listing_id);
        setIsSaved(true);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSavingToggle(false);
    }
  };

  if (isLoading || loading) return (
    <div className="p-8 text-center">
      <div className="inline-block w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );
  
  if (error) return (
    <div className="max-w-3xl mx-auto p-8">
      <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3">{error}</div>
    </div>
  );

  if (!listing) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button onClick={() => router.back()} className="text-teal-600 hover:text-teal-800 mb-4 flex items-center gap-1">
        ← Back
      </button>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-teal-600 to-emerald-600 p-6 text-white">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold">{listing.apartment_name}</h1>
              <p className="text-teal-100 mt-1 capitalize">{listing.locality} · {listing.property_type}</p>
            </div>
            <button
              onClick={toggleSave}
              disabled={savingToggle}
              className="bg-white/20 hover:bg-white/30 rounded-full p-2 transition-colors"
            >
              {isSaved ? '❤️' : '🤍'}
            </button>
          </div>
          <div className="mt-4 text-3xl font-bold">
            {listing.price > 0 ? formatPrice(listing.price) : '—'}
          </div>
        </div>

        <div className="p-6">
          {/* Key stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Bedrooms', value: `${listing.bedroom} BHK` },
              { label: 'Bathrooms', value: listing.bathroom },
              { label: 'Carpet Area', value: listing.carpet_area ? formatArea(listing.carpet_area) : '—' },
              { label: 'Floor', value: listing.floor ? `${listing.floor}/${listing.total_floors}` : '—' },
              { label: 'Furnishing', value: listing.furnishing },
              { label: 'Facing', value: listing.facing_direction || '—' },
              { label: 'Parking', value: listing.covered_parking !== undefined ? listing.covered_parking : '—' },
              { label: 'Posted', value: formatDate(listing.posted_at) },
            ].map(({ label, value }) => (
              <div key={label} className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">{label}</p>
                <p className="font-semibold text-gray-900 capitalize">{String(value)}</p>
              </div>
            ))}
          </div>

          {/* Price per sqft */}
          {listing.price > 0 && listing.carpet_area > 0 && (
            <div className="bg-teal-50 rounded-lg p-3 mb-4">
              <p className="text-sm text-teal-700">
                Price per sq.ft: <span className="font-bold">₹{(listing.price / listing.carpet_area).toFixed(0)}</span>
              </p>
            </div>
          )}

          {/* Status badges */}
          <div className="flex gap-2 flex-wrap mb-4">
            {listing.is_live && (
              <span className="bg-green-100 text-green-700 text-xs font-medium px-2.5 py-1 rounded-full">Active</span>
            )}
            {!listing.is_live && (
              <span className="bg-gray-100 text-gray-600 text-xs font-medium px-2.5 py-1 rounded-full">Inactive</span>
            )}
            {listing.is_verified && (
              <span className="bg-blue-100 text-blue-700 text-xs font-medium px-2.5 py-1 rounded-full">✓ Verified</span>
            )}
            <span className="bg-purple-100 text-purple-700 text-xs font-medium px-2.5 py-1 rounded-full capitalize">{listing.website}</span>
          </div>

          {/* Description */}
          <div className="mb-6">
            <h2 className="font-semibold text-gray-900 mb-2">Description</h2>
            <p className="text-gray-600 text-sm leading-relaxed">{listing.description}</p>
          </div>

          {/* Contact */}
          <div className="border-t border-gray-100 pt-4">
            <h2 className="font-semibold text-gray-900 mb-3">Contact</h2>
            <div className="flex items-center gap-4">
              <div>
                <p className="font-medium text-gray-900">{listing.posted_by_name}</p>
                <p className="text-sm text-gray-500 capitalize">{listing.posted_by}</p>
              </div>
              <a
                href={`tel:${listing.posted_by_contact}`}
                className="ml-auto bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-lg text-sm transition-colors"
              >
                📞 Call
              </a>
            </div>
          </div>

          {/* External link */}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <a
              href={listing.listing_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-teal-600 hover:text-teal-800 text-sm"
            >
              View original listing on {listing.website} →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
