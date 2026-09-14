import json
d=json.load(open('data/listings_all.json'))
print(f'Fetched: {len(d["records"])} listings, API total: {d["total_from_api"]}')
print(f'File size: {len(json.dumps(d))} bytes')
if d["records"]:
    print(f'Sample keys: {list(d["records"][0].keys())}')
    print(f'is_live sample: {d["records"][0].get("is_live")}')
