# Ivy Homes Property Portal — Assignment Submission

**Candidate**: Amrit Raj  
**Email**: amritraj@mnnit.ac.in  
**API Key**: IVY26-5C13E2AFECB7  
**City**: Gurgaon  

---

## How to Run

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Log in with any of the demo accounts:

| Email | Password |
|-------|----------|
| demo1@ivy.homes | c48a4a267c |
| demo2@ivy.homes | c48a4a267c |
| demo3@ivy.homes | c48a4a267c |

For production deployment: [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

---

## Tools Used

- **LLM**: Claude (Sonnet 4.6) via Antigravity AI assistant — used for data analysis scripts, API exploration, and frontend code generation
- **Framework**: Next.js 15 with TypeScript, Tailwind CSS
- **Data analysis**: Python scripts using `requests` and `collections`
- **Deployment**: Vercel

---

## How I Worked Out Which Parts of the Documentation to Distrust

### Step 1: Initial API call — immediate failure

The very first API call using the documented query-parameter auth (`?api_key=...`) returned `401: "send your key in the X-API-Key request header, not as a query parameter"`. This was a clear signal that the documentation was unreliable, not just partially wrong.

### Step 2: Auth flow discovery

I systematically tested the login endpoint and discovered:
- The auth login also needs `X-API-Key` (undocumented)
- Response field is `access_token` not `token`
- `expires_in` is 900 seconds (15 min), not 86400 (24h)
- A `refresh_token` and `/auth/refresh` endpoint exist (doc says "no refresh flow")

This made me distrust every field name and parameter in the documentation.

### Step 3: Pagination — the critical discovery

After getting a token, I fetched pages 1, 2, and 3 of `/v1/listings` and found that **all three pages returned identical results**. The `page` parameter was being silently ignored. The actual response shape was completely different from the documentation:

- **Documented**: `{total, page, page_size, results}`
- **Actual**: `{limit, offset, count, total, has_more, results}`

Switching to offset-based pagination (`offset=0, 50, 100...`) revealed the full dataset. This was the most impactful finding: anyone using page-based pagination (as documented) would only ever see the same ~50 records.

### Step 4: Full dataset pull and analysis

With correct pagination, I fetched:
- 3,500 listings (API claims `total=3332` — another discrepancy)
- 1,320 rentals  
- 400 projects

### Step 5: Endpoint probing

Tested every documented endpoint path:
- `/v1/listing/{id}` → 404 (correct: `/v1/listings/{id}`)
- `/v1/listings/{id}/similar` → 404
- `/v1/favourites` → 404 (correct: `/v1/saved`)
- `/v1/analytics/summary` → 404

For favourites, I tested multiple path variations (`/v1/saved`, `/v1/favorites`, `/v1/wishlist`) and found `/v1/saved` works.

### Step 6: Data quality analysis

Once I had the full dataset, I ran systematic checks:

**Corrupt listings**: Listings with `carpet_area < 100 sqft` for 2+ bedroom apartments. Found 120+ `MAG-` prefix listings with 70-90 sqft carpet but realistic prices (₹1.5-1.8 Cr). Also found listings with negative prices.

**Fake listings**: Grouped by `posted_by_contact`. Found a sharp distribution: most phones appear for 2-10 listings (plausible for real agents), but some appear for 25-35 listings with 4-6 different `posted_by_name` values (e.g., same number listed as "Suresh Nair", "Nisha Kulkarni", "Shreya Iyer", "Varun Verma"). One contact number being used by 4 different people across 35 listings is the clearest possible fake signal.

**Project prices**: Values like 1.66 and 4.54 for `price_max` are obviously not rupees. Cross-referencing with listing prices (median ~₹1.45 Cr in rupees), these must be in crores. Additionally, 184 of 381 projects have `price_min > price_max`, indicating the fields are swapped in those records.

---

## What I Checked That Turned Out to Be Fine

These are the hypotheses I tested that did NOT pan out:

1. **Timestamps being in a different timezone**: Listed `posted_at` values are in UTC (Z suffix) — this is correct per documentation. Only the `/health` endpoint uses IST.

2. **Locality filter returning wrong records**: The filter correctly returns only matching-locality records. What's wrong is the `total` count (it undercounts), not the records themselves.

3. **BHK filter being broken**: `bhk=2` correctly filters to 2-bedroom listings.

4. **Price filter**: `min_price`/`max_price` work correctly as filters.

5. **Rental prices in a different unit**: Rental `price` (monthly rent) values of ₹12,000-₹80,000 are in rupees and look correct.

6. **Duplicate listing IDs**: After correctly using offset pagination, there are zero duplicate listing IDs. The earlier apparent duplicates were an artifact of the page parameter being ignored.

7. **Sort parameters broken**: `sort_by=price&order=desc` does correctly sort by price descending.

8. **Project `total_listings` being a global count**: It is per-project, just frequently wrong.

---

## What I Would Do With Another Two Days

1. **Q9 (fake listings) refinement**: I used a threshold of "same phone, 3+ different seller names" which is conservative. With more time I'd cross-reference with `/v1/saved` access patterns, description similarity, and IP/timing patterns if available.

2. **Q7 (costliest project) verification**: The project price unit ambiguity (crores vs lakhs) and the 184 swapped min/max entries deserve deeper verification — perhaps by fetching associated listings and comparing their prices to the project's claimed range.

3. **Better insights UI**: The insights screen would show time-series charts, a Gurgaon heatmap of price by locality, and better visualization of the fake listing patterns.

4. **Full test suite**: Unit tests for the API client, especially the token refresh flow.

5. **Server-side rendering**: Move the data-heavy pages to SSR for better initial load.

---

## Architecture

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout with AuthProvider
│   │   ├── page.tsx            # Redirect to listings/login
│   │   ├── login/page.tsx      # Login form
│   │   ├── listings/
│   │   │   ├── page.tsx        # Browse + filter listings
│   │   │   └── [id]/page.tsx   # Single listing detail
│   │   ├── rentals/
│   │   │   ├── page.tsx        # Browse rentals
│   │   │   └── [id]/page.tsx   # Single rental
│   │   ├── projects/
│   │   │   ├── page.tsx        # Browse projects
│   │   │   └── [id]/page.tsx   # Single project
│   │   ├── saved/page.tsx      # Saved listings
│   │   └── insights/page.tsx   # Analytics dashboard
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── ListingCard.tsx
│   │   ├── RentalCard.tsx
│   │   └── ProjectCard.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx     # Auth + token refresh
│   └── lib/
│       └── api.ts              # API client (with all fixes)
```

---

## Key API Fixes Applied

| Issue | Documented | Actual |
|-------|-----------|--------|
| Auth method | Query param `?api_key=` | `X-API-Key` header |
| Login needs key | Not mentioned | Yes, `X-API-Key` required |
| Token field | `token` | `access_token` |
| Token lifetime | 86400s (24h) | 900s (15min) |
| Refresh flow | None | `POST /auth/refresh` with `refresh_token` |
| Pagination | `page` param | `offset` param |
| Response shape | `{total, page, page_size, results}` | `{limit, offset, count, total, has_more, results}` |
| Max per request | 200 | 50 |
| Single listing path | `/v1/listing/{id}` | `/v1/listings/{id}` |
| Similar listings | `/v1/listings/{id}/similar` | 404, doesn't exist |
| Favourites path | `/v1/favourites` | `/v1/saved` |
| Favourites add | `{id: '...'}` | `{listing_id: '...'}` |
| Analytics | `/v1/analytics/summary` | 404, doesn't exist |
| Project prices | Rupees (integer) | Crores (float) |
| Listings returned | Active only | Both active and inactive |
