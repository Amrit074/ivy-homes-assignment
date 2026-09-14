// Ivy Homes API client library - CORRECTED
// Key discoveries vs documentation:
// 1. API key goes in X-API-Key header (doc says query param)
// 2. Auth login ALSO needs X-API-Key header (undocumented)
// 3. Auth response field is "access_token" (doc says "token")
// 4. Token expires in 900s (15 min), NOT 86400s (24h)
// 5. There IS a refresh_token + /auth/refresh endpoint (doc says no refresh flow)
// 6. All data endpoints need Bearer token
// 7. Pagination uses offset/limit, NOT page/limit (doc says page)
// 8. Response shape: {limit, offset, count, total, has_more, results}
//    (doc says: {total, page, page_size, results})
// 9. Max records per request = 50 (doc says limit up to 200)
// 10. /v1/listing/{id} (singular) returns 404; correct is /v1/listings/{id}
// 11. /v1/listings/{id}/similar returns 404 (documented but missing)
// 12. /v1/favourites returns 404; correct endpoint is /v1/saved
// 13. POST /v1/saved needs "listing_id" field (doc says "id")
// 14. /v1/analytics/summary returns 404 (documented but missing)
// 15. Project price_min/price_max are in crores, NOT rupees (doc says rupees)
// 16. /v1/listings returns both is_live=true and is_live=false (doc says only active)

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://solve.ivy.homes';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'IVY26-5C13E2AFECB7';

export interface AuthResponse {
  access_token: string;    // doc says "token" - WRONG
  refresh_token: string;   // undocumented
  token_type: string;
  expires_in: number;      // 900 (15min), doc says 86400 (24h) - WRONG
  refresh_url: string;     // undocumented
  user: { email: string }; // doc shows name too, but name is absent
}

export interface Listing {
  listing_id: string;
  listing_url: string;
  website: string;
  city_id: number;
  apartment_name: string;
  locality: string;
  property_type: string;
  bedroom: number;
  bathroom: number;
  balcony?: number;
  floor?: number;
  total_floors?: number;
  furnishing: string;
  facing_direction?: string;
  covered_parking?: number;
  price: number;
  carpet_area: number;
  super_built_up_area?: number;
  latitude?: number;
  longitude?: number;
  posted_by: string;
  posted_by_name: string;
  posted_by_contact: string;
  project_id?: string | null;
  is_verified: boolean;
  description: string;
  posted_at: string;
  is_live: boolean;  // undocumented field; endpoint returns both true and false
}

export interface Rental {
  listing_id: string;
  listing_url: string;
  website: string;
  city_id: number;
  title?: string;
  apartment_name: string;
  locality: string;
  property_type: string;
  bedroom: number;
  bathroom: number;
  floor?: number;
  total_floors?: number;
  furnishing: string;
  facing_direction?: string;
  price: number;
  deposit?: number;
  maintenance?: number;
  carpet_area: number;
  super_builtup_area?: number;
  latitude?: number;
  longitude?: number;
  posted_by: string;
  posted_by_name: string;
  posted_by_contact: string;
  description: string;
  posted_at: string;
  is_live?: boolean;
}

export interface Project {
  project_id: string;
  project_url: string;
  city_id: number;
  apartment_name: string;
  developer_name: string;
  locality: string;
  project_status: string;
  total_units?: number;
  total_towers?: number;
  total_floors?: number;
  launch_date?: string;
  possession_date?: string;
  rera_number?: string;
  min_area_sqft?: number;
  max_area_sqft?: number;
  amenities?: string[];
  latitude?: number;
  longitude?: number;
  total_listings?: number;
  // price_min and price_max are in CRORES, not rupees as documented
  price_min?: number;
  price_max?: number;
}

// Actual API response shape (different from docs)
export interface ApiResponse<T> {
  limit: number;
  offset: number;
  count: number;
  total: number;
  has_more: boolean;
  results: T[];
}

export interface ListingFilters {
  offset?: number;
  limit?: number;
  locality?: string;
  bhk?: number;
  property_type?: string;
  min_price?: number;
  max_price?: number;
  furnishing?: string;
  sort_by?: string;
  order?: string;
  project_id?: string;
}

