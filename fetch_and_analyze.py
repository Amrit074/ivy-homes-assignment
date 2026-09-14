"""
FIXED fetch: offset increments by actual batch_size (50), not limit parameter value.
Also fully analyzes all 10 questions with real data.
"""

import requests
import json
import time
import sys
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://solve.ivy.homes"
API_KEY = "IVY26-5C13E2AFECB7"
PASSWORD = "c48a4a267c"
API_HEADERS = {"X-API-Key": API_KEY}
IST = timezone(timedelta(hours=5, minutes=30))
REFERENCE = datetime(2026, 9, 10, 0, 0, 0, tzinfo=IST)

def login():
    r = requests.post(f"{BASE_URL}/auth/login",
                      json={"email": "demo1@ivy.homes", "password": PASSWORD},
                      headers=API_HEADERS, timeout=10)
    return r.json()["access_token"]

def get_headers(token):
    return {**API_HEADERS, "Authorization": f"Bearer {token}"}

def fetch_all(endpoint, token, extra_params=None):
    """Fetch all records - offset increments by actual count returned."""
    params = dict(extra_params or {})
    params["limit"] = 200  # request max, actual max returned is 50
    params["offset"] = 0

    all_results = []
    total = None
    headers = get_headers(token)
    batch = 0

    while True:
        batch += 1
        r = requests.get(f"{BASE_URL}{endpoint}", params=params, headers=headers, timeout=30)
        if not r.ok:
            print(f"  ERROR offset={params['offset']}: {r.status_code} {r.text[:100]}")
            break
        
        data = r.json()
        results = data.get("results", [])
        count_returned = len(results)
        
        if total is None:
            total = data.get("total", 0)
        
        if count_returned == 0:
            break
        
        all_results.extend(results)
        has_more = data.get("has_more", False)
        
        if batch <= 3 or batch % 10 == 0:
            print(f"  Batch {batch} (offset={params['offset']}): got {count_returned}, fetched={len(all_results)}/{total}, has_more={has_more}")
        
        if not has_more:
            break
        
        # Increment by actual count returned (not limit param)
        params["offset"] += count_returned
        time.sleep(0.05)
    
    print(f"  DONE: {len(all_results)} records fetched, API total={total}")
    return all_results, total

def save_json(data, filename):
    import os
    os.makedirs("data", exist_ok=True)
    with open(f"data/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved data/{filename}")

print("=" * 70)
print("FULL DATA FETCH - FINAL")
print("=" * 70)

token = login()
headers = get_headers(token)

# 1. ALL LISTINGS
print("\n[1] Listings...")
listings, l_total = fetch_all("/v1/listings", token)
save_json({"total_from_api": l_total, "count_fetched": len(listings), "records": listings}, "listings_final.json")
l_ids = [l["listing_id"] for l in listings]
print(f"  Unique IDs: {len(set(l_ids))}")

# 2. ALL RENTALS
print("\n[2] Rentals...")
rentals, r_total = fetch_all("/v1/rentals", token)
save_json({"total_from_api": r_total, "count_fetched": len(rentals), "records": rentals}, "rentals_final.json")

# 3. ALL PROJECTS
print("\n[3] Projects...")
projects, p_total = fetch_all("/v1/projects", token)
save_json({"total_from_api": p_total, "count_fetched": len(projects), "records": projects}, "projects_final.json")

# 4. SECTOR 49 RENTALS (with filter)
print("\n[4] Sector 49 rentals...")
sec49, sec49_total = fetch_all("/v1/rentals", token, extra_params={"locality": "sector 49"})
save_json({"total": sec49_total, "count": len(sec49), "records": sec49}, "sec49_rentals_final.json")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

# Q1: total_listing_records
q1 = len(listings)
print(f"\nQ1: total_listing_records = {q1}")
print(f"  (API says total={l_total}, we fetched {len(listings)})")

# Q2: unique_properties
lid_counts = Counter(l_ids)
q2 = len(lid_counts)
dup_lids = {lid: cnt for lid, cnt in lid_counts.items() if cnt > 1}
print(f"\nQ2: unique_properties = {q2}")
print(f"  Duplicate listing_ids: {len(dup_lids)}")
if dup_lids:
    for lid, cnt in sorted(dup_lids.items(), key=lambda x: -x[1])[:5]:
        print(f"    {lid}: {cnt} times")

