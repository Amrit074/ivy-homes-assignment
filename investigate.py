"""
Full re-fetch with correct auth token field name.
"""

import requests
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://solve.ivy.homes"
API_KEY = "IVY26-5C13E2AFECB7"
PASSWORD = "c48a4a267c"
API_HEADERS = {"X-API-Key": API_KEY}

def login(email):
    r = requests.post(f"{BASE_URL}/auth/login",
                      json={"email": email, "password": PASSWORD},
                      headers=API_HEADERS, timeout=10)
    d = r.json()
    print(f"  Login {email}: {r.status_code}")
    print(f"  Response fields: {list(d.keys())}")
    print(f"  expires_in: {d.get('expires_in')}")
    print(f"  user: {d.get('user')}")
    return d.get("access_token") or d.get("token")

def get_headers(token):
    return {**API_HEADERS, "Authorization": f"Bearer {token}"}

def fetch_all_pages(endpoint, token, extra_params=None, max_limit=200):
    params = dict(extra_params or {})
    params["limit"] = max_limit
    params["page"] = 1
    all_results = []
    total = None
    last_data = None
    headers = get_headers(token)

    while True:
        r = requests.get(f"{BASE_URL}{endpoint}", params=params, headers=headers, timeout=30)
        if not r.ok:
            print(f"  ERROR page {params['page']}: {r.status_code} {r.text[:100]}")
            break
        data = r.json()
        last_data = data
        results = data.get("results", [])
        all_results.extend(results)
        if total is None:
            total = data.get("total", 0)
        
        fetched_so_far = len(all_results)
        print(f"  Page {params['page']}: got {len(results)}, total so far {fetched_so_far}/{total}")
        
        if fetched_so_far >= total or len(results) == 0:
            break
        params["page"] += 1
        time.sleep(0.05)
    
    return all_results, total, last_data

def save_json(data, filename):
    import os
    os.makedirs("data", exist_ok=True)
    with open(f"data/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved data/{filename}")

print("=" * 70)
print("FULL RE-FETCH WITH CORRECT AUTH")
print("=" * 70)

# 1. Login ALL users and document
print("\n[1] Auth discovery...")
for email in ["demo1@ivy.homes", "demo2@ivy.homes", "demo3@ivy.homes"]:
    print(f"\n  User: {email}")
    token = login(email)
    print(f"  Token: {token[:30]}..." if token else "  FAILED")

# Use demo1
token = login("demo1@ivy.homes")
headers = get_headers(token)

# 2. Pagination investigation
print("\n[2] Pagination investigation...")
print("  Testing pages 1,2,3 with limit=10:")
ids_by_page = {}
for page in [1, 2, 3]:
    r = requests.get(f"{BASE_URL}/v1/listings",
                     params={"page": page, "limit": 10},
                     headers=headers, timeout=10)
    if r.ok:
        d = r.json()
        ids = [x["listing_id"] for x in d.get("results", [])]
        ids_by_page[page] = set(ids)
        print(f"  Page {page}: total={d.get('total')}, page_size={d.get('page_size')}, resp_keys={list(d.keys())}, ids={ids[:3]}")

p1_p2_overlap = ids_by_page.get(1, set()) & ids_by_page.get(2, set())
p2_p3_overlap = ids_by_page.get(2, set()) & ids_by_page.get(3, set())
print(f"  Page 1 & 2 overlap: {p1_p2_overlap}")
print(f"  Page 2 & 3 overlap: {p2_p3_overlap}")

# 3. Check what 'page_size' means vs 'limit'
print("\n[3] page vs offset test:")
r1 = requests.get(f"{BASE_URL}/v1/listings", params={"page": 1, "limit": 5}, headers=headers, timeout=10)
r2 = requests.get(f"{BASE_URL}/v1/listings", params={"page": 2, "limit": 5}, headers=headers, timeout=10)
if r1.ok and r2.ok:
    ids1 = [x["listing_id"] for x in r1.json()["results"]]
    ids2 = [x["listing_id"] for x in r2.json()["results"]]
    print(f"  Page 1 limit=5: {ids1}")
    print(f"  Page 2 limit=5: {ids2}")
    print(f"  Same? {ids1 == ids2}")

# 4. Fetch all listings fresh
print("\n[4] Fetching all listings fresh...")
listings_raw, listings_total, last_meta = fetch_all_pages("/v1/listings", token, max_limit=200)
print(f"\nFetched {len(listings_raw)} raw records, API total={listings_total}")
all_ids = [l["listing_id"] for l in listings_raw]
unique_ids = set(all_ids)
print(f"Unique IDs: {len(unique_ids)}")

