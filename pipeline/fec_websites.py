"""Look up each campaign committee's registered website on the FEC API.

Usage: python pipeline/fec_websites.py OUT.json C001,C002,... [candidate searches as "q|STATE|OFFICE"]
Uses FEC_API_KEY if set, else DEMO_KEY (low rate limit, so keep batches small).
"""
import json, os, sys, time
import requests

key = os.environ.get("FEC_API_KEY") or "DEMO_KEY"
out_path, ids = sys.argv[1], [i for i in sys.argv[2].split(",") if i]
searches = sys.argv[3:]
res = {"committees": {}, "searches": {}}


def get(url, params):
    params = dict(params, api_key=key)
    for i in range(6):
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 200:
            return r.json()
        time.sleep(15 * (i + 1))
    return {"error": r.status_code}


for cid in ids:
    j = get(f"https://api.open.fec.gov/v1/committee/{cid}/", {})
    c = (j.get("results") or [{}])[0]
    res["committees"][cid] = {"name": c.get("name"), "website": c.get("website"), "error": j.get("error")}
    time.sleep(2)
for s in searches:
    q, st, office = s.split("|")
    j = get("https://api.open.fec.gov/v1/candidates/search/", {"q": q, "state": st, "office": office})
    res["searches"][s] = [{"candidate_id": c["candidate_id"], "name": c["name"],
                           "committees": [[p["committee_id"], p["name"], p.get("cycles", [])[-3:]] for p in c.get("principal_committees", [])]}
                          for c in j.get("results", [])]
os.makedirs(os.path.dirname(out_path), exist_ok=True)
json.dump(res, open(out_path, "w"), indent=1)
print(json.dumps(res)[:2000])
