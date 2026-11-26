"""Shared loader: every promise draft, normalized, with its review decision and vote positions."""
import json, re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUNDS = ["pilot_round1", "round2", "round3", "issues", "round4", "round5", "round6", "round7", "round8"]
PREFIX = {"P": "P", "ROUND2": "R2", "ROUND3": "R3", "ISSUES": "NI", "ROUND4": "R4", "ROUND5": "R5", "ROUND6": "R6", "ROUND7": "R7", "ROUND8": "R8"}
LABEL = {"S1582": "GENIUS Act", "S5": "Laken Riley Act", "HR29": "Laken Riley Act (House version)",
         "HR1": "2025 reconciliation bill (H.R. 1)", "HR3633": "CLARITY Act", "HR1919": "Anti-CBDC Act",
         "S331": "HALT Fentanyl Act", "HR21": "Born-Alive Abortion Survivors Protection Act",
         "S6": "Born-Alive Abortion Survivors Protection Act",
         "HR1834": "3-year ACA premium tax credit extension", "S3385": "3-year ACA premium tax credit extension",
         "HR4": "Rescissions Act of 2025", "HR22": "SAVE Act", "HR2913": "Ukraine Support Act",
         "HR1041": "Veterans 2nd Amendment Protection Act", "HR1958": "Deporting Fraudsters Act",
         "HR498": "Do No Harm in Medicaid Act", "HR7008": "Stop Insider Trading Act"}


# Plain labels for amendment votes, whose official question text names only the procedure.
VOTE_LABEL = {
    "senate-1-00344": "Murray amendment to strike the Planned Parenthood defunding (motion to waive the budget rules)",
    "senate-1-00361": "Kim amendment to strike the limits on Medicaid provider payments",
    "senate-1-00369": "Klobuchar amendment to strike the delayed SNAP cost-sharing provision",
}


def norm_id(raw):
    m = re.match(r"([A-Z]+\d?)-?(\d{3})$", raw)
    return f"{PREFIX[m.group(1)]}-{m.group(2)}"


def iso_date(raw):
    raw = (raw or "").strip()
    for fmt, part in (("%d-%b-%Y", raw), ("%B %d, %Y", ",".join(raw.split(",")[:2]))):
        try:
            return datetime.strptime(part.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return raw


def members():
    out = {}
    for f in sorted((ROOT / "pipeline").glob("*members*.json")):
        for m in json.loads(f.read_text())["members"]:
            out[m["key"]] = m
    return out


def votes_index():
    return {Path(v["file"]).stem: v for v in json.loads((ROOT / "votes/119/index.json").read_text())["votes"]}


def vote_info(vid, member, V, LIS):
    v = V[vid]
    q = v["question"] or ""
    short = ("final passage" if "Passage" in q else "final passage (Senate version)" if "Concur" in q
             else "vote to start debate (needed 60)" if "Cloture" in q else q.strip())
    short = VOTE_LABEL.get(vid, short)
    who = member["bioguide"] if member["chamber"] == "House" else LIS.get(member["bioguide"])
    return {"id": vid, "bill": LABEL.get(v["bill"], v.get("bill_label", v["bill"])), "question": short,
            "date": iso_date(v["date"]), "vote": v["positions"].get(who, {}).get("vote", "Not voting"),
            "source": v["source"]}


def load_all():
    M, V = members(), votes_index()
    LIS = json.loads((ROOT / "data/bioguide_to_lis.json").read_text())
    review = json.loads((ROOT / "data/promises/review_decisions.json").read_text())
    out = []
    for rnd in ROUNDS:
        for p in json.loads((ROOT / f"data/promises/{rnd}_drafts.json").read_text())["promises"]:
            pid = norm_id(p["id"])
            m = M[p["member"]]
            vids = [v["id"] for v in p["votes"]] if "votes" in p else p.get("suggested_test_votes", [])
            d = review["decisions"][pid]
            out.append({"id": pid, "member": p["member"], "bioguide": m["bioguide"], "name": m["name"],
                        "party": m["party"], "chamber": m["chamber"], "state": m["state"],
                        "quote": p["quote"], "kind": p["kind"], "issue": p["issue"], "source": p["source"],
                        "note": p.get("note", ""), "votes": [vote_info(x, m, V, LIS) for x in vids],
                        "decision": d["decision"], "reason": d["reason"]})
    return out, review
