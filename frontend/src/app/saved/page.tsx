'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getSaved, removeSaved, Listing } from '@/lib/api';
import ListingCard from '@/components/ListingCard';

export default function SavedPage() {
  const { getValidToken } = useAuth();
  const router = useRouter();

  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [removingId, setRemovingId] = useState<string | null>(null);

  const fetchSaved = useCallback(async () => {
    const token = await getValidToken();
    if (!token) { router.replace('/login'); return; }
    setLoading(true);
    setError('');
    try {
      const data = await getSaved(token);
      setListings(data.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load saved listings');
    } finally {
      setLoading(false);
    }
  }, [getValidToken, router]);

  useEffect(() => {
    fetchSaved();
  }, [fetchSaved]);

  async function handleUnsave(id: string) {
    const token = await getValidToken();
    if (!token) return;
    setRemovingId(id);
    try {
      await removeSaved(token, id);
      setListings(prev => prev.filter(l => l.listing_id !== id));
    } catch (e) {
      console.error('Failed to remove saved listing:', e);
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Saved Listings</h1>
          {!loading && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {listings.length} saved {listings.length === 1 ? 'listing' : 'listings'}
            </p>
          )}
        </div>
        <button
          onClick={fetchSaved}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="w-10 h-10 border-4 border-red-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading saved listings...</p>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <p className="text-red-500">{error}</p>
          <button onClick={fetchSaved} className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm">Retry</button>
        </div>
      ) : listings.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
          <div className="text-6xl">❤️</div>
          <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300">No saved listings yet</h2>
          <p className="text-gray-500 dark:text-gray-400 max-w-sm">
            Save properties while browsing to keep track of listings you&apos;re interested in.
          </p>
          <button
            onClick={() => router.push('/listings')}
            className="mt-2 px-6 py-3 bg-teal-600 hover:bg-teal-700 text-white font-medium rounded-xl transition-colors"
          >
            Browse Listings
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {listings.map(listing => (
            <div
              key={listing.listing_id}
              className={`transition-opacity ${removingId === listing.listing_id ? 'opacity-50 pointer-events-none' : ''}`}
            >
              <ListingCard
                listing={listing}
                isSaved={true}
                onUnsave={handleUnsave}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
