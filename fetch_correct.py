"""
CORRECT data fetch using offset-based pagination (not page-based as documented).
Also tests /v1/saved for favourites.
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

def login():
    r = requests.post(f"{BASE_URL}/auth/login",
                      json={"email": "demo1@ivy.homes", "password": PASSWORD},
                      headers=API_HEADERS, timeout=10)
    return r.json()["access_token"]

def get_headers(token):
    return {**API_HEADERS, "Authorization": f"Bearer {token}"}

def fetch_all_offset(endpoint, token, extra_params=None, batch_size=200):
    """Fetch all records using offset-based pagination."""
    params = dict(extra_params or {})
    params["limit"] = batch_size
    params["offset"] = 0

    all_results = []
    total = None
    last_data = None
    headers = get_headers(token)
    batch = 0

    while True:
        batch += 1
        r = requests.get(f"{BASE_URL}{endpoint}", params=params, headers=headers, timeout=30)
        if not r.ok:
            print(f"  ERROR offset={params['offset']}: {r.status_code} {r.text[:100]}")
            break
        
        data = r.json()
        last_data = data
        results = data.get("results", [])
        all_results.extend(results)
        
        if total is None:
            total = data.get("total", 0)
            # Print response shape to understand
            print(f"  First response keys: {list(data.keys())}")
            print(f"  API total: {total}, has_more: {data.get('has_more')}")
        
        fetched = len(all_results)
        has_more = data.get("has_more", False)
        print(f"  Batch {batch} (offset={params['offset']}): got {len(results)}, total fetched={fetched}/{total}, has_more={has_more}")
        
        if not has_more or len(results) == 0:
            break
        
        params["offset"] += batch_size
        time.sleep(0.05)
    
    return all_results, total, last_data

def save_json(data, filename):
    import os
    os.makedirs("data", exist_ok=True)
    with open(f"data/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved data/{filename}")

print("=" * 70)
print("CORRECT DATA FETCH (OFFSET-BASED PAGINATION)")
print("=" * 70)

token = login()
headers = get_headers(token)

# 1. Fetch all listings with offset pagination
print("\n[1] Fetching all listings (offset-based)...")
listings, l_total, l_meta = fetch_all_offset("/v1/listings", token, batch_size=200)
print(f"\nListing results:")
print(f"  Total fetched: {len(listings)}")
print(f"  API total: {l_total}")
print(f"  Unique IDs: {len(set(l['listing_id'] for l in listings))}")
save_json({"total_from_api": l_total, "count_fetched": len(listings), "records": listings}, "listings_correct.json")

# 2. Fetch all rentals
print("\n[2] Fetching all rentals (offset-based)...")
rentals, r_total, r_meta = fetch_all_offset("/v1/rentals", token, batch_size=200)
print(f"\nRental results:")
print(f"  Total fetched: {len(rentals)}")
print(f"  API total: {r_total}")
print(f"  Unique IDs: {len(set(r['listing_id'] for r in rentals))}")
save_json({"total_from_api": r_total, "count_fetched": len(rentals), "records": rentals}, "rentals_correct.json")

# 3. Fetch all projects
print("\n[3] Fetching all projects (offset-based)...")
projects, p_total, p_meta = fetch_all_offset("/v1/projects", token, batch_size=200)
print(f"\nProject results:")
print(f"  Total fetched: {len(projects)}")
print(f"  API total: {p_total}")
print(f"  Unique IDs: {len(set(p['project_id'] for p in projects))}")
save_json({"total_from_api": p_total, "count_fetched": len(projects), "records": projects}, "projects_correct.json")

# 4. Sector 49 rentals
print("\n[4] Fetching Sector 49 rentals...")
sec49, sec49_total, _ = fetch_all_offset("/v1/rentals", token, 
                                          extra_params={"locality": "sector 49"},
                                          batch_size=200)
print(f"  Sector 49: {len(sec49)}, API total={sec49_total}")
save_json({"locality": "sector 49", "total": sec49_total, "count": len(sec49), "records": sec49}, 
          "rentals_sector49_correct.json")

# 5. Test /v1/saved endpoint
print("\n[5] Testing /v1/saved endpoint...")
saved_resp = requests.get(f"{BASE_URL}/v1/saved", headers=headers, timeout=10)
print(f"  GET /v1/saved: {saved_resp.status_code}")
print(f"  Response: {saved_resp.json()}")

# Add a listing to saved
if listings:
    test_lid = listings[0]["listing_id"]
    add_resp = requests.post(f"{BASE_URL}/v1/saved",
                             json={"listing_id": test_lid},
                             headers=headers, timeout=10)
    print(f"\n  POST /v1/saved with listing_id: {add_resp.status_code}")
    print(f"  Response: {add_resp.text[:200]}")
    
    # Try id field
    add_resp2 = requests.post(f"{BASE_URL}/v1/saved",
                              json={"id": test_lid},
                              headers=headers, timeout=10)
    print(f"\n  POST /v1/saved with id: {add_resp2.status_code}")
    print(f"  Response: {add_resp2.text[:200]}")
    
    # Check saved again
    saved_after = requests.get(f"{BASE_URL}/v1/saved", headers=headers, timeout=10)
    print(f"\n  GET /v1/saved after add: {saved_after.json()}")
    
    # Try DELETE /v1/saved/{id}
    del_resp = requests.delete(f"{BASE_URL}/v1/saved/{test_lid}", headers=headers, timeout=10)
    print(f"\n  DELETE /v1/saved/{test_lid}: {del_resp.status_code} {del_resp.text[:100]}")

# 6. Project price investigation
print("\n[6] Project price unit investigation...")
from collections import Counter
price_maxes = [(p["project_id"], p.get("apartment_name"), p.get("price_max"), p.get("price_min")) 
               for p in projects if p.get("price_max")]
print(f"Sample projects (first 10):")
for pid, name, pmax, pmin in price_maxes[:10]:
    # If in crores: 1.66 Cr = 16.6M, 4.54 Cr = 45.4M - reasonable for Gurgaon luxury
    # If in lakhs: 1.66L = 166000 - too cheap
    print(f"  {pid} ({name}): min={pmin}, max={pmax}")

# Look at listing prices for comparison
l_prices = sorted([l.get("price", 0) for l in listings if l.get("price")])
print(f"\nListing price range (in whatever unit):")
print(f"  Min: {l_prices[0]:,}")
print(f"  Max: {l_prices[-1]:,}")
print(f"  Median: {l_prices[len(l_prices)//2]:,}")
print(f"  Sample: {l_prices[:5]}")

# Listing prices are in full rupees (e.g. 6000000 = 60L), consistent with docs
# Project prices: 1.66, 4.54... these must be in crores
print("\nConclusion: Project prices appear to be in crores, not rupees as documented")
print("  1.66 crore = 16,600,000 rupees (reasonable for Gurgaon)")
print("  Compare to listing max: ", l_prices[-1])

# 7. Check filter functionality with offset
print("\n[7] Testing filters with offset pagination...")
# Locality filter
r = requests.get(f"{BASE_URL}/v1/listings",
                 params={"locality": "sector 49", "limit": 5, "offset": 0},
                 headers=headers, timeout=10)
if r.ok:
    d = r.json()
    print(f"  locality=sector 49: total={d.get('total')}, has_more={d.get('has_more')}")
    sample_locs = [x.get("locality") for x in d.get("results", [])]
    print(f"  Sample localities in response: {sample_locs}")

# BHK filter
r = requests.get(f"{BASE_URL}/v1/listings",
                 params={"bhk": 2, "limit": 5, "offset": 0},
                 headers=headers, timeout=10)
if r.ok:
    d = r.json()
    print(f"  bhk=2: total={d.get('total')}")
    sample_beds = [x.get("bedroom") for x in d.get("results", [])]
    print(f"  Sample bedrooms: {sample_beds}")

# Sort by price
r = requests.get(f"{BASE_URL}/v1/listings",
                 params={"sort_by": "price", "order": "desc", "limit": 5, "offset": 0},
                 headers=headers, timeout=10)
if r.ok:
    d = r.json()
    prices = [x.get("price") for x in d.get("results", [])]
    print(f"  sort_by=price desc: prices={prices}")

print("\nDONE!")
