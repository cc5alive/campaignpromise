"""Turn hand-picked selections into verified promise drafts.

Input:  data/promises/<round>_selections.json  (list of picks)
Output: data/promises/<round>_drafts.json

Each pick: {"member": key, "page": original URL, "quote": exact text,
            "kind": "Pledge"|"Stated position", "issue": ..., "votes": [vote ids], "note": ...}
A quote is kept only if it appears word for word in the archived HTML.
"""
import json, re, sys
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
rnd = sys.argv[1]
members_file = sys.argv[2]
picks = json.loads((ROOT / f"data/promises/{rnd}_selections.json").read_text())
M = {m["key"]: m for f in members_file.split(",") for m in json.loads((ROOT / "pipeline" / f).read_text())["members"]}
LIS = json.loads((ROOT / "data/bioguide_to_lis.json").read_text())


def iso_date(raw):
    """House XML gives 22-May-2025; Senate XML gives 'July 1, 2025,  11:56 AM'. Return YYYY-MM-DD."""
    raw = (raw or "").strip()
    for fmt, part in (("%d-%b-%Y", raw), ("%B %d, %Y", ",".join(raw.split(",")[:2]))):
        try:
            return datetime.strptime(part.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return raw


V = {Path(v["file"]).stem: v for v in json.loads((ROOT / "votes/119/index.json").read_text())["votes"]}
LABEL = {"S1582": "GENIUS Act", "S5": "Laken Riley Act", "HR29": "Laken Riley Act (House version)",
         "HR1": "2025 reconciliation bill", "HR3633": "CLARITY Act", "HR1919": "Anti-CBDC Act",
         "S331": "HALT Fentanyl Act", "HR21": "Born-Alive Abortion Survivors Protection Act",
         "S6": "Born-Alive Abortion Survivors Protection Act",
         "HR1834": "3-year ACA premium tax credit extension", "S3385": "3-year ACA premium tax credit extension"}
cache = {}

def page_text(path):
    if path not in cache:
        s = BeautifulSoup((ROOT / path).read_bytes(), "html.parser")
        for t in s(["script", "style", "noscript"]):
            t.decompose()
        cache[path] = re.sub(r"\s+", " ", s.get_text(" "))
    return cache[path]

out, rejected = [], []
for i, p in enumerate(picks, 1):
    if "cand" in p:  # resolve a shortlist index into its exact sentence and page
        cdir = p.get("cand_dir", "candidates")
        c = json.loads((ROOT / f"data/promises/{cdir}/{p['member']}.json").read_text())["candidates"][p["cand"]]
        p["quote"], p["page"] = c["sentence"], c["page"]
    m = M[p["member"]]
    man = json.loads((ROOT / f"archive/2024/{p['member']}/manifest.json").read_text())
    pg = next((x for x in man["pages"] if x.get("original") == p["page"] and "error" not in x), None)
    if not pg or re.sub(r"\s+", " ", p["quote"]) not in page_text(pg["file"]):
        rejected.append((p["member"], p["quote"][:70]))
        continue
    who = m["bioguide"] if m["chamber"] == "House" else LIS.get(m["bioguide"])
    votes = []
    for vid in p.get("votes", []):
        v = V[vid]
        q = v["question"] or ""
        short = ("final passage" if "Passage" in q else "final passage (Senate version)" if "Concur" in q
                 else "vote to start debate (needed 60)" if "Cloture" in q else q)
        votes.append({"id": vid, "bill": LABEL.get(v["bill"], v.get("bill_label", v["bill"])), "question": short, "date": iso_date(v["date"]),
                      "vote": v["positions"].get(who, {}).get("vote", "not found"), "source": v["source"]})
    out.append({"id": f"{rnd.upper()}-{len(out)+1:03d}", "member": p["member"], "name": m["name"], "party": m["party"],
                "chamber": m["chamber"], "state": m["state"], "quote": p["quote"], "kind": p["kind"], "issue": p["issue"],
                "source": {"original": pg["original"], "snapshot": pg["timestamp"], "wayback": pg["wayback"],
                           "file": pg["file"], "sha256_html": pg["sha256_html"]},
                "quote_verified_in_source": True, "votes": votes, "note": p.get("note", ""),
                "status": "draft", "drafted_by": "Claude (AI)", "reviewed_by": None})
(ROOT / f"data/promises/{rnd}_drafts.json").write_text(json.dumps({"round": rnd, "promises": out, "rejected": rejected}, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(out), "drafts;", len(rejected), "rejected:", rejected)
