"""
Q6 and Q7 deep verification + Q4 corrupt check
"""
import json, sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

def load(f):
    with open(f"data/{f}", encoding="utf-8") as fp:
        return json.load(fp)

listings = load("listings_final.json")["records"]
projects = load("projects_final.json")["records"]

# ============================================================
# Q1 - double check
# ============================================================
print("Q1: total_listing_records")
lid_counts = Counter(l["listing_id"] for l in listings)
print(f"  Total raw records: {len(listings)}")
print(f"  Unique IDs: {len(lid_counts)}")
dups = {lid: cnt for lid, cnt in lid_counts.items() if cnt > 1}
print(f"  Duplicate IDs: {len(dups)}")
# Q1 answer = total raw records (even duplicates count as retrievable records)
print(f"  Q1 = {len(listings)}")

# ============================================================
# Q6: avg_price_per_sqft_2bhk - what went wrong?
# ============================================================
print("\nQ6: Deep check")

# Recheck without fake exclusion first
active_2bhk = [l for l in listings if l.get("is_live") and l.get("bedroom") == 2]
print(f"  Active 2BHK total: {len(active_2bhk)}")

# Check all price/sqft values
ppsf_all = [(l["listing_id"], l["price"], l["carpet_area"], l["price"]/l["carpet_area"]) 
            for l in active_2bhk
            if l.get("price") and l.get("carpet_area") and l["carpet_area"] > 0 and l["price"] > 0]

vals = sorted([v[3] for v in ppsf_all])
print(f"  Valid count: {len(vals)}")
print(f"  Range: {vals[0]:.0f} to {vals[-1]:.0f}")
print(f"  Mean: {sum(vals)/len(vals):.2f}")
print(f"  Median: {vals[len(vals)//2]:.2f}")
print(f"  Bottom 10: {[f'{v:.0f}' for v in vals[:10]]}")
print(f"  Top 10: {[f'{v:.0f}' for v in vals[-10:]]}")

# The problem: some listings have price in different units?
# Listing price range from earlier: min=-12M, max=39.27M, median=14.58M
# A 2BHK at 14.58M / 1000sqft = 14,580 per sqft. That's reasonable for Gurgaon.
# But we saw values like 18 (per sqft)? Those are suspiciously low.
print("\n  Suspiciously low price/sqft (< 500):")
low_ppsf = [(lid, p, a, ppsf) for lid, p, a, ppsf in ppsf_all if ppsf < 500]
for lid, p, a, ppsf in sorted(low_ppsf, key=lambda x: x[3])[:20]:
    l = next(x for x in listings if x["listing_id"] == lid)
    print(f"    {lid}: price={p}, carpet={a}, ppsf={ppsf:.1f}, locality={l.get('locality')}, bed={l['bedroom']}")

print("\n  Suspiciously high price/sqft (> 20000):")
high_ppsf = [(lid, p, a, ppsf) for lid, p, a, ppsf in ppsf_all if ppsf > 20000]
for lid, p, a, ppsf in sorted(high_ppsf, key=lambda x: -x[3])[:10]:
    l = next(x for x in listings if x["listing_id"] == lid)
    print(f"    {lid}: price={p:,}, carpet={a}, ppsf={ppsf:.1f}, locality={l.get('locality')}")

# The high ppsf ones - are prices in some different unit?
# 21686 per sqft on a typical Gurgaon apartment seems off
# Let's check typical Gurgaon 2BHK prices in 2026: 50L-2Cr, carpet 700-1200 sqft
# So price/sqft = 50L/1000 = 5000 to 2Cr/700 = 28571
# Actually 14000-20000 per sqft is quite normal for Gurgaon luxury!
# But 21686 is possible. Let me check the low ones:

# Price of 17250 for a 2BHK carpet = 970sqft -> 17.79 per sqft. That's way too low.
# If price 17250 is meant to be 17,250,000 -> 17.79 per sqft is wrong
# But 17250 / 970 = 17.78... These are clearly wrong price entries
# Unless these are in per sqft already? No, that doesn't make sense.

# Let me look at the overall listing price distribution
all_prices = sorted([l.get("price",0) for l in listings if l.get("price")])
print(f"\n  All listing price range: {all_prices[0]:,} to {all_prices[-1]:,}")
print(f"  Prices histogram:")
bins = [(0, 1000), (1000, 100000), (100000, 1000000), (1000000, 5000000), 
        (5000000, 10000000), (10000000, 20000000), (20000000, 50000000), (50000000, 1e12)]
