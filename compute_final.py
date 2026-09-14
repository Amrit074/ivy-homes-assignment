"""
FINAL: Compute all 10 answers cleanly.
"""
import json, sys
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')
IST = timezone(timedelta(hours=5, minutes=30))
REFERENCE = datetime(2026, 9, 10, 0, 0, 0, tzinfo=IST)

def load(f):
    with open(f"data/{f}", encoding="utf-8") as fp:
        return json.load(fp)

listings = load("listings_final.json")["records"]
rentals = load("rentals_final.json")["records"]
projects = load("projects_final.json")["records"]

print(f"Total records: listings={len(listings)}, rentals={len(rentals)}, projects={len(projects)}")

# ============================================================
# Q1: total_listing_records
# ============================================================
q1 = len(listings)  # Total retrievable records (all unique in this case)
print(f"\nQ1 = {q1}")

# ============================================================
# Q2: unique_properties
# ============================================================
unique_lids = len(set(l["listing_id"] for l in listings))
q2 = unique_lids
print(f"Q2 = {q2}")

# ============================================================
# Q3: active_listings (is_live=True)
# ============================================================
q3 = sum(1 for l in listings if l.get("is_live") == True)
print(f"Q3 = {q3}")

# ============================================================
# Q4: corrupt_listing_ids
# Things that CANNOT EXIST physically:
# 1. Negative price
# 2. Price < 1 lakh (any residential property must cost >= 1L in India)
# 3. Floor > total_floors (physically impossible)
# 4. SBA < carpet (by definition SBA >= carpet)
# 5. Carpet area < 100 sqft with 2+ bedrooms (impossible)
# ============================================================
corrupt = set()

for l in listings:
    lid = l["listing_id"]
    price = l.get("price")
    carpet = l.get("carpet_area") or 0
    sba = l.get("super_built_up_area") or 0
    floor = l.get("floor") or 0
    total_floors = l.get("total_floors") or 0
    bedroom = l.get("bedroom") or 0
    
    if price is not None and price < 0:
        corrupt.add(lid)
    elif price is not None and 0 < price < 100000:  # impossibly cheap (< 1 lakh)
        corrupt.add(lid)
    
    if floor > 0 and total_floors > 0 and floor > total_floors:
        corrupt.add(lid)
    
    if sba > 0 and carpet > 0 and sba < carpet:
        corrupt.add(lid)
    
    # Any bedroom count with carpet < 100 sqft is impossible for habitation
    if bedroom >= 2 and carpet > 0 and carpet < 100:
        corrupt.add(lid)

q4 = sorted(list(corrupt))
print(f"\nQ4 = {len(q4)} IDs: {q4}")

# ============================================================
# Q5: total_monthly_rent for Sector 49
# ============================================================
sec49 = [r for r in rentals if r.get("locality","").lower().strip() == "sector 49"]
q5 = sum(r.get("price", 0) for r in sec49)
print(f"\nQ5 = {q5} (from {len(sec49)} Sector 49 rentals)")

# ============================================================
# Q6: avg_price_per_sqft_2bhk
# Active, bedroom=2, exclude corrupt (Q4) and fake (Q9)
# ============================================================
# First let's figure out Q9 (fakes)
phone_to_lids = defaultdict(set)
for l in listings:
    phone = l.get("posted_by_contact","")
    if phone:
        phone_to_lids[phone].add(l["listing_id"])

# Fake = phone used with 3+ different posted_by_names
fake = set()
for phone, lids in phone_to_lids.items():
    phone_listings = [l for l in listings if l["listing_id"] in lids]
    names = set(l.get("posted_by_name","") for l in phone_listings)
    if len(names) >= 3:  # same phone, 3+ different "sellers" = clearly fake
        fake.update(lids)

q9 = sorted(list(fake))
print(f"\nQ9 = {len(q9)} fake IDs (first 5: {q9[:5]})")

# Now Q6
exclude_q6 = set(q4) | set(q9)
eligible = [l for l in listings
            if l.get("is_live") == True
            and l.get("bedroom") == 2
            and l["listing_id"] not in exclude_q6
            and l.get("price") and l["price"] > 0
            and l.get("carpet_area") and l["carpet_area"] > 0]

q6_vals = [l["price"] / l["carpet_area"] for l in eligible]
q6 = round(sum(q6_vals) / len(q6_vals), 2) if q6_vals else 0.0
print(f"\nQ6 = {q6} (from {len(eligible)} eligible listings)")
print(f"  Range: {min(q6_vals):.0f} to {max(q6_vals):.0f}")
q6_vals_sorted = sorted(q6_vals)
print(f"  Median: {q6_vals_sorted[len(q6_vals_sorted)//2]:.2f}")

# ============================================================
# Q7: costliest_project
# ============================================================
# Project prices in crores; for "swapped" entries, actual_max = price_min field
all_proj_prices = []
for p in projects:
    pmin = p.get("price_min") or 0
    pmax = p.get("price_max") or 0
    if pmin > pmax:  # swapped: actual max is in min field
        actual_max_cr = pmin
    else:
        actual_max_cr = pmax
    all_proj_prices.append((p["project_id"], actual_max_cr * 10_000_000))

all_proj_prices.sort(key=lambda x: -x[1])
q7_pid, q7_price = all_proj_prices[0]
q7 = {"project_id": q7_pid, "price_max_inr": int(q7_price)}
print(f"\nQ7 = {q7}")

# ============================================================
# Q8: listings_last_7_days [REFERENCE-7days, REFERENCE)
# ============================================================
window_start = REFERENCE - timedelta(days=7)
window_end = REFERENCE

in_window = 0
for l in listings:
    ps = l.get("posted_at","")
    try:
        if ps.endswith("Z"):
            dt = datetime.fromisoformat(ps.replace("Z","+00:00"))
        else:
            dt = datetime.fromisoformat(ps)
        dt_ist = dt.astimezone(IST)
        if window_start <= dt_ist < window_end:
            in_window += 1
    except:
        pass

q8 = in_window
print(f"\nQ8 = {q8}")

# ============================================================
# Q10: projects_with_wrong_listing_count
# ============================================================
project_actual = Counter(l.get("project_id") for l in listings if l.get("project_id"))
wrong = sum(1 for p in projects 
            if (p.get("total_listings") or 0) != project_actual.get(p["project_id"], 0))
q10 = wrong
print(f"\nQ10 = {q10}")

# ============================================================
# FINAL SUMMARY
# ============================================================
final = {
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

print("\n" + "=" * 70)
print("FINAL ANSWERS")
print("=" * 70)
for k, v in final.items():
    if isinstance(v, list):
        print(f"  {k}: {len(v)} items")
    else:
        print(f"  {k}: {v}")

with open("data/FINAL_ANSWERS_CLEAN.json", "w", encoding="utf-8") as f:
    json.dump(final, f, indent=2, ensure_ascii=False)
print("\nSaved to data/FINAL_ANSWERS_CLEAN.json")
