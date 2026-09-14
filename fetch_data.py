"""
Ivy Homes API Data Fetcher - v3
Findings so far:
1. API key must go in X-API-Key header (doc says query param) 
2. Auth login ALSO needs X-API-Key header (undocumented)
3. ALL data endpoints need Bearer token (doc implied key alone was enough)
4. /v1/analytics/summary returns 404 (endpoint doesn't exist)
5. /v1/listing (singular, no id) returns 404 (expected)
6. /v1/listing/{id} singular returns 404 (correct path is /v1/listings/{id})
"""

import requests
import json
import time
import os

BASE_URL = "https://solve.ivy.homes"
API_KEY = "IVY26-5C13E2AFECB7"
PASSWORD = "c48a4a267c"
EMAIL = "demo1@ivy.homes"

API_HEADERS = {"X-API-Key": API_KEY}

def get_token():
    """Login and get bearer token."""
    resp = requests.post(f"{BASE_URL}/auth/login", 
                         json={"email": EMAIL, "password": PASSWORD},
                         headers=API_HEADERS,
                         timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("token") or data.get("access_token")
        print(f"  Logged in, token: {token[:30]}...")
        return token, data
    else:
        print(f"  Login failed {resp.status_code}: {resp.text}")
        return None, None

def make_headers(token=None):
    h = dict(API_HEADERS)
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def fetch_all_pages(endpoint, token, extra_params=None, max_limit=200):
    """Fetch all pages from a paginated endpoint."""
    params = dict(extra_params or {})
    params["limit"] = max_limit
    params["page"] = 1

    all_results = []
    total = None
    last_data = None

    headers = make_headers(token)

    while True:
        print(f"  Fetching {endpoint} page {params['page']}...", end=" ")
        resp = requests.get(f"{BASE_URL}{endpoint}", params=params, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"ERROR {resp.status_code}: {resp.text[:200]}")
            break

        data = resp.json()
        last_data = data
        results = data.get("results", [])
        all_results.extend(results)

        if total is None:
            total = data.get("total", 0)

        print(f"got {len(results)}, total={len(all_results)}/{total}")

        if len(all_results) >= total or len(results) == 0:
            break

        params["page"] += 1
        time.sleep(0.05)

    return all_results, total, last_data

def fetch_single(endpoint, token=None, extra_params=None):
    """Fetch a single endpoint."""
    params = extra_params or {}
    resp = requests.get(f"{BASE_URL}{endpoint}", params=params, 
                        headers=make_headers(token), timeout=30)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

def post_req(endpoint, body, token=None):
    resp = requests.post(f"{BASE_URL}{endpoint}", json=body,
                         headers=make_headers(token), timeout=30)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

def delete_req(endpoint, token=None):
    resp = requests.delete(f"{BASE_URL}{endpoint}",
                           headers=make_headers(token), timeout=30)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

def save_json(data, filename):
    os.makedirs("data", exist_ok=True)
    with open(f"data/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved data/{filename}")

print("=" * 60)
print("IVY HOMES API DATA FETCHER v3")
print("=" * 60)

# 1. Health check
print("\n[1] Health check...")
status, health = fetch_single("/health")
print(f"  Status: {status}, Response: {json.dumps(health)}")
save_json({"status_code": status, "response": health}, "health.json")

# 2. Auth - login needs X-API-Key header too
print("\n[2] Auth tests...")
# Try login WITHOUT API key header
r1 = requests.post(f"{BASE_URL}/auth/login", 
                   json={"email": EMAIL, "password": PASSWORD}, timeout=10)
print(f"  Login without X-API-Key: {r1.status_code} - {r1.text[:200]}")

# Try login WITH API key header
r2 = requests.post(f"{BASE_URL}/auth/login",
                   json={"email": EMAIL, "password": PASSWORD},
                   headers=API_HEADERS, timeout=10)
print(f"  Login with X-API-Key: {r2.status_code}")
save_json({
    "without_key": {"status": r1.status_code, "body": r1.text},
    "with_key": {"status": r2.status_code, "body": r2.json() if r2.ok else r2.text}
}, "auth_tests.json")

# 3. Get token and test all 3 demo users
print("\n[3] Logging in all demo users...")
tokens = {}
for email in ["demo1@ivy.homes", "demo2@ivy.homes", "demo3@ivy.homes"]:
    r = requests.post(f"{BASE_URL}/auth/login",
                      json={"email": email, "password": PASSWORD},
                      headers=API_HEADERS, timeout=10)
    if r.ok:
        d = r.json()
        tokens[email] = d.get("token") or d.get("access_token")
        print(f"  {email}: OK, expires_in={d.get('expires_in')}")
    else:
        print(f"  {email}: FAILED {r.status_code} {r.text}")

save_json({"tokens": {k: v[:20]+"..." for k, v in tokens.items()}}, "all_tokens.json")

# Use demo1 token for data fetching
token = tokens.get("demo1@ivy.homes")
if not token:
    print("ERROR: Could not get token!")
    exit(1)

# 4. Fetch ALL listings
print("\n[4] Fetching all listings...")
listings, listings_total, listings_last_meta = fetch_all_pages("/v1/listings", token, max_limit=200)
print(f"  DONE: {len(listings)} listings, API total={listings_total}")

# Check if is_live field exists
if listings:
    sample = listings[0]
    print(f"  Sample listing keys: {list(sample.keys())}")
    has_is_live = "is_live" in sample
    print(f"  has is_live: {has_is_live}")

save_json({
    "total_from_api": listings_total,
    "count_fetched": len(listings),
    "last_page_meta": {k: v for k, v in (listings_last_meta or {}).items() if k != "results"},
    "records": listings
}, "listings_all.json")

# 5. Fetch ALL rentals
print("\n[5] Fetching all rentals...")
rentals, rentals_total, rentals_last_meta = fetch_all_pages("/v1/rentals", token, max_limit=200)
print(f"  DONE: {len(rentals)} rentals, API total={rentals_total}")
if rentals:
    print(f"  Sample rental keys: {list(rentals[0].keys())}")
save_json({
    "total_from_api": rentals_total,
    "count_fetched": len(rentals),
    "records": rentals
}, "rentals_all.json")

# 6. Fetch ALL projects
print("\n[6] Fetching all projects...")
projects, projects_total, projects_last_meta = fetch_all_pages("/v1/projects", token, max_limit=200)
print(f"  DONE: {len(projects)} projects, API total={projects_total}")
if projects:
    print(f"  Sample project keys: {list(projects[0].keys())}")
save_json({
    "total_from_api": projects_total,
    "count_fetched": len(projects),
    "records": projects
}, "projects_all.json")

# 7. Analytics - test multiple paths
print("\n[7] Testing analytics endpoints...")
analytics_paths = [
    "/v1/analytics/summary",
    "/v1/analytics",
    "/analytics/summary",
    "/v1/summary",
]
analytics_results = {}
for path in analytics_paths:
    s, b = fetch_single(path, token)
    analytics_results[path] = {"status": s, "snippet": (json.dumps(b) if isinstance(b, dict) else b)[:300]}
    print(f"  {path}: {s}")
save_json(analytics_results, "analytics_tests.json")

# 8. Test individual listing endpoint
print("\n[8] Testing single listing endpoint paths...")
if listings:
    test_id = listings[0]["listing_id"]
    paths = [
        f"/v1/listings/{test_id}",    # correct (listings plural)
        f"/v1/listing/{test_id}",     # documented (singular)
        f"/v1/listings/{test_id}/similar",  # similar listings
    ]
    ep_results = {}
    for path in paths:
        s, b = fetch_single(path, token)
        ep_results[path] = {"status": s, "snippet": (json.dumps(b)[:300] if isinstance(b, dict) else str(b)[:300])}
        print(f"  {path}: {s}")
    save_json(ep_results, "single_listing_tests.json")

# 9. Sector 49 rentals (for Q5)
print("\n[9] Fetching Sector 49 rentals...")
sec49_rentals, sec49_total, _ = fetch_all_pages("/v1/rentals", token, 
                                                 extra_params={"locality": "sector 49"}, 
                                                 max_limit=200)
print(f"  Sector 49 rentals: {len(sec49_rentals)}, total={sec49_total}")
save_json({
    "locality": "sector 49",
    "total_from_api": sec49_total,
    "count": len(sec49_rentals),
    "records": sec49_rentals
}, "rentals_sector49.json")

# 10. Test favourites
print("\n[10] Testing favourites...")
s, b = fetch_single("/v1/favourites", token)
print(f"  GET /v1/favourites: {s} - {json.dumps(b)[:200] if isinstance(b, dict) else b[:200]}")
save_json({"get_status": s, "get_body": b}, "favourites_test.json")

# 11. Test filter parameters to find which ones work
print("\n[11] Testing filter params...")
filter_tests = {}

if listings:
    # Get all localities in dataset
    localities = list(set(l.get("locality","") for l in listings))[:5]
    
    for loc in localities[:3]:
        r = requests.get(f"{BASE_URL}/v1/listings",
                         params={"locality": loc, "limit": 200},
                         headers=make_headers(token), timeout=15)
        if r.ok:
            api_count = r.json().get("total")
            manual_count = sum(1 for l in listings if l.get("locality","").lower() == loc.lower())
            filter_tests[f"locality={loc}"] = {
                "api_total": api_count,
                "manual_count": manual_count,
                "filter_works": api_count == manual_count
            }
            print(f"  locality={loc}: api={api_count}, manual={manual_count}")

save_json(filter_tests, "filter_tests.json")

# 12. Check is_live field specifically
print("\n[12] Checking is_live field...")
if listings:
    live_count = sum(1 for l in listings if l.get("is_live") == True)
    not_live_count = sum(1 for l in listings if l.get("is_live") == False)
    no_field = sum(1 for l in listings if "is_live" not in l)
    print(f"  is_live=True: {live_count}")
    print(f"  is_live=False: {not_live_count}")
    print(f"  no is_live field: {no_field}")

print("\n" + "=" * 60)
print("DATA FETCH COMPLETE!")
print(f"  Listings:       {len(listings)} (API total={listings_total})")
print(f"  Rentals:        {len(rentals)} (API total={rentals_total})")
print(f"  Projects:       {len(projects)} (API total={projects_total})")
print(f"  Sector49 rent:  {len(sec49_rentals)}")
print("=" * 60)