for lo, hi in bins:
    cnt = sum(1 for p in all_prices if lo <= p < hi)
    print(f"    {lo:>12,} - {hi:>12,.0f}: {cnt} listings")

# So the very low-priced listings ARE corrupt (price < 100K for a property is impossible)
corrupt_low_price = [l["listing_id"] for l in listings if l.get("price") and 0 < l["price"] < 100000]
print(f"\n  Listings with price < 100,000 (corrupt?): {len(corrupt_low_price)}")
for lid in corrupt_low_price[:10]:
    l = next(x for x in listings if x["listing_id"] == lid)
    print(f"    {lid}: price={l['price']}, bed={l['bedroom']}, carpet={l['carpet_area']}, locality={l['locality']}")

# These should be excluded from Q6 as corrupt
all_corrupt_ids = set()
# Negative price
all_corrupt_ids.update(l["listing_id"] for l in listings if l.get("price") is not None and l["price"] < 0)
# Price too low (below 1 lakh for any residential property - impossible)
all_corrupt_ids.update(l["listing_id"] for l in listings if l.get("price") and 0 < l["price"] < 100000)
# Floor > total floors
all_corrupt_ids.update(l["listing_id"] for l in listings 
                        if l.get("floor") and l.get("total_floors") and l["floor"] > l["total_floors"])
# SBA < carpet
all_corrupt_ids.update(l["listing_id"] for l in listings
                        if l.get("super_built_up_area") and l.get("carpet_area") 
                        and l["super_built_up_area"] < l["carpet_area"])

print(f"\n  Total corrupt IDs (all categories): {len(all_corrupt_ids)}")

# Recalculate Q6
active_2bhk_clean = [l for l in listings 
                      if l.get("is_live") and l.get("bedroom") == 2 
                      and l["listing_id"] not in all_corrupt_ids]
valid_q6 = [(l["price"] / l["carpet_area"]) 
            for l in active_2bhk_clean
            if l.get("price") and l.get("carpet_area") and l["price"] > 0 and l["carpet_area"] > 0]

if valid_q6:
    vals_clean = sorted(valid_q6)
    avg_clean = sum(vals_clean) / len(vals_clean)
    print(f"\n  Q6 (clean, no fake exclusion): {avg_clean:.2f}")
    print(f"  Range: {vals_clean[0]:.0f} to {vals_clean[-1]:.0f}")
    print(f"  Median: {vals_clean[len(vals_clean)//2]:.2f}")

# ============================================================
# Q7: Project price verification
# ============================================================
print("\n\nQ7: Project price - final determination")
print("  Need to determine: are prices in crores or some other unit?")
print("  For 'swapped' projects (min > max), is min in lakhs?")
print()

# Let's verify by checking P60004: min=94.6, max=2.15
# If min is lakhs: 94.6 * 100000 = 9,460,000 = 94.6 lakhs ≈ 0.946 crore
# If max is crores: 2.15 * 10,000,000 = 21,500,000 = 2.15 crore
# Range: 94.6 lakhs to 2.15 crores -> min=0.946Cr, max=2.15Cr (OK)

# For P60001: min=1.66, max=4.54 (normal case)
# If both in crores: 1.66Cr to 4.54Cr -> OK for Gurgaon
# Listings in Gurgaon: median=14.58M = 1.458Cr, max=39.27M = 3.927Cr
# So projects capped at 4.54Cr is plausible upper end.

# The "swapped" ones:
# P60004: min=94.6 (lakhs = 0.946Cr), max=2.15 (Cr)
# P60009: min=88.2 (lakhs = 0.882Cr), max=1.88 (Cr)
# These make perfect sense if min is in LAKHS and max is in CRORES for swapped entries!

# But then how do we find the highest price_max?
# For "normal" projects: price_max in crores
# For "swapped" projects: the actual max price is price_MIN in lakhs / 100 (to convert to Cr)
# Wait, no - if price_min is swapped with price_max, and price_min should be smaller:
# The actual max price for swapped = price_MIN field (which is unusually large, in lakhs)
# = price_MIN * 100000 / 10000000 = price_MIN / 100 crores? No...

# Let me think again:
# "Swapped" means the values for price_min and price_max are in each other's fields.
# ADDITIONALLY, the unit of the min-field (actually max price) is lakhs, not crores.
# So for P60004:
#   - The "minimum price" is in the price_MAX field = 2.15 crores = 21.5M INR
#   - The "maximum price" is in the price_MIN field = 94.6 lakhs = 9.46M INR  
# But 9.46M < 21.5M, so this would mean min=9.46M, max=21.5M but they're still SWAPPED in the field names.
# That makes it: actual_min_price (in INR) = 94.6L = 9.46M, actual_max_price = 2.15Cr = 21.5M
# The price_min FIELD = 94.6 (actually the min price in LAKHS) ← confusingly labeled as price_min
# The price_max FIELD = 2.15 (actually the max price in CRORES) ← correctly labeled

