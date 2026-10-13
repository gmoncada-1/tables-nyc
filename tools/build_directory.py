"""Build data/nyc-directory.json from NYC Open Data (DOHMH Restaurant Inspection Results, 43nn-pn8j).
One row per restaurant (CAMIS) inspected since 2023, compact keys for the app."""
import json, urllib.request, urllib.parse, datetime
BASE = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
since = (datetime.date.today() - datetime.timedelta(days=3*365)).isoformat()
cols = "camis,dba,boro,building,street,zipcode,cuisine_description,latitude,longitude"
rows, off = {}, 0
while True:
    q = {"$select": cols + ",max(inspection_date) as last", "$group": cols,
         "$where": f"inspection_date > '{since}'", "$limit": "50000", "$offset": str(off), "$order": "camis"}
    url = BASE + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=120) as r:
        page = json.load(r)
    for x in page:
        c = x.get("camis"); 
        if not c: continue
        prev = rows.get(c)
        if prev and prev.get("last","") >= x.get("last",""): continue
        rows[c] = x
    if len(page) < 50000: break
    off += 50000
out = []
for c, x in rows.items():
    try: lat, lng = round(float(x.get("latitude") or 0), 5), round(float(x.get("longitude") or 0), 5)
    except ValueError: lat = lng = 0
    name = (x.get("dba") or "").strip()
    if not name: continue
    addr = " ".join(p for p in [(x.get("building") or "").strip(), (x.get("street") or "").strip().title()] if p)
    out.append([c, name.title() if name.isupper() else name, x.get("boro","").title(), addr, x.get("zipcode",""), x.get("cuisine_description",""), lat or None, lng or None])
out.sort(key=lambda r: r[1].lower())
meta = {"source": "NYC Open Data - DOHMH New York City Restaurant Inspection Results (43nn-pn8j)", "url": "https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j",
        "inspected_since": since, "built": datetime.date.today().isoformat(), "fields": ["camis","name","boro","address","zip","cuisine","lat","lng"], "count": len(out)}
json.dump({"meta": meta, "rows": out}, open("data/nyc-directory.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(meta)