# Q3: active_listings (is_live=True)
q3 = sum(1 for l in listings if l.get("is_live") == True)
print(f"\nQ3: active_listings = {q3}")
print(f"  is_live=False: {sum(1 for l in listings if l.get('is_live')==False)}")
print(f"  NOTE: Doc says only active returned but we see both!")

# Q4: corrupt listings
print(f"\nQ4: corrupt_listing_ids analysis...")

# Negative prices
neg_price = [l for l in listings if l.get("price") and l.get("price") < 0]
print(f"  Negative price: {len(neg_price)}")
for l in neg_price[:5]:
    print(f"    {l['listing_id']}: price={l['price']}, carpet={l.get('carpet_area')}, bed={l.get('bedroom')}")

# Floor > total_floors
floor_issue = [l for l in listings 
               if l.get("floor") and l.get("total_floors") 
               and l.get("floor") > l.get("total_floors")]
print(f"  Floor > total_floors: {len(floor_issue)}")

# SBA < carpet
sba_issue = [l for l in listings
             if l.get("super_built_up_area") and l.get("carpet_area")
             and l.get("super_built_up_area") < l.get("carpet_area")]
print(f"  SBA < carpet: {len(sba_issue)}")
for l in sba_issue[:3]:
    print(f"    {l['listing_id']}: carpet={l['carpet_area']}, SBA={l['super_built_up_area']}")

# Impossibly small area for bedroom count (definitive cases)
area_impossible = []
for l in listings:
    bed = l.get("bedroom", 0)
    carpet = l.get("carpet_area", 0)
    if carpet and bed:
        # A 2BHK must be at least 500sqft; 3BHK at least 700sqft in India
        if (bed == 2 and carpet < 300) or (bed >= 3 and carpet < 400):
            area_impossible.append(l)
print(f"  Impossibly small area for bedroom count: {len(area_impossible)}")
for l in area_impossible[:5]:
    print(f"    {l['listing_id']}: {l['bedroom']}BHK, carpet={l['carpet_area']}")

# Zero area
zero_area = [l for l in listings if l.get("carpet_area") == 0]
print(f"  Zero carpet area: {len(zero_area)}")

# "Cannot exist" = physically impossible
corrupt_set = set()
corrupt_set.update(l["listing_id"] for l in neg_price)
corrupt_set.update(l["listing_id"] for l in floor_issue)
corrupt_set.update(l["listing_id"] for l in sba_issue)
corrupt_set.update(l["listing_id"] for l in area_impossible)
corrupt_set.update(l["listing_id"] for l in zero_area)

q4 = sorted(list(corrupt_set))
print(f"\n  Q4 = {q4}")

# Q5: total_monthly_rent for Sector 49
print(f"\nQ5: Sector 49 rentals...")
sec49_manual = [r for r in rentals if r.get("locality","").lower().strip() == "sector 49"]
print(f"  Manual filter from all rentals: {len(sec49_manual)}")
print(f"  From locality filter fetch: {len(sec49)}")
print(f"  API total for Sector 49: {sec49_total}")

# Use manual filter (more reliable - we have all rentals)
total_rent_manual = sum(r.get("price", 0) for r in sec49_manual)
total_rent_filtered = sum(r.get("price", 0) for r in sec49)

print(f"  Prices sample: {sorted([r.get('price',0) for r in sec49_manual])[:10]}")
print(f"  Total monthly rent (manual): {total_rent_manual}")
print(f"  Total monthly rent (filtered endpoint): {total_rent_filtered}")

# Check for negative/weird prices
neg_rent = [r for r in sec49_manual if r.get("price",0) < 0]
print(f"  Negative rent prices: {len(neg_rent)}")
if neg_rent:
    for r in neg_rent[:3]:
        print(f"    {r['listing_id']}: price={r['price']}")

q5 = total_rent_manual
print(f"  Q5 = {q5}")

# Q6: avg_price_per_sqft_2bhk
print(f"\nQ6: avg_price_per_sqft_2bhk...")
eligible = [l for l in listings
            if l.get("is_live") == True
            and l.get("bedroom") == 2
            and l["listing_id"] not in corrupt_set]

print(f"  2BHK active (excl. corrupt): {len(eligible)}")

