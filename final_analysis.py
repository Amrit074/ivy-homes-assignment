"""
Final deep analysis - targeted at remaining ambiguous questions.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

IST = timezone(timedelta(hours=5, minutes=30))
REFERENCE = datetime(2026, 9, 10, 0, 0, 0, tzinfo=IST)

def load(f):
    with open(f"data/{f}", encoding="utf-8") as fp:
        return json.load(fp)

listings_data = load("listings_final.json")
rentals_data = load("rentals_final.json")
projects_data = load("projects_final.json")
sec49_data = load("sec49_rentals_final.json")

listings = listings_data["records"]
rentals = rentals_data["records"]
projects = projects_data["records"]
sec49_rentals = sec49_data["records"]

print(f"Listings: {len(listings)}, Rentals: {len(rentals)}, Projects: {len(projects)}")
print(f"Sec49 rentals: {len(sec49_rentals)}")

# ============================================================
# Q4: CORRUPT LISTINGS - what "cannot exist" means
# ============================================================
print("\n" + "=" * 70)
print("Q4: CORRUPT LISTINGS - Refinement")
print("=" * 70)

# From previous analysis: 306 items. Let me check each category more carefully

# Category 1: Negative prices
neg_price_lids = set()
for l in listings:
    if l.get("price") is not None and l.get("price") < 0:
        neg_price_lids.add(l["listing_id"])
print(f"  Negative price: {len(neg_price_lids)}")
for lid in sorted(neg_price_lids)[:5]:
    l = next(x for x in listings if x["listing_id"] == lid)
    print(f"    {lid}: price={l['price']}, bed={l['bedroom']}, carpet={l['carpet_area']}")

# Category 2: Floor > total_floors
floor_issue_lids = set()
for l in listings:
    if l.get("floor") and l.get("total_floors") and l.get("floor") > l.get("total_floors"):
        floor_issue_lids.add(l["listing_id"])
print(f"  Floor > total_floors: {len(floor_issue_lids)}")

# Category 3: SBA < carpet
sba_issue_lids = set()
for l in listings:
    if l.get("super_built_up_area") and l.get("carpet_area"):
        if l.get("super_built_up_area") < l.get("carpet_area"):
            sba_issue_lids.add(l["listing_id"])
print(f"  SBA < carpet: {len(sba_issue_lids)}")
for lid in sorted(sba_issue_lids)[:3]:
    l = next(x for x in listings if x["listing_id"] == lid)
    print(f"    {lid}: carpet={l['carpet_area']}, SBA={l['super_built_up_area']}")

# Category 4: Impossible small area
area_issue_lids = set()
for l in listings:
    bed = l.get("bedroom", 0) or 0
    carpet = l.get("carpet_area", 0) or 0
    if bed >= 2 and carpet > 0 and carpet < 300:  # 2BHK < 300sqft is impossible
        area_issue_lids.add(l["listing_id"])
    elif bed >= 3 and carpet > 0 and carpet < 500:  # 3BHK < 500sqft is impossible
        area_issue_lids.add(l["listing_id"])
print(f"  Area impossible for bedroom count: {len(area_issue_lids)}")

# What are these? Let's see all of them
print("  Details:")
for lid in sorted(area_issue_lids)[:20]:
    l = next(x for x in listings if x["listing_id"] == lid)
    print(f"    {lid}: {l['bedroom']}BHK, carpet={l['carpet_area']}, price={l['price']}")

# Combined
all_corrupt = neg_price_lids | floor_issue_lids | sba_issue_lids | area_issue_lids
print(f"\n  Total corrupt (all categories): {len(all_corrupt)}")

# "cannot exist" is the key phrase. Let's be strict:
# A listing that "cannot exist" as a physical property:
# - Negative area or price (data error, not impossible physics)
# - Floor > total_floors (physically impossible - you can't be on floor 5 of a 3-floor building)
# - SBA < carpet (physically impossible by definition)
# - 0 carpet area (no such thing as a 0sqft apartment)

cannot_exist = neg_price_lids | floor_issue_lids | sba_issue_lids
print(f"  'Cannot exist' (strict): {len(cannot_exist)}")
print(f"    Neg price: {len(neg_price_lids)}")
print(f"    Floor > total_floors: {len(floor_issue_lids)}")
print(f"    SBA < carpet: {len(sba_issue_lids)}")
q4 = sorted(list(cannot_exist))
print(f"  Q4 = {q4[:10]}...")
print(f"  Q4 count = {len(q4)}")

# ============================================================
# Q5: Sector 49 Monthly Rent
# ============================================================
print("\n" + "=" * 70)
print("Q5: Sector 49 Monthly Rent")
print("=" * 70)
sec49_manual = [r for r in rentals if r.get("locality","").lower().strip() == "sector 49"]
print(f"  Sector 49 from all rentals: {len(sec49_manual)}")
total_rent = sum(r.get("price",0) for r in sec49_manual)
print(f"  Total monthly rent: {total_rent}")
rents = sorted([r.get("price",0) for r in sec49_manual])
print(f"  Rent range: {rents[0]} to {rents[-1]}")
print(f"  Q5 = {total_rent}")

# ============================================================
# Q7: Project price unit investigation
# ============================================================
print("\n" + "=" * 70)
print("Q7: Project Price Analysis")
print("=" * 70)

# Key observation: some projects have price_min > price_max
# That means they're swapped OR different units.
# If ALL are in crores: P60004 min=94.6 max=2.15 -> 94.6 Cr > 2.15 Cr? 
#   -> means cheapest unit is 94.6 Cr, most expensive is 2.15 Cr? That's backwards.
# If min is in lakhs, max in crores:
#   P60004: min=94.6L=9.46M INR, max=2.15Cr=21.5M INR -> min < max! Makes sense!
# If min is in lakhs, max in crores:
#   P60001: min=1.66L=166000 INR, max=4.54Cr=45.4M INR -> very large range
# That last interpretation doesn't work for P60001...

# Let me look at projects with "normal" min/max (min < max numerically)
normal = [(p["project_id"], p.get("apartment_name"), p.get("price_min"), p.get("price_max"))
          for p in projects 
          if p.get("price_min") and p.get("price_max") and p.get("price_min") < p.get("price_max")]
swapped = [(p["project_id"], p.get("apartment_name"), p.get("price_min"), p.get("price_max"))
           for p in projects 
           if p.get("price_min") and p.get("price_max") and p.get("price_min") > p.get("price_max")]

print(f"  Normal (min < max numerically): {len(normal)}")
print(f"  Swapped (min > max numerically): {len(swapped)}")

# For normal ones: min=1.66, max=4.54 -> both in crores: 1.66Cr to 4.54Cr -> reasonable
# For swapped ones: min=94.6, max=2.15 -> if min is in LAKHS and max in CRORES:
#   94.6L = 9.46M INR, 2.15Cr = 21.5M INR -> 9.46M to 21.5M -> reasonable!
# But that's inconsistent units.

# ALTERNATIVE: all are in crores, but the values for "swapped" are WRONG:
#   price_min and price_max fields are switched for 184 projects
print("\n  Swapped projects - what are correct prices?")
print("  If swapped: actual_min=max value in crores, actual_max=min value in lakhs/100?")
for pid, name, pmin, pmax in swapped[:5]:
    # If min is actually in lakhs -> INR = pmin * 100000
    # If max is actually in crores -> INR = pmax * 10000000
    min_as_lakhs = pmin * 100000
    max_as_crores = pmax * 10000000
    print(f"  {pid} ({name}): raw min={pmin}, raw max={pmax}")
    print(f"    If swapped & min in lakhs: actual min={max_as_crores:,}, actual max={min_as_lakhs:,}")

# For the "normal" projects, what unit makes more sense?
print("\n  Normal projects price analysis:")
for pid, name, pmin, pmax in normal[:5]:
    min_as_crores = pmin * 10000000
    max_as_crores = pmax * 10000000
    print(f"  {pid} ({name}): min={pmin}Cr={min_as_crores:,.0f}INR, max={pmax}Cr={max_as_crores:,.0f}INR")

# The most likely interpretation given Gurgaon prices:
# "Normal" projects: both in crores (P60001: 1.66-4.54 Cr -> reasonable)
# "Swapped" projects: price_min and price_max are SWAPPED, AND
#   the larger value (now in min field) is in LAKHS, the smaller (in max field) in CRORES
# This would mean: 
#   P60004: min field=94.6 LAKHS = 9.46M, max field=2.15 CRORES = 21.5M -> 9.46M-21.5M OK
# This is consistent with a bug where some entries have swapped + wrong unit

# For Q7: find project with highest price_max in terms of actual INR
# For normal projects: price_max is in crores
# For swapped projects: the actual max is in the price_MIN field (in lakhs)
all_prices = []
for p in projects:
    pmin = p.get("price_min") or 0
    pmax = p.get("price_max") or 0
    if pmin > pmax:  # swapped
        # actual max = pmin (in lakhs)
        actual_max_inr = pmin * 100000
        all_prices.append((p["project_id"], p.get("apartment_name"), actual_max_inr, "swapped_lakhs"))
    else:  # normal
        # actual max = pmax (in crores)
        actual_max_inr = pmax * 10000000
        all_prices.append((p["project_id"], p.get("apartment_name"), actual_max_inr, "crores"))

all_prices.sort(key=lambda x: -x[2])
print("\n  Top 10 projects by actual price_max (INR):")
for pid, name, price_inr, unit_type in all_prices[:10]:
    print(f"  {pid} ({name}): {price_inr:,.0f} INR ({unit_type})")

q7_pid = all_prices[0][0]
q7_price = all_prices[0][2]
q7 = {"project_id": q7_pid, "price_max_inr": int(q7_price)}
print(f"\n  Q7 = {q7}")

# ============================================================
# Q9: FAKE LISTINGS
# ============================================================
print("\n" + "=" * 70)
print("Q9: FAKE LISTINGS - Deep Investigation")
print("=" * 70)

# Key signals for fake listings:
# 1. Same phone number used for many listings across different areas/names
# 2. These are likely "bait" listings to generate calls to an agency

phone_to_lids = defaultdict(list)
for l in listings:
    phone = l.get("posted_by_contact","")
    if phone:
        phone_to_lids[phone].append(l["listing_id"])

# Distribution
dist = Counter(len(v) for v in phone_to_lids.values())
print("Phone -> listing count distribution:")
for cnt in sorted(dist.keys()):
    print(f"  {dist[cnt]} phones appear in {cnt} listings")

# What's the natural "cut-off"?
# Real agents may legitimately have 3-5 listings. But 28-35 is suspicious.
# The distribution drops sharply above 10 usually.
# Let's see cumulative from top:
sorted_phones = sorted(phone_to_lids.items(), key=lambda x: -len(x[1]))

print("\n  Top 30 phones by listing count:")
cumulative_lids = set()
for i, (phone, lids) in enumerate(sorted_phones[:30]):
    cumulative_lids.update(lids)
    # Look at names used with this phone
    names = set(l.get("posted_by_name","") for l in listings if l["listing_id"] in set(lids))
    print(f"  {i+1}. {phone}: {len(lids)} listings, {len(names)} different names: {list(names)[:4]}")

# Multiple different names for same phone is VERY suspicious
print("\n  Phones with multiple different names (clearest fake signal):")
multi_name_phones = []
for phone, lids in phone_to_lids.items():
    names = set(l.get("posted_by_name","") for l in listings if l["listing_id"] in set(lids))
    if len(names) > 2 and len(lids) >= 10:
        multi_name_phones.append((phone, lids, names))

multi_name_phones.sort(key=lambda x: -len(x[1]))
for phone, lids, names in multi_name_phones[:10]:
    print(f"  {phone}: {len(lids)} listings, {len(names)} names: {list(names)[:5]}")

# The clearly fake ones are those with many listings AND multiple different names
# They're using a single fake contact number but listing as different "sellers"
fake_ids = set()
for phone, lids, names in multi_name_phones:
    if len(names) > 2:  # definitely not one real person
        fake_ids.update(lids)

print(f"\n  Fake IDs (phones with 10+ listings AND 3+ names): {len(fake_ids)}")

# But also include very high count phones with even 1-2 names
for phone, lids in sorted_phones:
    if len(lids) >= 20:  # anyone with 20+ listings is suspicious
        fake_ids.update(lids)

print(f"  Fake IDs (also including 20+ listings per phone): {len(fake_ids)}")

# Let's try a cleaner hypothesis: look at "posted_by" field
print("\n  Posted by type distribution:")
posted_by_types = Counter(l.get("posted_by","") for l in listings)
for ptype, cnt in posted_by_types.most_common():
    print(f"  {ptype}: {cnt}")

# Owner-posted listings with same number = more suspicious than agent
# Agent phones being shared is less suspicious (agencies have one number)
print("\n  Phone usage by poster type:")
for phone, lids in sorted_phones[:10]:
    phone_listings = [l for l in listings if l["listing_id"] in set(lids)]
    by_type = Counter(l.get("posted_by","") for l in phone_listings)
    print(f"  {phone}: {by_type}")

q9 = sorted(list(fake_ids))
print(f"\n  Q9 = {len(q9)} fake listing IDs")
print(f"  First 10: {q9[:10]}")

# ============================================================
# Q6 FINAL: With fake exclusions
# ============================================================
print("\n" + "=" * 70)
print("Q6 FINAL with fake exclusions")
print("=" * 70)
exclude = set(q4) | set(q9)
eligible = [l for l in listings
            if l.get("is_live") == True
            and l.get("bedroom") == 2
            and l["listing_id"] not in exclude]

valid = [(l["price"] / l["carpet_area"]) 
         for l in eligible 
         if l.get("price") and l.get("price") > 0 and l.get("carpet_area") and l.get("carpet_area") > 0]

if valid:
    q6 = round(sum(valid)/len(valid), 2)
    print(f"  Eligible 2BHK: {len(eligible)}, Valid: {len(valid)}")
    print(f"  Q6 = {q6}")

# ============================================================
# Q8 FINAL - with future-dated listing check
# ============================================================
print("\n" + "=" * 70)
print("Q8: Future-dated listings (data quality issue)")
print("=" * 70)
future_lids = []
for l in listings:
    ps = l.get("posted_at","")
    try:
        if ps.endswith("Z"):
            dt = datetime.fromisoformat(ps.replace("Z","+00:00"))
        else:
            dt = datetime.fromisoformat(ps)
        dt_ist = dt.astimezone(IST)
        if dt_ist > REFERENCE:  # posted AFTER reference date
            future_lids.append((l["listing_id"], dt_ist.isoformat()))
    except:
        pass
print(f"  Listings with posted_at > REFERENCE: {len(future_lids)}")
for lid, ts in future_lids[:10]:
    print(f"    {lid}: {ts}")

print(f"  NOTE: These shouldn't appear in any time-window analysis")

# ============================================================
# FINAL ANSWERS
# ============================================================
print("\n" + "=" * 70)
print("FINAL ANSWERS")
print("=" * 70)
print(f"  Q1 total_listing_records:    {listings_data['count_fetched']}")
print(f"  Q2 unique_properties:        {len(set(l['listing_id'] for l in listings))}")
print(f"  Q3 active_listings:          {sum(1 for l in listings if l.get('is_live'))}")
print(f"  Q4 corrupt_listing_ids:      {len(q4)} items")
print(f"  Q5 total_monthly_rent:       {total_rent}")
print(f"  Q6 avg_price_per_sqft_2bhk:  {q6}")
print(f"  Q7 costliest_project:        {q7}")
print(f"  Q8 listings_last_7_days:     129")
print(f"  Q9 fake_listing_ids:         {len(q9)} items")
print(f"  Q10 projects_wrong_count:    295")

final_answers = {
    "total_listing_records": listings_data["count_fetched"],
    "unique_properties": len(set(l["listing_id"] for l in listings)),
    "active_listings": sum(1 for l in listings if l.get("is_live")),
    "corrupt_listing_ids": q4,
    "total_monthly_rent": total_rent,
    "avg_price_per_sqft_2bhk": q6,
    "costliest_project": q7,
    "listings_last_7_days": 129,
    "fake_listing_ids": q9,
    "projects_with_wrong_listing_count": 295
}

with open("data/FINAL_ANSWERS.json", "w", encoding="utf-8") as f:
    json.dump(final_answers, f, indent=2, ensure_ascii=False)
print("\nSaved to data/FINAL_ANSWERS.json")
