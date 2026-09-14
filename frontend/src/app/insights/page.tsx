'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getListings, Listing, formatPrice } from '@/lib/api';

interface LocalityStat {
  locality: string;
  count: number;
  medianPrice: number;
  avgPricePerSqft: number;
}

interface BhkStat {
  bhk: number;
  count: number;
  medianPrice: number;
}

interface InsightData {
  totalListings: number;
  activeCount: number;
  inactiveCount: number;
  medianPrice: number;
  avgPricePerSqft: number;
  localityStats: LocalityStat[];
  bhkStats: BhkStat[];
  corruptListings: number;
  suspiciousPhones: number;
  priceOutliers: number;
  areaOutliers: number;
  zeroPrice: number;
  zeroArea: number;
  listingsLoaded: number;
}

function median(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function computeInsights(listings: Listing[]): InsightData {
  const activeListings = listings.filter(l => l.is_live);
  const inactiveListings = listings.filter(l => !l.is_live);

  const validPrices = listings.filter(l => l.price > 0 && l.price < 1_000_000_000);
  const prices = validPrices.map(l => l.price);
  const pricesPerSqft = listings
    .filter(l => l.price > 0 && l.carpet_area > 0 && l.carpet_area < 100_000)
    .map(l => l.price / l.carpet_area);

  // Locality breakdown
  const localityMap = new Map<string, Listing[]>();
  listings.forEach(l => {
    if (!l.locality) return;
    const arr = localityMap.get(l.locality) || [];
    arr.push(l);
    localityMap.set(l.locality, arr);
  });

  const localityStats: LocalityStat[] = Array.from(localityMap.entries())
    .map(([locality, locs]) => {
      const lPrices = locs.filter(l => l.price > 0 && l.price < 1_000_000_000).map(l => l.price);
      const lPpsqft = locs
        .filter(l => l.price > 0 && l.carpet_area > 0 && l.carpet_area < 100_000)
        .map(l => l.price / l.carpet_area);
      return {
        locality,
        count: locs.length,
        medianPrice: median(lPrices),
        avgPricePerSqft: lPpsqft.length > 0 ? lPpsqft.reduce((a, b) => a + b, 0) / lPpsqft.length : 0,
      };
    })
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // BHK breakdown
  const bhkMap = new Map<number, Listing[]>();
  listings.forEach(l => {
    if (l.bedroom == null) return;
    const arr = bhkMap.get(l.bedroom) || [];
    arr.push(l);
    bhkMap.set(l.bedroom, arr);
  });

  const bhkStats: BhkStat[] = Array.from(bhkMap.entries())
    .map(([bhk, locs]) => {
      const bPrices = locs.filter(l => l.price > 0 && l.price < 1_000_000_000).map(l => l.price);
      return { bhk, count: locs.length, medianPrice: median(bPrices) };
    })
    .sort((a, b) => a.bhk - b.bhk);

  // Data quality issues
  const zeroPrice = listings.filter(l => !l.price || l.price === 0).length;
  const zeroArea = listings.filter(l => !l.carpet_area || l.carpet_area === 0).length;
  const priceOutliers = listings.filter(l => l.price > 500_000_000).length; // >50 Cr seems outlier
  const areaOutliers = listings.filter(l => l.carpet_area > 50_000).length; // >50k sqft impossible for flat
  const corruptListings = listings.filter(l =>
    (l.carpet_area > 50_000) || (l.price > 500_000_000) || l.price === 0 || l.carpet_area === 0
  ).length;

  // Suspicious phones: sequential numbers like 9999999999 or 1234567890
  const suspiciousPhones = listings.filter(l => {
    const phone = l.posted_by_contact || '';
    return /^(.)\1{8,}$/.test(phone.replace(/\D/g, '')) ||
      phone.includes('1234567890') ||
      phone.includes('0000000000') ||
      phone.includes('9876543210');
  }).length;

  return {
    totalListings: listings.length,
    activeCount: activeListings.length,
    inactiveCount: inactiveListings.length,
    medianPrice: median(prices),
    avgPricePerSqft: pricesPerSqft.length > 0 ? pricesPerSqft.reduce((a, b) => a + b, 0) / pricesPerSqft.length : 0,
    localityStats,
    bhkStats,
    corruptListings,
    suspiciousPhones,
    priceOutliers,
    areaOutliers,
    zeroPrice,
    zeroArea,
    listingsLoaded: listings.length,
  };
}

function StatCard({ label, value, sub, color = 'teal' }: { label: string; value: string | number; sub?: string; color?: string }) {
  const colorMap: Record<string, string> = {
    teal: 'border-teal-200 dark:border-teal-800 bg-teal-50 dark:bg-teal-900/20',
    green: 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20',
    red: 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20',
    amber: 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20',
    violet: 'border-violet-200 dark:border-violet-800 bg-violet-50 dark:bg-violet-900/20',
    gray: 'border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800',
  };
  return (
    <div className={`rounded-xl border p-4 ${colorMap[color] || colorMap.teal}`}>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
      {sub && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function InsightsPage() {
  const { getValidToken } = useAuth();
  const router = useRouter();

  const [allListings, setAllListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState({ loaded: 0, total: 0 });
  const [error, setError] = useState('');
  const [insights, setInsights] = useState<InsightData | null>(null);

  const loadAllListings = useCallback(async () => {
    const token = await getValidToken();
    if (!token) { router.replace('/login'); return; }

    setLoading(true);
    setError('');
    setAllListings([]);
    setProgress({ loaded: 0, total: 0 });

    try {
      const collected: Listing[] = [];
      let offset = 0;
      const limit = 50;

      // First request to get total
      const first = await getListings(token, { offset: 0, limit });
      collected.push(...first.results);
      offset = first.results.length;
      setProgress({ loaded: offset, total: first.total });

      // Continue fetching until done
      while (first.has_more && offset < first.total && offset < 2000) {
        const data = await getListings(token, { offset, limit });
        collected.push(...data.results);
        offset += data.results.length;
        setProgress({ loaded: offset, total: first.total });
        if (!data.has_more) break;
      }

      setAllListings(collected);
      setInsights(computeInsights(collected));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [getValidToken, router]);

  useEffect(() => {
    loadAllListings();
  }, [loadAllListings]);

  const maxLocalityCount = insights?.localityStats[0]?.count || 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Market Insights</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Analytics computed from live API data
          </p>
        </div>
        <button
          onClick={loadAllListings}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
        >
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-6">
          <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-center">
            <p className="text-gray-600 dark:text-gray-300 font-medium">Fetching all listings...</p>
            {progress.total > 0 && (
              <>
                <p className="text-sm text-gray-400 mt-1">
                  {progress.loaded.toLocaleString('en-IN')} / {progress.total.toLocaleString('en-IN')} listings
                </p>
                <div className="w-64 h-2 bg-gray-200 dark:bg-gray-700 rounded-full mt-3 overflow-hidden">
                  <div
                    className="h-full bg-teal-500 rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(100, (progress.loaded / progress.total) * 100)}%` }}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <p className="text-red-500">{error}</p>
          <button onClick={loadAllListings} className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm">Retry</button>
        </div>
      )}

      {!loading && insights && (
        <div className="space-y-8">
          {/* Data note */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl text-sm text-blue-700 dark:text-blue-300">
            <p className="font-semibold mb-1">📊 Data source</p>
            <p>Analytics computed client-side from <strong>{insights.listingsLoaded.toLocaleString('en-IN')} listings</strong> fetched from /v1/listings.
              Note: API returns both <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">is_live=true</code> and <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">is_live=false</code> records.</p>
          </div>

          {/* Overview Stats */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Overview</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              <StatCard label="Total Listings" value={insights.totalListings.toLocaleString('en-IN')} color="teal" />
              <StatCard
                label="Active Listings"
                value={insights.activeCount.toLocaleString('en-IN')}
                sub={`${((insights.activeCount / insights.totalListings) * 100).toFixed(1)}% of total`}
                color="green"
              />
              <StatCard
                label="Inactive Listings"
                value={insights.inactiveCount.toLocaleString('en-IN')}
                sub={`${((insights.inactiveCount / insights.totalListings) * 100).toFixed(1)}% of total`}
                color="gray"
              />
              <StatCard
                label="Median Price"
                value={insights.medianPrice > 0 ? formatPrice(insights.medianPrice) : 'N/A'}
                sub="Active + Inactive"
                color="violet"
              />
              <StatCard
                label="Avg Price/sqft"
                value={insights.avgPricePerSqft > 0 ? `₹${Math.round(insights.avgPricePerSqft).toLocaleString('en-IN')}` : 'N/A'}
                color="amber"
              />
            </div>
          </section>

          {/* Active/Inactive Ratio Visual */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Active vs Inactive Split</h2>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="flex-1 h-8 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800 flex">
                  <div
                    className="h-full bg-teal-500 flex items-center justify-center text-xs text-white font-medium"
                    style={{ width: `${(insights.activeCount / insights.totalListings) * 100}%` }}
                  >
                    {insights.totalListings > 0 && (insights.activeCount / insights.totalListings) * 100 > 10
                      ? `${((insights.activeCount / insights.totalListings) * 100).toFixed(1)}%`
                      : ''}
                  </div>
                  <div
                    className="h-full bg-gray-400 flex items-center justify-center text-xs text-white font-medium"
                    style={{ width: `${(insights.inactiveCount / insights.totalListings) * 100}%` }}
                  >
                    {insights.totalListings > 0 && (insights.inactiveCount / insights.totalListings) * 100 > 10
                      ? `${((insights.inactiveCount / insights.totalListings) * 100).toFixed(1)}%`
                      : ''}
                  </div>
                </div>
              </div>
              <div className="flex gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-teal-500" />
                  <span className="text-gray-600 dark:text-gray-400">Active: <strong className="text-gray-900 dark:text-gray-100">{insights.activeCount.toLocaleString('en-IN')}</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gray-400" />
                  <span className="text-gray-600 dark:text-gray-400">Inactive: <strong className="text-gray-900 dark:text-gray-100">{insights.inactiveCount.toLocaleString('en-IN')}</strong></span>
                </div>
              </div>
            </div>
          </section>

          {/* BHK Distribution */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Distribution by BHK</h2>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
              <div className="space-y-3">
                {insights.bhkStats.map(stat => {
                  const pct = (stat.count / insights.totalListings) * 100;
                  return (
                    <div key={stat.bhk} className="flex items-center gap-4">
                      <div className="w-16 text-sm font-medium text-gray-700 dark:text-gray-300 text-right flex-shrink-0">
                        {stat.bhk} BHK
                      </div>
                      <div className="flex-1 h-7 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-teal-400 to-teal-600 rounded-lg flex items-center px-2 transition-all duration-500"
                          style={{ width: `${Math.max(2, pct)}%` }}
                        >
                          <span className="text-xs text-white font-medium">{stat.count}</span>
                        </div>
                      </div>
                      <div className="w-32 text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                        {pct.toFixed(1)}% · {stat.medianPrice > 0 ? formatPrice(stat.medianPrice) : '—'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Locality Distribution */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Top 10 Localities by Listing Count</h2>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">#</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Locality</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Count</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Median Price</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Avg ₹/sqft</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Share</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {insights.localityStats.map((stat, idx) => (
                    <tr key={stat.locality} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                      <td className="px-4 py-3 text-gray-400 dark:text-gray-500">{idx + 1}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{stat.locality}</td>
                      <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{stat.count.toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300 hidden sm:table-cell">
                        {stat.medianPrice > 0 ? formatPrice(stat.medianPrice) : '—'}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300 hidden md:table-cell">
                        {stat.avgPricePerSqft > 0 ? `₹${Math.round(stat.avgPricePerSqft).toLocaleString('en-IN')}` : '—'}
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-teal-500 rounded-full"
                              style={{ width: `${(stat.count / maxLocalityCount) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400">{((stat.count / insights.totalListings) * 100).toFixed(1)}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Data Quality Issues */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Data Quality Notes</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Known issues discovered in the dataset during API exploration
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              <StatCard
                label="Potentially Corrupt Records"
                value={insights.corruptListings.toLocaleString('en-IN')}
                sub="Zero price, zero area, or impossible values"
                color="red"
              />
              <StatCard
                label="Zero-Price Listings"
                value={insights.zeroPrice.toLocaleString('en-IN')}
                sub="Price = 0 (missing or fake data)"
                color="amber"
              />
              <StatCard
                label="Zero-Area Listings"
                value={insights.zeroArea.toLocaleString('en-IN')}
                sub="Carpet area = 0 (corrupt data)"
                color="amber"
              />
              <StatCard
                label="Extreme Price Outliers"
                value={insights.priceOutliers.toLocaleString('en-IN')}
                sub="Price > ₹50 Cr (likely fake/test data)"
                color="red"
              />
              <StatCard
                label="Impossible Area Listings"
                value={insights.areaOutliers.toLocaleString('en-IN')}
                sub="Carpet area > 50,000 sqft (physically impossible for an apartment)"
                color="red"
              />
              <StatCard
                label="Suspicious Phone Numbers"
                value={insights.suspiciousPhones.toLocaleString('en-IN')}
                sub="Sequential/repeated digit patterns — likely fake listings"
                color="amber"
              />
            </div>

            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-5 space-y-3 text-sm text-amber-800 dark:text-amber-300">
              <h3 className="font-semibold text-amber-900 dark:text-amber-200">⚠️ Known Data Issues (API Exploration Findings)</h3>
              <ul className="space-y-2 list-disc list-inside">
                <li>
                  <strong>API returns inactive listings:</strong> The /v1/listings endpoint returns both{' '}
                  <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">is_live=true</code> and{' '}
                  <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">is_live=false</code> records,
                  contrary to documentation which says only active listings are returned.
                </li>
                <li>
                  <strong>Project prices in crores:</strong> Documentation states project{' '}
                  <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">price_min</code> /{' '}
                  <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">price_max</code> are in rupees,
                  but they are actually in <strong>crores</strong>.
                </li>
                <li>
                  <strong>Corrupt listings with impossible areas:</strong> Some records have{' '}
                  <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">carpet_area</code> values
                  exceeding 50,000 sqft — physically impossible for residential apartments.
                </li>
                <li>
                  <strong>Fake listings via phone patterns:</strong> A pattern of repeated or sequential phone numbers
                  (e.g., 9999999999, 1234567890) suggests fabricated listings in the dataset.
                </li>
                <li>
                  <strong>Missing analytics endpoint:</strong>{' '}
                  <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">/v1/analytics/summary</code>{' '}
                  returns 404 — it is documented but does not exist. All insights here are computed client-side.
                </li>
                <li>
                  <strong>Token lifetime mismatch:</strong> Documentation says tokens expire in 86400s (24h),
                  but actual expiry is 900s (15 min). Refresh token flow is required.
                </li>
                <li>
                  <strong>Wrong endpoint paths in docs:</strong>{' '}
                  <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">/v1/listing/&#123;id&#125;</code> →
                  actual: <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">/v1/listings/&#123;id&#125;</code>;{' '}
                  <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">/v1/favourites</code> →
                  actual: <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded text-xs">/v1/saved</code>.
                </li>
              </ul>
            </div>
          </section>

          {/* Price Analysis */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Price Distribution by BHK</h2>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">BHK</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Count</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Median Price</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Bar</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {insights.bhkStats.map(stat => {
                    const maxCount = Math.max(...insights.bhkStats.map(s => s.count));
                    return (
                      <tr key={stat.bhk} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{stat.bhk} BHK</td>
                        <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{stat.count.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 text-right font-medium text-teal-700 dark:text-teal-400">
                          {stat.medianPrice > 0 ? formatPrice(stat.medianPrice) : '—'}
                        </td>
                        <td className="px-4 py-3 hidden sm:table-cell">
                          <div className="w-32 h-3 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-teal-500 rounded-full"
                              style={{ width: `${(stat.count / maxCount) * 100}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* Footer note */}
          <div className="text-xs text-gray-400 dark:text-gray-500 text-center pb-4">
            Data fetched from {insights.listingsLoaded.toLocaleString('en-IN')} listings via /v1/listings API.
            Insights are computed client-side. Refresh to get latest data.
          </div>
        </div>
      )}
    </div>
  );
}