# ID frequency
from collections import Counter, defaultdict
id_freq = Counter(all_ids)
print(f"Most common IDs:")
for lid, cnt in id_freq.most_common(5):
    print(f"  {lid}: {cnt} times")

save_json({
    "total_from_api": listings_total,
    "count_fetched": len(listings_raw),
    "unique_count": len(unique_ids),
    "last_page_meta": {k: v for k, v in (last_meta or {}).items() if k != "results"},
    "records": listings_raw
}, "listings_fresh.json")

# 5. Rentals
print("\n[5] Fetching all rentals...")
rentals_raw, rentals_total, _ = fetch_all_pages("/v1/rentals", token, max_limit=200)
rental_ids = [r["listing_id"] for r in rentals_raw]
print(f"Fetched {len(rentals_raw)} raw, {len(set(rental_ids))} unique, API total={rentals_total}")
save_json({
    "total_from_api": rentals_total,
    "count_fetched": len(rentals_raw),
    "unique_count": len(set(rental_ids)),
    "records": rentals_raw
}, "rentals_fresh.json")

# 6. Projects
print("\n[6] Fetching all projects...")
projects_raw, projects_total, _ = fetch_all_pages("/v1/projects", token, max_limit=200)
proj_ids = [p["project_id"] for p in projects_raw]
print(f"Fetched {len(projects_raw)} raw, {len(set(proj_ids))} unique, API total={projects_total}")

# Check project price units
print("\nProject price_max sample:")
seen_pids = set()
for p in projects_raw:
    if p["project_id"] not in seen_pids:
        seen_pids.add(p["project_id"])
        pmax = p.get("price_max")
        pmin = p.get("price_min")
        print(f"  {p['project_id']} ({p.get('apartment_name')}): price_min={pmin}, price_max={pmax}")
        if len(seen_pids) >= 5:
            break

save_json({
    "total_from_api": projects_total,
    "count_fetched": len(projects_raw),
    "unique_count": len(set(proj_ids)),
    "records": projects_raw
}, "projects_fresh.json")

# 7. Check single project endpoint
print("\n[7] Single project test...")
r = requests.get(f"{BASE_URL}/v1/projects/{projects_raw[0]['project_id']}",
                 headers=headers, timeout=10)
print(f"  Status: {r.status_code}")
if r.ok:
    print(f"  Data: {json.dumps(r.json(), indent=2)[:600]}")

# 8. Favourites test  
print("\n[8] Favourites endpoints...")
fav_paths = ["/v1/favourites", "/v1/favorites", "/v1/saved", "/v1/wishlist"]
for path in fav_paths:
    r = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=5)
    print(f"  GET {path}: {r.status_code} - {r.text[:100]}")

# 9. Analytics endpoints
print("\n[9] Analytics endpoints...")
for path in ["/v1/analytics/summary", "/v1/analytics", "/v1/stats", "/v1/summary", "/api/v1/analytics/summary"]:
    r = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=5)
    print(f"  {path}: {r.status_code}")

# 10. Sector 49 rentals
print("\n[10] Sector 49 rentals...")
sec49, sec49_total, _ = fetch_all_pages("/v1/rentals", token, extra_params={"locality": "sector 49"}, max_limit=200)
print(f"  Sector 49: {len(sec49)} raw, {len(set(r['listing_id'] for r in sec49))} unique, API total={sec49_total}")
save_json({"total_from_api": sec49_total, "count": len(sec49), "records": sec49}, "rentals_sector49_fresh.json")

# 11. Check refresh endpoint
print("\n[11] Auth refresh test...")
auth_resp = requests.post(f"{BASE_URL}/auth/login",
                          json={"email": "demo1@ivy.homes", "password": PASSWORD},
                          headers=API_HEADERS, timeout=10).json()
refresh_token = auth_resp.get("refresh_token")
refresh_url = auth_resp.get("refresh_url")
print(f"  refresh_token: {refresh_token[:30] if refresh_token else None}...")
print(f"  refresh_url: {refresh_url}")
if refresh_url:
    r = requests.post(f"{BASE_URL}{refresh_url}",
                      json={"refresh_token": refresh_token},
                      headers=API_HEADERS, timeout=10)
    print(f"  Refresh status: {r.status_code}")
    if r.ok:
        print(f"  Refresh response: {json.dumps(r.json())[:300]}")
    else:
        print(f"  Refresh error: {r.text[:200]}")

print("\nDONE!")