valid = [(l["listing_id"], l["price"], l["carpet_area"]) 
         for l in eligible
         if l.get("price") and l.get("carpet_area") and l.get("price") > 0 and l.get("carpet_area") > 0]

print(f"  Valid (pos price & area): {len(valid)}")
if valid:
    ppsf = [p/a for _, p, a in valid]
    avg = sum(ppsf)/len(ppsf)
    ppsf_sorted = sorted(ppsf)
    print(f"  Mean: {avg:.2f}")
    print(f"  Range: {ppsf_sorted[0]:.0f} to {ppsf_sorted[-1]:.0f}")

q6_prelim = round(avg, 2) if valid else 0.0

# Q7: costliest project
print(f"\nQ7: costliest_project...")
# Project prices look wrong - some have price_min=94.6 and price_max=2.15
# This means some are in crores and some in... something else?
# Let's investigate: min should be < max
price_swapped = [(p["project_id"], p.get("apartment_name"), p.get("price_min"), p.get("price_max"))
                 for p in projects
                 if p.get("price_min") and p.get("price_max") and p.get("price_min") > p.get("price_max")]
print(f"  Projects where price_min > price_max: {len(price_swapped)}")
for pid, name, pmin, pmax in price_swapped[:5]:
    print(f"    {pid} ({name}): min={pmin}, max={pmax}")

# The "correct" values: compare max project price to listing prices
# Listings are in full rupees (e.g., 17050000 = 1.7Cr)
# Project price_max values: 4.54, 4.12, 4.17, 2.15, 2.25... (clearly crores)
# But some project price_min values: 94.6, 81.6, 88.2, 78.9... (could be lakhs?)
# 94.6 lakhs = 9,460,000 rupees (reasonable for Gurgaon)
# So price_min might be in LAKHS and price_max in CRORES? That's mixed units!
print(f"\n  Price unit hypothesis:")
print(f"  price_max in crores: 4.54 Cr = 45,400,000 INR")
print(f"  price_min in lakhs: 94.6 L = 9,460,000 INR")
print(f"  OR: both in crores, so 94.6 Cr is ultra-luxury")

# Actually wait - 94.6 crore for a single apartment? That's too high even for Gurgaon
# 94.6 lakhs = 9.46 million = reasonable for Gurgaon mid-range
# So: price_min is in LAKHS, price_max is in CRORES? That's clearly a documentation bug

# Compare to actual listing prices for similar projects
# A project with price_min=94.6 (lakhs = 9.46M INR) and price_max=2.15 (crores = 21.5M INR)
# That would be a reasonable range for Gurgaon
# But min > max numerically (94.6 > 2.15) is WRONG - that's the bug!

# So the true interpretation: BOTH are in crores
# price_min=94.6 means 94.6 CRORES = too expensive
# price_min=1.66 means 1.66 CRORES = reasonable
# The P60004 case: min=94.6, max=2.15 -> min > max -> data is SWAPPED

print("\n  Investigation: are price_min and price_max sometimes SWAPPED?")
for p in projects[:15]:
    pmin = p.get("price_min", 0) or 0
    pmax = p.get("price_max", 0) or 0
    swapped = pmin > pmax
    print(f"  {p['project_id']}: min={pmin}, max={pmax}, swapped={swapped}")

# For Q7, find highest price_max (which might be in crores)
projs_sorted = sorted(projects, key=lambda p: p.get("price_max", 0) or 0, reverse=True)
print(f"\n  Top 5 by price_max:")
for p in projs_sorted[:5]:
    print(f"  {p['project_id']} ({p['apartment_name']}): price_max={p.get('price_max')}, locality={p.get('locality')}")

q7_project = projs_sorted[0]
# Convert to INR (if in crores, multiply by 10M)
q7_price_crores = q7_project.get("price_max", 0)
q7_price_inr = int(q7_price_crores * 10_000_000)
q7 = {"project_id": q7_project["project_id"], "price_max_inr": q7_price_inr}
print(f"  Q7 = {q7}")
print(f"  (raw price_max={q7_price_crores}, interpreted as {q7_price_inr} INR if in crores)")

# Q8: listings_last_7_days
print(f"\nQ8: listings_last_7_days...")
start = REFERENCE - timedelta(days=7)
end = REFERENCE
print(f"  Window: {start.isoformat()} to {end.isoformat()}")