function getApiHeaders(token?: string): HeadersInit {
  const headers: Record<string, string> = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
  params?: Record<string, string | number | undefined>
): Promise<T> {
  let url = `${BASE_URL}${path}`;

  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.set(key, String(value));
      }
    }
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...getApiHeaders(token),
      ...(options.headers as Record<string, string>),
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Auth
export async function login(email: string, password: string): Promise<AuthResponse> {
  // NOTE: X-API-Key header is required here too (not documented)
  return apiFetch<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(token: string): Promise<void> {
  try {
    await apiFetch('/auth/logout', { method: 'POST' }, token);
  } catch { /* ignore */ }
}

export async function refreshToken(refreshTokenStr: string): Promise<AuthResponse> {
  // /auth/refresh is undocumented but exists
  return apiFetch<AuthResponse>('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshTokenStr }),
  });
}

// Listings - uses offset not page
export async function getListings(
  token: string,
  filters: ListingFilters = {}
): Promise<ApiResponse<Listing>> {
  const { offset = 0, limit = 20, ...rest } = filters;
  return apiFetch<ApiResponse<Listing>>(
    '/v1/listings',
    {},
    token,
    { offset, limit, ...rest } as Record<string, string | number | undefined>
  );
}

export async function getListing(token: string, listingId: string): Promise<Listing> {
  // Correct path is /v1/listings/{id} NOT /v1/listing/{id} (doc is wrong)
  return apiFetch<Listing>(`/v1/listings/${listingId}`, {}, token);
}

// Rentals
export async function getRentals(
  token: string,
  filters: {
    offset?: number;
    limit?: number;
    locality?: string;
    bhk?: number;
    furnishing?: string;
    sort_by?: string;
    order?: string;
  } = {}
): Promise<ApiResponse<Rental>> {
  const { offset = 0, limit = 20, ...rest } = filters;
  return apiFetch<ApiResponse<Rental>>(
    '/v1/rentals',
    {},
    token,
    { offset, limit, ...rest } as Record<string, string | number | undefined>
  );
}

export async function getRental(token: string, listingId: string): Promise<Rental> {
  return apiFetch<Rental>(`/v1/rentals/${listingId}`, {}, token);
}

// Projects
export async function getProjects(
  token: string,
  filters: {
    offset?: number;
    limit?: number;
    locality?: string;
    project_status?: string;
    sort_by?: string;
    order?: string;
  } = {}
): Promise<ApiResponse<Project>> {
  const { offset = 0, limit = 20, ...rest } = filters;
  return apiFetch<ApiResponse<Project>>(
    '/v1/projects',
    {},
    token,
    { offset, limit, ...rest } as Record<string, string | number | undefined>
  );
}

export async function getProject(token: string, projectId: string): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${projectId}`, {}, token);
}

// Saved/Favourites - correct endpoint is /v1/saved (not /v1/favourites as documented)
export interface SavedResponse {
  count: number;
  results: Listing[];
}

export async function getSaved(token: string): Promise<SavedResponse> {
  return apiFetch<SavedResponse>('/v1/saved', {}, token);
}

export async function addSaved(token: string, listingId: string): Promise<{ ok: boolean; listing_id: string; saved_count: number }> {
  // Needs "listing_id" field, NOT "id" as documented
  return apiFetch('/v1/saved', {
    method: 'POST',
    body: JSON.stringify({ listing_id: listingId }),
  }, token);
}

export async function removeSaved(token: string, listingId: string): Promise<void> {
  await apiFetch(`/v1/saved/${listingId}`, { method: 'DELETE' }, token);
}

// Formatting helpers
export function formatPrice(priceRupees: number): string {
  if (priceRupees >= 10_000_000) {
    return `₹${(priceRupees / 10_000_000).toFixed(2)} Cr`;
  } else if (priceRupees >= 100_000) {
    return `₹${(priceRupees / 100_000).toFixed(2)} L`;
  }
  return `₹${priceRupees.toLocaleString('en-IN')}`;
}

export function formatProjectPrice(crores: number): string {
  // Project prices are in crores (documentation says rupees - WRONG)
  return `₹${crores.toFixed(2)} Cr`;
}

export function formatArea(sqft: number): string {
  return `${sqft.toLocaleString('en-IN')} sq.ft`;
}

export function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return isoString;
  }
}
