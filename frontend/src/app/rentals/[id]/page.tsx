'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getRental, formatPrice, formatArea, formatDate, Rental } from '@/lib/api';

export default function RentalDetailPage() {
  const { getValidToken } = useAuth();
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [rental, setRental] = useState<Rental | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      const token = await getValidToken();
      if (!token) { router.replace('/login'); return; }
      setLoading(true);
      setError('');
      try {
        const data = await getRental(token, id);
        setRental(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load rental');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, getValidToken, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] gap-4">
        <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400">Loading rental...</p>
      </div>
    );
  }

  if (error || !rental) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <p className="text-red-500">{error || 'Rental not found'}</p>
        <button onClick={() => router.back()} className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm">← Go back</button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
        <button onClick={() => router.push('/rentals')} className="hover:text-emerald-600 dark:hover:text-emerald-400">Rentals</button>
        <span>/</span>
        <span className="text-gray-900 dark:text-gray-100 truncate max-w-xs">{rental.apartment_name}</span>
      </nav>

      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
        <div className="h-2 bg-emerald-500" />
        <div className="p-6 sm:p-8">
          <div className="mb-4">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {rental.apartment_name || rental.title}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-1">
              <span>📍</span> {rental.locality}
            </p>
          </div>

          {/* Rent Info */}
          <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl">
            <div className="flex items-baseline gap-3 flex-wrap">
              <span className="text-3xl font-bold text-emerald-700 dark:text-emerald-400">
                {rental.price > 0 ? formatPrice(rental.price) : 'Rent on request'}
              </span>
              <span className="text-sm text-emerald-600 dark:text-emerald-500">/month</span>
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-1 mt-2">
              {rental.deposit && rental.deposit > 0 && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Deposit: <span className="font-semibold">{formatPrice(rental.deposit)}</span>
                </p>
              )}
              {rental.maintenance && rental.maintenance > 0 && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Maintenance: <span className="font-semibold">{formatPrice(rental.maintenance)}/mo</span>
                </p>
              )}
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
              Listed {formatDate(rental.posted_at)} · {rental.website}
            </p>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Bedrooms', value: `${rental.bedroom} BHK`, icon: '🛏' },
              { label: 'Bathrooms', value: rental.bathroom, icon: '🚿' },
              { label: 'Floor', value: rental.floor != null ? `${rental.floor}${rental.total_floors ? ` / ${rental.total_floors}` : ''}` : '—', icon: '🏢' },
              { label: 'Carpet Area', value: rental.carpet_area > 0 ? formatArea(rental.carpet_area) : '—', icon: '📐' },
              { label: 'Super Built-up', value: rental.super_builtup_area ? formatArea(rental.super_builtup_area) : '—', icon: '📏' },
              { label: 'Furnishing', value: rental.furnishing, icon: '🛋' },
              { label: 'Facing', value: rental.facing_direction ?? '—', icon: '🧭' },
              { label: 'Property Type', value: rental.property_type, icon: '🏠' },
            ].map(item => (
              <div key={item.label} className="bg-gray-50 dark:bg-gray-800 rounded-xl p-3">
                <p className="text-xs text-gray-400 dark:text-gray-500 mb-0.5">{item.icon} {item.label}</p>
                <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">{String(item.value)}</p>
              </div>
            ))}
          </div>

          {/* Description */}
          {rental.description && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">About this rental</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed whitespace-pre-line">{rental.description}</p>
            </div>
          )}

          {/* Contact */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-5">
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-3">Contact Details</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-gray-400 dark:text-gray-500">Posted by</p>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{rental.posted_by_name || rental.posted_by}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{rental.posted_by}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 dark:text-gray-500">Contact</p>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{rental.posted_by_contact}</p>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800 flex flex-wrap gap-x-6 gap-y-2 text-xs text-gray-400">
            <span>ID: <code className="font-mono">{rental.listing_id}</code></span>
            {rental.listing_url && (
              <a href={rental.listing_url} target="_blank" rel="noopener noreferrer" className="text-emerald-500 hover:underline">
                View original listing ↗
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