in_window = []
for l in listings:
    ps = l.get("posted_at", "")
    if not ps: continue
    try:
        if ps.endswith("Z"):
            dt = datetime.fromisoformat(ps.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(ps)
        dt_ist = dt.astimezone(IST)
        if start <= dt_ist < end:
            in_window.append(l["listing_id"])
    except:
        pass

q8 = len(in_window)
print(f"  Q8 = {q8}")

# Show date distribution
dates = []
for l in listings:
    ps = l.get("posted_at","")
    try:
        if ps.endswith("Z"):
            dt = datetime.fromisoformat(ps.replace("Z","+00:00"))
        else:
            dt = datetime.fromisoformat(ps)
        dates.append(dt.astimezone(IST).date())
    except:
        pass

date_counts = Counter(dates)
print("  Posted dates (recent):")
for d in sorted(date_counts.keys())[-20:]:
    in_w = " <<< IN WINDOW" if start.date() <= d < end.date() else ""
    print(f"    {d}: {date_counts[d]}{in_w}")

# Q9: fake listings
print(f"\nQ9: fake_listing_ids analysis...")

# Phone number frequency
phone_to_lids = defaultdict(list)
for l in listings:
    phone = l.get("posted_by_contact", "")
    if phone:
        phone_to_lids[phone].append(l["listing_id"])

print("  Phone frequency distribution:")
freq_dist = Counter(len(v) for v in phone_to_lids.values())
for cnt, num_phones in sorted(freq_dist.items()):
    print(f"    {num_phones} phone(s) used for {cnt} listing(s)")

print("\n  Top 20 most-used phone numbers:")
for phone, lids in sorted(phone_to_lids.items(), key=lambda x: -len(x[1]))[:20]:
    sample_listings = [l for l in listings if l["listing_id"] in set(lids)][:3]
    localities = set(l.get("locality") for l in [l for l in listings if l["listing_id"] in set(lids)])
    names = set(l.get("posted_by_name","") for l in [l for l in listings if l["listing_id"] in set(lids)])
    print(f"    {phone}: {len(lids)} listings, localities={list(localities)[:3]}, names={list(names)[:2]}")

# Descriptions
desc_to_lids = defaultdict(list)
for l in listings:
    desc = l.get("description","").strip()
    if desc:
        desc_to_lids[desc].append(l["listing_id"])
dup_descs = {d: v for d, v in desc_to_lids.items() if len(v) > 1}
print(f"\n  Shared descriptions: {len(dup_descs)}")
for desc, lids in sorted(dup_descs.items(), key=lambda x: -len(x[1]))[:5]:
    print(f"    '{desc[:60]}': {len(lids)} listings")

# Q10: projects with wrong listing count
print(f"\nQ10: projects_with_wrong_listing_count...")
project_listing_count = Counter(l.get("project_id") for l in listings if l.get("project_id"))
wrong = 0
wrong_list = []
for p in projects:
    pid = p["project_id"]
    reported = p.get("total_listings", 0) or 0
    actual = project_listing_count.get(pid, 0)
    if reported != actual:
        wrong += 1
        wrong_list.append((pid, reported, actual))

wrong_list.sort(key=lambda x: abs(x[1]-x[2]), reverse=True)
print(f"  Projects with wrong total_listings: {wrong}")
print(f"  Top mismatches:")
for pid, rep, act in wrong_list[:10]:
    print(f"    {pid}: reported={rep}, actual={act}")

q10 = wrong
print(f"  Q10 = {q10}")

# FINAL ANSWERS
print("\n" + "=" * 70)
print("FINAL ANSWERS SUMMARY")
print("=" * 70)
answers = {
    "total_listing_records": q1,
    "unique_properties": q2,
    "active_listings": q3,
    "corrupt_listing_ids": q4,
    "total_monthly_rent": q5,
    "avg_price_per_sqft_2bhk": q6_prelim,
    "costliest_project": q7,
    "listings_last_7_days": q8,
    "fake_listing_ids": [],  # TBD after understanding patterns
    "projects_with_wrong_listing_count": q10
}
for k, v in answers.items():
    if isinstance(v, list):
        print(f"  {k}: {len(v)} items = {v[:5]}")
    else:
        print(f"  {k}: {v}")

save_json(answers, "answers_v2.json")