# WAIT - if so, then for "normal" projects:
# P60001: min=1.66Cr=16.6M, max=4.54Cr=45.4M -> this is a wide range
# For "swapped" P60004: min_field=94.6L=9.46M, max_field=2.15Cr=21.5M
# The "min" in P60004 is actually higher than the "min" in P60001? No:
# P60004 actual_min = 9.46M, P60001 actual_min = 16.6M... OK that's reversed.

# Alternative hypothesis: ALL prices are in crores, and for "swapped" entries,
# JUST the values are wrong (data entry error): min was entered as max and vice versa
# P60004: actual min = 2.15Cr = 21.5M, actual max = 94.6Cr = 946M (ultra luxury)
# That would be a super-luxury project. 94.6 Cr = $11M for one apartment? 
# Even in Gurgaon that's very extreme.

# Most likely: documentation says INR but actually in crores (units bug)
# AND some projects have min/max swapped (data quality bug)
# For costliest project, we need highest ACTUAL max price
# If "swapped" means min/max are switched but both in same units (crores):
#   P60090's price_max=98.9Cr = 989M INR -> a whole society not a single unit, could be total
# If "normal" means both in crores:
#   P60060's price_max=5.83Cr = 58.3M INR -> top end apartment, very possible

# The "swapped" high values (94.6 Cr, 98.9 Cr) are likely the ACTUAL max for those projects
# because they have min > max, meaning someone entered the max in the min field

# FINAL INTERPRETATION: All prices in crores. Some projects have min/max swapped.
# For Q7 (highest price_max): we should find the project with the highest actual max price.
# For "normal" projects: actual_max = price_max field
# For "swapped" projects: actual_max = price_min field (larger value)

all_proj_max = []
for p in projects:
    pmin = p.get("price_min") or 0
    pmax = p.get("price_max") or 0
    if pmin > pmax:  # swapped: actual_max = pmin
        actual_max_crores = pmin
    else:
        actual_max_crores = pmax
    actual_max_inr = actual_max_crores * 10_000_000
    all_proj_max.append((p["project_id"], p.get("apartment_name"), actual_max_crores, actual_max_inr))

all_proj_max.sort(key=lambda x: -x[3])
print("  Top 10 projects by actual max price:")
for pid, name, max_cr, max_inr in all_proj_max[:10]:
    print(f"    {pid} ({name}): {max_cr} Cr = {max_inr:,.0f} INR")

# Is 98.9 Cr for a single apartment reasonable? Even for Gulmohar Park Delhi?
# ANSWER: No, not for a single apartment. But for a project's price range (min to max across all units), 98.9Cr = $11.8M
# is possible for ultra-luxury projects like Golf Course Road Gurgaon.
# Actually Gurgaon has flats at 5-30Cr for luxury. 98.9Cr is a penthouse/villa price - maybe?
# Given the data, P60090 (Puravankara Willows, New Gurgaon) seems like the answer.

q7_final = {"project_id": all_proj_max[0][0], "price_max_inr": all_proj_max[0][3]}
print(f"\n  Q7 FINAL = {q7_final}")

# ============================================================
# SUMMARY
# ============================================================
print("\n\nFINAL VERIFIED ANSWERS")
print("=" * 70)
q4_final = sorted(list(all_corrupt_ids))
print(f"  Q4 = {len(q4_final)} items: {q4_final[:5]}...")

# Save updated corrupt IDs
print(f"\n  Corrupt ID categories:")
neg = [l["listing_id"] for l in listings if l.get("price") is not None and l["price"] < 0]
low = [l["listing_id"] for l in listings if l.get("price") and 0 < l["price"] < 100000]
floor_bad = [l["listing_id"] for l in listings 
             if l.get("floor") and l.get("total_floors") and l["floor"] > l["total_floors"]]
sba_bad = [l["listing_id"] for l in listings
           if l.get("super_built_up_area") and l.get("carpet_area") 
           and l["super_built_up_area"] < l["carpet_area"]]
print(f"    Negative price: {len(neg)}")
print(f"    Price < 1L: {len(low)}")
print(f"    Floor > total_floors: {len(floor_bad)}")
print(f"    SBA < carpet: {len(sba_bad)}")
print(f"    Combined: {len(q4_final)}")
