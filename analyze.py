"""
Deep Analysis v2 - Fixed encoding, deduplication, and analysis
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

IST = timezone(timedelta(hours=5, minutes=30))
REFERENCE = datetime(2026, 9, 10, 0, 0, 0, tzinfo=IST)

def load(filename):
    with open(f"data/{filename}", "r", encoding="utf-8") as f:
        return json.load(f)

listings_data = load("listings_all.json")
rentals_data = load("rentals_all.json")
projects_data = load("projects_all.json")

listings_raw = listings_data["records"]
rentals_raw = rentals_data["records"]
projects_raw = projects_data["records"]

print("=" * 70)
print("DATA OVERVIEW")
print("=" * 70)
print(f"Listings fetched: {len(listings_raw)} (API total: {listings_data['total_from_api']})")
print(f"Rentals fetched:  {len(rentals_raw)} (API total: {rentals_data['total_from_api']})")
print(f"Projects fetched: {len(projects_raw)} (API total: {projects_data['total_from_api']})")

# ============================================================
# DEDUPLICATION ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("DEDUPLICATION")
print("=" * 70)

# Listings: count by listing_id
lid_counts = Counter(l["listing_id"] for l in listings_raw)
dup_lids = {lid: cnt for lid, cnt in lid_counts.items() if cnt > 1}
print(f"\nListings:")
print(f"  Unique listing_ids: {len(lid_counts)}")
print(f"  Duplicate listing_ids: {len(dup_lids)}")
print(f"  Total extra records from duplication: {sum(cnt-1 for cnt in dup_lids.values())}")
print(f"  Top duplicates:")
for lid, cnt in sorted(dup_lids.items(), key=lambda x: -x[1])[:5]:
    print(f"    {lid}: {cnt} times")

# Deduplicated listings (keep first occurrence)
seen_lids = set()
listings = []
for l in listings_raw:
    lid = l["listing_id"]
    if lid not in seen_lids:
        seen_lids.add(lid)
        listings.append(l)
print(f"\n  After dedup: {len(listings)} unique listings")

# Rentals dedup
rid_counts = Counter(r["listing_id"] for r in rentals_raw)
dup_rids = {rid: cnt for rid, cnt in rid_counts.items() if cnt > 1}
print(f"\nRentals:")
print(f"  Unique listing_ids: {len(rid_counts)}")
print(f"  Duplicate listing_ids: {len(dup_rids)}")
seen_rids = set()
rentals = []
for r in rentals_raw:
    rid = r["listing_id"]
    if rid not in seen_rids:
        seen_rids.add(rid)
        rentals.append(r)
print(f"  After dedup: {len(rentals)} unique rentals")

# Projects dedup
pid_counts = Counter(p["project_id"] for p in projects_raw)
dup_pids = {pid: cnt for pid, cnt in pid_counts.items() if cnt > 1}
print(f"\nProjects:")
print(f"  Unique project_ids: {len(pid_counts)}")
print(f"  Duplicate project_ids: {len(dup_pids)}")
seen_pids = set()
projects = []
for p in projects_raw:
    pid = p["project_id"]
    if pid not in seen_pids:
        seen_pids.add(pid)
        projects.append(p)
print(f"  After dedup: {len(projects)} unique projects")

# ============================================================
# Q1: total_listing_records
# ============================================================
print("\n" + "=" * 70)
print("Q1: total_listing_records")
print("=" * 70)
# The question asks "how many listing records are retrievable"
# We fetched 3350 raw records (including duplicates across pages)
# API says total=3332, but we fetched 3350 (18 extra)
# The actual retrievable record count is what we fetched: 3350
# But the question might mean unique records...
# Let's re-examine: we fetched 67 pages of 50 records = 3350
# API says total=3332, so 3350-3332=18 "extra" records in pagination
q1 = len(listings_raw)  # total retrievable records
print(f"  Total records retrievable (raw): {q1}")
print(f"  API reported total: {listings_data['total_from_api']}")
print(f"  This IS a discrepancy - records=3350 but total=3332")
print(f"  Q1 = {q1} (the actual number paginatable from the endpoint)")

# ============================================================
# Q2: unique_properties
# ============================================================
print("\n" + "=" * 70)
print("Q2: unique_properties (distinct listing_ids)")
print("=" * 70)
q2 = len(lid_counts)  # distinct listing_ids
print(f"  Q2 = {q2}")

# ============================================================
# Q3: active_listings (is_live=True) - from raw records
# ============================================================
print("\n" + "=" * 70)
print("Q3: active_listings")
print("=" * 70)
# From raw records (all retrievable)
q3_raw = sum(1 for l in listings_raw if l.get("is_live") == True)
# From deduped records
q3_dedup = sum(1 for l in listings if l.get("is_live") == True)
print(f"  is_live=True (raw): {q3_raw}")
print(f"  is_live=True (dedup): {q3_dedup}")
print(f"  is_live=False (raw): {sum(1 for l in listings_raw if l.get('is_live')==False)}")
q3 = q3_raw  # question says "how many retrievable listing records have is_live true"
print(f"  Q3 = {q3}")

# ============================================================
# Q4: corrupt_listing_ids
# ============================================================
print("\n" + "=" * 70)
print("Q4: corrupt_listing_ids")
print("=" * 70)

# Look for listings that describe something that "cannot exist"
# Physical impossibilities:
# 1. floor > total_floors
# 2. super_built_up_area < carpet_area (SBA must ALWAYS be >= carpet)
# 3. bedroom = 0 when it should be a living space
# 4. negative values for area/price
# 5. Area physically impossible (e.g., 1 sqft for 3BHK)

corrupt_unique = set()
for l in listings:  # use deduped
    lid = l["listing_id"]
    bedroom = l.get("bedroom")
    bathroom = l.get("bathroom")
    carpet = l.get("carpet_area")
    sba = l.get("super_built_up_area")
    floor_num = l.get("floor")
    total_floors = l.get("total_floors")
    price = l.get("price")
    
    reasons = []
    
    # SBA < carpet is physically impossible (super built-up always includes carpet)
    if carpet and sba and sba < carpet:
        reasons.append(f"SBA({sba}) < carpet({carpet})")
    
    # Floor > total_floors
    if floor_num is not None and total_floors is not None and floor_num > total_floors:
        reasons.append(f"floor({floor_num}) > total_floors({total_floors})")
    
    # Negative/zero values for critical fields
    if carpet is not None and carpet <= 0:
        reasons.append(f"carpet_area={carpet}")
    if price is not None and price <= 0:
        reasons.append(f"price={price}")
    
    # Carpet area impossibly small - let's be more careful here
    # A 1BHK studio in India is minimum ~300 sqft carpet
    # A 2BHK minimum ~600 sqft carpet 
    # A 3BHK minimum ~900 sqft carpet
    # But the assignment says "cannot exist" so let's look for clear impossibilities
    
    if reasons:
        corrupt_unique.add(lid)
        if len(corrupt_unique) <= 20:
            print(f"  CORRUPT: {lid} - {reasons}")

# Check for more patterns
print(f"\n  Total corrupt unique listing_ids: {len(corrupt_unique)}")

# Let's look at the specific "small carpet for bedroom" cases more carefully
# A 1-bedroom needs at least 1 room (~100-150sqft in India could technically exist for micro-units)
# A 2-bedroom with 77sqft is clearly impossible
print("\n  Checking carpet vs bedroom ratio:")
for l in listings:
    carpet = l.get("carpet_area", 0)
    bed = l.get("bedroom", 0)
    if bed >= 2 and carpet and carpet < 200:  # clearly impossible: 2BHK < 200sqft
        print(f"    {l['listing_id']}: {bed}BHK, carpet={carpet}")
        corrupt_unique.add(l["listing_id"])
    elif bed >= 3 and carpet and carpet < 300:  # 3BHK < 300sqft
        print(f"    {l['listing_id']}: {bed}BHK, carpet={carpet}")
        corrupt_unique.add(l["listing_id"])

q4 = sorted(list(corrupt_unique))
print(f"\n  Q4 = {q4}")

# ============================================================
# Q5: total_monthly_rent for Sector 49
# ============================================================
print("\n" + "=" * 70)
print("Q5: total_monthly_rent (Sector 49)")
print("=" * 70)

# From deduplicated rentals, filter for sector 49
sec49_rentals = [r for r in rentals if r.get("locality","").lower().strip() == "sector 49"]
print(f"  Sector 49 rentals (deduped, manual filter): {len(sec49_rentals)}")

total_rent = sum(r.get("price", 0) for r in sec49_rentals)
print(f"  Sample prices: {[r.get('price') for r in sec49_rentals[:10]]}")
print(f"  Total monthly rent: {total_rent}")

# Check if price needs unit conversion - doc says "monthly rent in rupees"
# Values look reasonable if in rupees (20000-80000 per month)
if sec49_rentals:
    prices_sample = sorted([r.get("price",0) for r in sec49_rentals])
    print(f"  Price range: {prices_sample[0]} to {prices_sample[-1]}")
    print(f"  Median: {prices_sample[len(prices_sample)//2]}")

q5 = total_rent
print(f"  Q5 = {q5}")

# ============================================================
# Q6: avg_price_per_sqft_2bhk
# ============================================================
print("\n" + "=" * 70)
print("Q6: avg_price_per_sqft_2bhk")
print("=" * 70)

# First we need Q9 (fake listing IDs) - let's compute tentatively
# Active (is_live=True), bedroom=2, exclude corrupt (Q4) and fake (Q9 - TBD)
eligible_2bhk = [l for l in listings  # deduped
                 if l.get("is_live") == True
                 and l.get("bedroom") == 2
                 and l["listing_id"] not in set(q4)]

print(f"  2BHK active listings (excl. corrupt): {len(eligible_2bhk)}")

valid_ppsf = [(l["listing_id"], l["price"] / l["carpet_area"]) 
              for l in eligible_2bhk 
              if l.get("price") and l.get("carpet_area") and l.get("carpet_area") > 0]

print(f"  Valid for calculation: {len(valid_ppsf)}")
if valid_ppsf:
    vals = [v for _, v in valid_ppsf]
    avg = sum(vals) / len(vals)
    print(f"  Mean price/sqft: {avg:.2f}")
    
    # Check for outliers
    vals_sorted = sorted(vals)
    print(f"  Range: {vals_sorted[0]:.0f} to {vals_sorted[-1]:.0f}")
    print(f"  Bottom 5: {[f'{v:.0f}' for v in vals_sorted[:5]]}")
    print(f"  Top 5: {[f'{v:.0f}' for v in vals_sorted[-5:]]}")

q6_prelim = round(avg, 2) if valid_ppsf else 0.0
print(f"  Q6 (preliminary, before removing fake) = {q6_prelim}")

# ============================================================
# Q7: costliest_project
# ============================================================
print("\n" + "=" * 70)
print("Q7: costliest_project")
print("=" * 70)
sorted_projects = sorted(projects, key=lambda p: p.get("price_max", 0) or 0, reverse=True)
print("  Top 5 by price_max:")
for p in sorted_projects[:5]:
    print(f"  {p['project_id']}: {p.get('apartment_name')}, price_max={p.get('price_max'):,}, locality={p.get('locality')}")
q7 = {"project_id": sorted_projects[0]["project_id"], "price_max_inr": sorted_projects[0].get("price_max")}
print(f"  Q7 = {q7}")

# ============================================================
# Q8: listings_last_7_days [REFERENCE-7, REFERENCE)
# ============================================================
print("\n" + "=" * 70)
print("Q8: listings_last_7_days")
print("=" * 70)
start = REFERENCE - timedelta(days=7)
end = REFERENCE
print(f"  Window: {start.isoformat()} to {end.isoformat()}")

in_window = []
for l in listings_raw:  # raw - question says "retrievable records"
    posted_str = l.get("posted_at", "")
    if not posted_str:
        continue
    try:
        if posted_str.endswith("Z"):
            dt = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(posted_str)
        dt_ist = dt.astimezone(IST)
        if start <= dt_ist < end:
            in_window.append(l["listing_id"])
    except Exception as e:
        pass

q8 = len(in_window)
print(f"  Q8 = {q8}")

# What format are timestamps in?
sample_ts = [l["posted_at"] for l in listings[:5]]
print(f"  Sample timestamps: {sample_ts}")
# Check if they're UTC or IST
# Health endpoint showed +05:30 (IST), but docs say Z (UTC)

# ============================================================
# Q9: fake_listing_ids - DEEP ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("Q9: fake_listing_ids (deep analysis)")
print("=" * 70)

# Hypothesis: fake listings have suspicious phone numbers used across many listings
# A real seller won't have 100 listings with the same phone number
phone_to_lids = defaultdict(list)
for l in listings:
    phone = l.get("posted_by_contact", "")
    if phone:
        phone_to_lids[phone].append(l["listing_id"])

print("\n  Phone number frequency distribution:")
freq_dist = Counter(len(v) for v in phone_to_lids.values())
for count, num_phones in sorted(freq_dist.items()):
    print(f"    {num_phones} phone(s) used for exactly {count} listing(s)")

# Phones used for many listings are suspicious
suspicious_threshold = 10
suspicious_phones = {p: ids for p, ids in phone_to_lids.items() if len(ids) >= suspicious_threshold}
print(f"\n  Phones used for >= {suspicious_threshold} listings:")
all_fake_ids = set()
for phone, ids in sorted(suspicious_phones.items(), key=lambda x: -len(x[1])):
    print(f"    {phone}: {len(ids)} listings")
    # Look at these listings
    these_listings = [l for l in listings if l["listing_id"] in set(ids)]
    localities = set(l.get("locality") for l in these_listings)
    bedrooms = set(l.get("bedroom") for l in these_listings)
    names = set(l.get("posted_by_name") for l in these_listings)
    print(f"      localities={list(localities)[:5]}, bedrooms={bedrooms}, names={list(names)[:5]}")
    all_fake_ids.update(ids)

print(f"\n  Total potential fake listing_ids (phone-based): {len(all_fake_ids)}")

# Hypothesis 2: identical descriptions = fake/template listings
desc_to_lids = defaultdict(list)
for l in listings:
    desc = l.get("description", "").strip()
    if desc and len(desc) > 50:
        desc_to_lids[desc].append(l["listing_id"])

dup_desc_groups = {d: ids for d, ids in desc_to_lids.items() if len(ids) > 3}
print(f"\n  Descriptions shared by > 3 listings: {len(dup_desc_groups)}")
for desc, ids in list(dup_desc_groups.items())[:3]:
    print(f"    '{desc[:60]}...' -> {len(ids)} listings")

# Hypothesis 3: Look at contact numbers for specific pattern
# All real contacts would be distinct, fakes might share numbers
contact_set = Counter(l.get("posted_by_contact","") for l in listings)
print(f"\n  Total unique contact numbers: {len(contact_set)}")
print(f"  Most repeated contacts:")
for contact, count in contact_set.most_common(10):
    print(f"    {contact}: {count}")

# Hypothesis 4: Listings where price per sqft is an exact round number
# Fakes might have templated prices
round_ppsf = []
for l in listings:
    if l.get("price") and l.get("carpet_area"):
        ppsf = l["price"] / l["carpet_area"]
        if ppsf == int(ppsf):  # exactly integer
            round_ppsf.append((l["listing_id"], ppsf))
print(f"\n  Listings with exactly integer price/sqft: {len(round_ppsf)}")

# The most reliable signal: same contact for MANY different listings
# Real agents might have a few (say <=5), but fake ones will have many more
print("\n  Setting fake threshold at 20+ listings per phone:")
fake_phones_20 = {p: ids for p, ids in phone_to_lids.items() if len(ids) >= 20}
fake_ids_20 = set()
for p, ids in fake_phones_20.items():
    fake_ids_20.update(ids)
print(f"  Phones with 20+ listings: {len(fake_phones_20)}, fake IDs: {len(fake_ids_20)}")

q9 = sorted(list(fake_ids_20))
print(f"\n  Q9 (using 20+ threshold) = {len(q9)} fake listings")
print(f"  First 10: {q9[:10]}")

# ============================================================
# Q6 FINAL: Now exclude fake listings
# ============================================================
print("\n" + "=" * 70)
print("Q6 FINAL: avg_price_per_sqft_2bhk (excl. corrupt + fake)")
print("=" * 70)
exclude_set = set(q4) | set(q9)
eligible_final = [l for l in listings
                  if l.get("is_live") == True
                  and l.get("bedroom") == 2
                  and l["listing_id"] not in exclude_set]
print(f"  2BHK active, excl corrupt+fake: {len(eligible_final)}")

valid_final = [(l["listing_id"], l["price"] / l["carpet_area"]) 
               for l in eligible_final
               if l.get("price") and l.get("carpet_area") and l.get("carpet_area") > 0]

if valid_final:
    vals = [v for _, v in valid_final]
    avg_final = sum(vals) / len(vals)
    print(f"  Q6 FINAL = {round(avg_final, 2)}")
    q6 = round(avg_final, 2)
else:
    q6 = q6_prelim

# ============================================================
# Q10: projects_with_wrong_listing_count
# ============================================================
print("\n" + "=" * 70)
print("Q10: projects_with_wrong_listing_count")
print("=" * 70)

# Count actual listings per project
project_actual = Counter()
for l in listings:  # deduped
    pid = l.get("project_id")
    if pid:
        project_actual[pid] += 1

wrong_count = 0
wrong_projects = []
for p in projects:
    pid = p["project_id"]
    reported = p.get("total_listings", 0) or 0
    actual = project_actual.get(pid, 0)
    if reported != actual:
        wrong_count += 1
        wrong_projects.append((pid, p.get("apartment_name",""), reported, actual, actual-reported))

wrong_projects.sort(key=lambda x: abs(x[4]), reverse=True)
print(f"  Projects with wrong total_listings: {wrong_count}")
print(f"  Top mismatches:")
for pid, name, rep, act, diff in wrong_projects[:10]:
    print(f"    {pid} ({name}): reported={rep}, actual={act}, diff={diff:+d}")

q10 = wrong_count
print(f"  Q10 = {q10}")

# ============================================================
# FINAL ANSWERS
# ============================================================
print("\n" + "=" * 70)
print("FINAL ANSWERS")
print("=" * 70)
answers = {
    "total_listing_records": q1,
    "unique_properties": q2,
    "active_listings": q3,
    "corrupt_listing_ids": q4,
    "total_monthly_rent": q5,
    "avg_price_per_sqft_2bhk": q6,
    "costliest_project": q7,
    "listings_last_7_days": q8,
    "fake_listing_ids": q9,
    "projects_with_wrong_listing_count": q10
}
for k, v in answers.items():
    if isinstance(v, list):
        print(f"  {k}: [{len(v)} items] {v[:3]}...")
    else:
        print(f"  {k}: {v}")

with open("data/final_answers.json", "w", encoding="utf-8") as f:
    json.dump(answers, f, indent=2, ensure_ascii=False)
print("\nSaved to data/final_answers.json")

# ============================================================
# DOCUMENTATION DISCREPANCIES SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("DOCUMENTATION DISCREPANCIES")
print("=" * 70)

discrepancies = [
    {
        "finding": "Auth: API key must be X-API-Key header, not query param",
        "endpoint": "*",
        "category": "auth",
    },
    {
        "finding": "Auth login POST also needs X-API-Key header (undocumented)",
        "endpoint": "/auth/login",
        "category": "auth",
    },
    {
        "finding": "All data endpoints require Bearer token (doc implies key alone is enough)",
        "endpoint": "/v1/listings",
        "category": "auth",
    },
    {
        "finding": "/v1/analytics/summary returns 404",
        "endpoint": "/v1/analytics/summary",
        "category": "missing_endpoint",
    },
    {
        "finding": "GET /v1/listing/{id} returns 404, correct path is /v1/listings/{id}",
        "endpoint": "/v1/listing/{id}",
        "category": "missing_endpoint",
    },
    {
        "finding": "/v1/listings/{id}/similar returns 404",
        "endpoint": "/v1/listings/{id}/similar",
        "category": "missing_endpoint",
    },
    {
        "finding": "/v1/favourites returns 404 - endpoint not implemented",
        "endpoint": "/v1/favourites",
        "category": "missing_endpoint",
    },
    {
        "finding": "Doc says /v1/listings returns only active listings, but is_live=False records are present",
        "endpoint": "/v1/listings",
        "category": "completeness",
    },
    {
        "finding": "Pagination: more records retrievable than total field suggests (duplicates)",
        "endpoint": "/v1/listings",
        "category": "pagination",
    },
    {
        "finding": "Timestamps in health endpoint use +05:30 (IST), doc says UTC/Z",
        "endpoint": "/health",
        "category": "timestamps",
    },
    {
        "finding": "is_live field not documented but present on listing objects",
        "endpoint": "/v1/listings",
        "category": "undocumented_endpoint",
    },
    {
        "finding": "locality filter doesn't filter correctly - api total != actual records",
        "endpoint": "/v1/listings",
        "category": "filters",
    },
]

for d in discrepancies:
    print(f"  [{d['category']}] {d['endpoint']}: {d['finding']}")
