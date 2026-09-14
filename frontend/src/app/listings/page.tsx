'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getListings, formatPrice, formatArea, type Listing, addSaved, removeSaved, getSaved } from '@/lib/api';
import ListingCard from '@/components/ListingCard';

const LOCALITIES = [
  '', 'sector 49', 'sector 56', 'sector 65', 'sohna road', 'golf course road',
  'dwarka expressway', 'mg road', 'new gurgaon', 'dlf phase 3', 'golf course extension road'
];

const FURNISHINGS = ['', 'unfurnished', 'semi-furnished', 'fully-furnished'];
const PROPERTY_TYPES = ['', 'apartment', 'villa', 'independent house', 'plot', 'builder floor'];

export default function ListingsPage() {
  const { user, getValidToken, isLoading } = useAuth();
  const router = useRouter();
  
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  
  const [filters, setFilters] = useState({
    locality: '',
    bhk: '',
    min_price: '',
    max_price: '',
    furnishing: '',
    property_type: '',
    sort_by: 'posted_at',
    order: 'desc',
  });
  const [appliedFilters, setAppliedFilters] = useState(filters);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  // Load saved listings for the heart icon
  const loadSaved = useCallback(async () => {
    const token = await getValidToken();
    if (!token) return;
    try {
      const saved = await getSaved(token);
      setSavedIds(new Set(saved.results.map(l => l.listing_id)));
    } catch { /* ignore */ }
  }, [getValidToken]);

  useEffect(() => {
    if (user) loadSaved();
  }, [user, loadSaved]);

  const fetchListings = useCallback(async (currentOffset: number, reset: boolean = false) => {
    const token = await getValidToken();
    if (!token) { router.push('/login'); return; }
    
    setLoading(true);
    setError('');
    try {
      const params: Record<string, string | number> = {
        offset: currentOffset,
        limit: 20,
        sort_by: appliedFilters.sort_by,
        order: appliedFilters.order,
      };
      if (appliedFilters.locality) params.locality = appliedFilters.locality;
      if (appliedFilters.bhk) params.bhk = parseInt(appliedFilters.bhk);
      if (appliedFilters.min_price) params.min_price = parseInt(appliedFilters.min_price);
      if (appliedFilters.max_price) params.max_price = parseInt(appliedFilters.max_price);
      if (appliedFilters.furnishing) params.furnishing = appliedFilters.furnishing;
      if (appliedFilters.property_type) params.property_type = appliedFilters.property_type;

      const data = await getListings(token, params as Parameters<typeof getListings>[1]);
      setTotal(data.total);
      setHasMore(data.has_more);
      
      if (reset) {
        setListings(data.results);
      } else {
        setListings(prev => [...prev, ...data.results]);
      }
      setOffset(currentOffset + data.results.length);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load listings');
    } finally {
      setLoading(false);
    }
  }, [appliedFilters, getValidToken, router]);

  useEffect(() => {
    if (user) {
      setOffset(0);
      setListings([]);
      fetchListings(0, true);
    }
  }, [user, appliedFilters, fetchListings]);

  const handleApplyFilters = () => {
    setAppliedFilters(filters);
  };

  const toggleSave = async (listingId: string) => {
    const token = await getValidToken();
    if (!token) return;
    try {
      if (savedIds.has(listingId)) {
        await removeSaved(token, listingId);
        setSavedIds(prev => { const s = new Set(prev); s.delete(listingId); return s; });
      } else {
        await addSaved(token, listingId);
        setSavedIds(prev => new Set(prev).add(listingId));
      }
    } catch (err) {
      console.error('Failed to toggle save:', err);
    }
  };

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading...</div>;
  if (!user) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Listings in Gurgaon</h1>
        {total > 0 && <p className="text-gray-500">{total.toLocaleString()} listings available</p>}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          <select
            value={filters.locality}
            onChange={e => setFilters(f => ({ ...f, locality: e.target.value }))}
            className="col-span-2 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All Localities</option>
            {LOCALITIES.filter(l => l).map(l => (
              <option key={l} value={l}>{l.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}</option>
            ))}
          </select>
          
          <select
            value={filters.bhk}
            onChange={e => setFilters(f => ({ ...f, bhk: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All BHK</option>
            {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n} BHK</option>)}
          </select>

          <select
            value={filters.furnishing}
            onChange={e => setFilters(f => ({ ...f, furnishing: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All Furnishing</option>
            {FURNISHINGS.filter(f => f).map(f => <option key={f} value={f}>{f}</option>)}
          </select>

          <input
            type="number"
            placeholder="Min Price (₹)"
            value={filters.min_price}
            onChange={e => setFilters(f => ({ ...f, min_price: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          />

          <input
            type="number"
            placeholder="Max Price (₹)"
            value={filters.max_price}
            onChange={e => setFilters(f => ({ ...f, max_price: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          />

          <select
            value={`${filters.sort_by}:${filters.order}`}
            onChange={e => {
              const [sort_by, order] = e.target.value.split(':');
              setFilters(f => ({ ...f, sort_by, order }));
            }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="posted_at:desc">Newest First</option>
            <option value="posted_at:asc">Oldest First</option>
            <option value="price:asc">Price: Low to High</option>
            <option value="price:desc">Price: High to Low</option>
            <option value="carpet_area:desc">Largest Area</option>
          </select>

          <button
            onClick={handleApplyFilters}
            className="bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-lg text-sm transition-colors"
          >
            Apply
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {/* Listings grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {listings.map(listing => (
          <ListingCard
            key={listing.listing_id}
            listing={listing}
            isSaved={savedIds.has(listing.listing_id)}
            onToggleSave={() => toggleSave(listing.listing_id)}
          />
        ))}
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {!loading && hasMore && listings.length > 0 && (
        <div className="text-center py-6">
          <button
            onClick={() => fetchListings(offset)}
            className="bg-white border border-gray-300 hover:border-teal-500 text-gray-700 hover:text-teal-700 font-medium py-2.5 px-8 rounded-lg transition-colors"
          >
            Load More ({total - listings.length} remaining)
          </button>
        </div>
      )}

      {!loading && !hasMore && listings.length > 0 && (
        <p className="text-center py-4 text-gray-400 text-sm">All {listings.length} listings loaded</p>
      )}

      {!loading && listings.length === 0 && !error && (
        <div className="text-center py-16 text-gray-400">
          <div className="text-5xl mb-4">🏠</div>
          <p>No listings found with current filters</p>
        </div>
      )}
    </div>
  );
}
