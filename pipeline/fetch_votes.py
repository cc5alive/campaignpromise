"""Download official roll-call votes for the pilot bills (119th Congress).

Sources (the chambers' own records):
  Senate: senate.gov roll-call vote menus and per-vote XML
  House:  clerk.house.gov/evs/<year>/rollNNN.xml

Writes votes/119/<chamber>-<year or session>-<number>.xml for every roll call
on a target bill, plus votes/119/index.json with one row per vote and each
member's position keyed by Bioguide ID (House) or LIS ID + name (Senate).
"""
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "votes" / "119"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "campaignpromise.org vote fetcher (github.com/cc5alive/campaignpromise)"}

# Pilot bills. Keys are normalized bill numbers: chamber letters + number, no spaces or dots.
TARGETS = {
    "S1582": "GENIUS Act (stablecoins)",
    "HR3633": "CLARITY Act (digital asset market structure)",
    "HR1919": "Anti-CBDC Surveillance State Act",
    "S5": "Laken Riley Act (immigration detention)",
    "HR29": "Laken Riley Act, House version",
    "HR1": "2025 budget reconciliation bill (One Big Beautiful Bill Act)",
    # Round 4 issues: fentanyl, abortion, health care
    "S331": "HALT Fentanyl Act",
    "HR21": "Born-Alive Abortion Survivors Protection Act",
    "S6": "Born-Alive Abortion Survivors Protection Act, Senate version",
    "HR1834": "3-year extension of enhanced ACA premium tax credits (passed House Jan 8, 2026 under the title Breaking the Gridlock Act)",
    "HR4": "Rescissions Act of 2025 ($9 billion spending cut)",
    "S3385": "3-year extension of enhanced ACA premium tax credits (Senate Democratic bill, Dec 11, 2025)",
    # Round 7: more votes that test promises from both parties
    "HR22": "SAVE Act (proof of citizenship to register to vote)",
    "HR2913": "Ukraine Support Act",
    "HR1041": "Veterans 2nd Amendment Protection Act",
    "HR1958": "Deporting Fraudsters Act",
    "HR498": "Do No Harm in Medicaid Act",
    "HR7008": "Stop Insider Trading Act (partial stock ban plus voter ID)",
}
# Every roll call seen (both chambers), without member positions: lets us find the
# official record for any new issue without guessing roll numbers.
CATALOG = []


def norm_bill(s):
    s = (s or "").upper().replace(".", "").replace(" ", "")
    s = s.replace("HRES", "HRES").replace("HJRES", "HJRES")
    return s


def get(url, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            if r.status_code in (200, 404):
                return r
        except requests.RequestException:
            pass
        time.sleep(5 * (i + 1))
    return None


def senate():
    rows = []
    for sess, year in ((1, 2025), (2, 2026)):
        menu = get(f"https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_119_{sess}.xml")
        if not menu or menu.status_code != 200:
            print("senate menu missing", sess, flush=True)
            continue
        root = ET.fromstring(menu.content)
        for v in root.iter("vote"):
            issue = norm_bill(v.findtext("issue"))
            CATALOG.append({"chamber": "Senate", "session": sess, "number": int(v.findtext("vote_number")),
                            "date": v.findtext("vote_date"), "bill": issue, "question": v.findtext("question"),
                            "result": v.findtext("result"), "title": v.findtext("title")})
            if issue not in TARGETS:
                continue
            num = int(v.findtext("vote_number"))
            url = f"https://www.senate.gov/legislative/LIS/roll_call_votes/vote119{sess}/vote_119_{sess}_{num:05d}.xml"
            r = get(url)
            time.sleep(1)
            if not r or r.status_code != 200:
                continue
            path = OUT / f"senate-{sess}-{num:05d}.xml"
            path.write_bytes(r.content)
            x = ET.fromstring(r.content)
            members = {}
            for m in x.iter("member"):
                members[m.findtext("lis_member_id")] = {
                    "name": f"{m.findtext('first_name')} {m.findtext('last_name')}",
                    "party": m.findtext("party"), "state": m.findtext("state"),
                    "vote": m.findtext("vote_cast"),
                }
            rows.append({
                "chamber": "Senate", "session": sess, "number": num, "date": x.findtext("vote_date"),
                "bill": issue, "bill_label": TARGETS[issue], "question": x.findtext("vote_question_text"),
                "vote_title": x.findtext("vote_title"), "result": x.findtext("vote_result_text"),
                "source": url, "file": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(r.content).hexdigest(), "positions": members,
            })
            print("senate", sess, num, issue, x.findtext("vote_question_text"), flush=True)
    return rows


def house():
    rows = []
    for year in (2025, 2026):
        misses = 0
        n = 0
        while misses < 3:
            n += 1
            url = f"https://clerk.house.gov/evs/{year}/roll{n:03d}.xml"
            r = get(url)
            time.sleep(0.3)
            if not r or r.status_code != 200 or b"<rollcall-vote" not in r.content[:2000]:
                misses += 1
                continue
            misses = 0
            try:
                x = ET.fromstring(r.content)
            except ET.ParseError:
                continue
            meta = x.find("vote-metadata")
            bill = norm_bill(meta.findtext("legis-num"))
            CATALOG.append({"chamber": "House", "year": year, "number": n, "date": meta.findtext("action-date"),
                            "bill": bill, "question": meta.findtext("vote-question"),
                            "result": meta.findtext("vote-result"), "title": meta.findtext("vote-desc")})
            if bill not in TARGETS:
                continue
            path = OUT / f"house-{year}-{n:03d}.xml"
            path.write_bytes(r.content)
            members = {}
            for rv in x.iter("recorded-vote"):
                leg = rv.find("legislator")
                members[leg.get("name-id")] = {
                    "name": leg.get("unaccented-name") or leg.text, "party": leg.get("party"),
                    "state": leg.get("state"), "vote": rv.findtext("vote"),
                }
            rows.append({
                "chamber": "House", "year": year, "number": n, "date": meta.findtext("action-date"),
                "bill": bill, "bill_label": TARGETS[bill], "question": meta.findtext("vote-question"),
                "vote_title": meta.findtext("vote-desc"), "result": meta.findtext("vote-result"),
                "source": url, "file": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(r.content).hexdigest(), "positions": members,
            })
            print("house", year, n, bill, meta.findtext("vote-question"), flush=True)
        print("house", year, "last roll checked", n, flush=True)
    return rows


def main():
    rows = senate() + house()
    rows.sort(key=lambda r: (r["date"] or "", r["chamber"], r["number"]))
    (OUT / "index.json").write_text(json.dumps({
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "targets": TARGETS, "votes": rows}, indent=1), encoding="utf-8")
    (OUT / "catalog.json").write_text(json.dumps(CATALOG, indent=0), encoding="utf-8")
    print(len(rows), "votes saved;", len(CATALOG), "roll calls catalogued")


if __name__ == "__main__":
    main()
