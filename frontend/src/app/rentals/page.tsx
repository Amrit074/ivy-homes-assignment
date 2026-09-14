'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getRentals, Rental } from '@/lib/api';
import RentalCard from '@/components/RentalCard';

const LIMIT = 20;

const LOCALITIES = [
  'Whitefield', 'Koramangala', 'HSR Layout', 'Indiranagar', 'Marathahalli',
  'Electronic City', 'JP Nagar', 'BTM Layout', 'Sarjapur Road', 'Hebbal',
  'Yelahanka', 'Bannerghatta Road', 'Bellandur', 'Vijaya Nagar', 'Jayanagar',
];

const BHK_OPTIONS = [1, 2, 3, 4, 5];
const FURNISHING_OPTIONS = ['Furnished', 'Semi-Furnished', 'Unfurnished'];

export default function RentalsPage() {
  const { getValidToken } = useAuth();
  const router = useRouter();

  const [rentals, setRentals] = useState<Rental[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);

  // Filters
  const [locality, setLocality] = useState('');
  const [bhk, setBhk] = useState('');
  const [furnishing, setFurnishing] = useState('');

  const fetchRentals = useCallback(async (newOffset: number, replace: boolean) => {
    const token = await getValidToken();
    if (!token) { router.replace('/login'); return; }

    if (newOffset === 0) setLoading(true);
    else setLoadingMore(true);
    setError('');

    try {
      const data = await getRentals(token, {
        offset: newOffset,
        limit: LIMIT,
        ...(locality && { locality }),
        ...(bhk && { bhk: Number(bhk) }),
        ...(furnishing && { furnishing }),
      });

      setTotal(data.total);
      setHasMore(data.has_more);
      setOffset(newOffset + data.results.length);

      if (replace) setRentals(data.results);
      else setRentals(prev => [...prev, ...data.results]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load rentals');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [getValidToken, router, locality, bhk, furnishing]);

  useEffect(() => {
    setOffset(0);
    fetchRentals(0, true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locality, bhk, furnishing]);

  function resetFilters() {
    setLocality('');
    setBhk('');
    setFurnishing('');
  }

  const hasActiveFilters = locality || bhk || furnishing;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Rent Property</h1>
          {!loading && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {total.toLocaleString('en-IN')} rentals found
            </p>
          )}
        </div>
        <button
          onClick={() => setFiltersOpen(f => !f)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
            filtersOpen || hasActiveFilters
              ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-300 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300'
              : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400'
          }`}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
          </svg>
          Filters {hasActiveFilters ? '•' : ''}
        </button>
      </div>

      {/* Filters Panel */}
      {filtersOpen && (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 mb-6 shadow-sm">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Locality</label>
              <select
                value={locality}
                onChange={e => setLocality(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">All localities</option>
                {LOCALITIES.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">BHK</label>
              <div className="flex gap-1 flex-wrap">
                {BHK_OPTIONS.map(b => (
                  <button
                    key={b}
                    onClick={() => setBhk(bhk === String(b) ? '' : String(b))}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ${
                      bhk === String(b)
                        ? 'bg-emerald-600 border-emerald-600 text-white'
                        : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    {b}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Furnishing</label>
              <div className="flex gap-1 flex-wrap">
                {FURNISHING_OPTIONS.map(f => (
                  <button
                    key={f}
                    onClick={() => setFurnishing(furnishing === f ? '' : f)}
                    className={`px-2 py-1 text-xs font-medium rounded-md border transition-colors ${
                      furnishing === f
                        ? 'bg-emerald-600 border-emerald-600 text-white'
                        : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
          </div>
          {hasActiveFilters && (
            <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800 flex justify-end">
              <button onClick={resetFilters} className="text-sm text-red-500 hover:text-red-600 font-medium">
                Reset all
              </button>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading rentals...</p>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <p className="text-red-500">{error}</p>
          <button onClick={() => fetchRentals(0, true)} className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm">Retry</button>
        </div>
      ) : rentals.length === 0 ? (
        <div className="text-center py-24">
          <p className="text-5xl mb-4">🔑</p>
          <p className="text-gray-500 dark:text-gray-400">No rentals found. Try adjusting your filters.</p>
          {hasActiveFilters && (
            <button onClick={resetFilters} className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm">Clear filters</button>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {rentals.map(rental => (
              <RentalCard key={rental.listing_id} rental={rental} />
            ))}
          </div>
          {hasMore && (
            <div className="flex justify-center mt-8">
              <button
                onClick={() => fetchRentals(offset, false)}
                disabled={loadingMore}
                className="px-8 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-medium rounded-lg transition-colors"
              >
                {loadingMore ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Loading...
                  </span>
                ) : `Load more (${total - offset} remaining)`}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
