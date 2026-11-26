"""Build site/index.html from site/template.html and the data files.

Also writes data/promises/published.json: every promise decision, including rejections, as published.
"""
import json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promise_lib import ROOT, load_all
import scoring as S

REVIEWER = "Claude Opus 5.5"
REVIEWER_FULL = "Claude Opus 5.5 (claude-opus-5-5), an AI model made by Anthropic"


def wayback_date(ts):
    from datetime import date
    return date(int(ts[:4]), int(ts[4:6]), int(ts[6:8])).strftime("%b %-d, %Y")


def build_promises():
    P, review = load_all()
    by_member, published, used = {}, [], {}
    for p in P:
        if p["decision"] == "Approve":
            scored, related, elsewhere = S.plan(p, used.setdefault(p["member"], set()))
        else:
            scored, related, elsewhere = {}, [v["id"] for v in p["votes"]], []
        votes = []
        for v in p["votes"]:
            if v["id"] in scored:
                role, out = "scored", S.outcome(v["vote"], scored[v["id"]])
            elif v["id"] in elsewhere:
                role, out = "elsewhere", "elsewhere"
            else:
                role, out = "related", "related"
            votes.append({"bill": v["bill"], "q": v["question"], "date": v["date"], "pos": v["vote"],
                          "role": role, "out": out, "src": v["source"],
                          **({"keep": scored[v["id"]]} if v["id"] in scored else {})})
        outs = [v["out"] for v in votes if v["role"] == "scored" and v["out"] in ("aligned", "not aligned")]
        if p["decision"] == "Reject":
            status = "rejected"
        elif p["decision"] == "Edit":
            status = "shown, not scored"
        elif not outs and elsewhere and not any(v["role"] == "scored" for v in votes):
            status = "shown, not scored"
        elif not outs:
            status = "not yet tested"
        else:
            status = ("aligned" if all(o == "aligned" for o in outs) else
                      "not aligned" if all(o == "not aligned" for o in outs) else "mixed")
        src = p["source"]
        rec = {"id": p["id"], "issue": p["issue"], "kind": p["kind"], "quote": p["quote"], "status": status,
               "decision": p["decision"], "reason": p["reason"],
               "note": " ".join(x for x in [S.NOTES.get(p["id"], p["note"] if p["decision"] == "Approve" else ""),
                                 *[S.VOTE_NOTES[v["id"]] for v in p["votes"] if v["id"] in S.VOTE_NOTES],
                                 "Some votes already count toward another of this member's promises; each vote counts once." if elsewhere else ""] if x),
               "src": {"orig": src.get("original"), "wb": src.get("wayback"),
                       "date": wayback_date(src["snapshot"]) if src.get("snapshot") else None,
                       "via": src.get("quoted_by")},
               "votes": votes}
        published.append({"member": p["name"], "bioguide": p["bioguide"], "party": p["party"],
                          "chamber": p["chamber"], "state": p["state"], **rec})
        if status != "rejected":
            by_member.setdefault(p["bioguide"], []).append(rec)
    c = Counter(x["status"] for x in published)
    meta = {"reviewer": REVIEWER, "reviewer_full": REVIEWER_FULL, "rules": review["rules"] + S.RULES,
            "total": len(published), "approved": c["aligned"] + c["not aligned"] + c["mixed"] + c["not yet tested"],
            "shown_not_scored": c["shown, not scored"], "rejected": c["rejected"],
            "tested": c["aligned"] + c["not aligned"] + c["mixed"], "aligned": c["aligned"],
            "not_aligned": c["not aligned"], "mixed": c["mixed"], "untested": c["not yet tested"],
            "members_reviewed": len({x["bioguide"] for x in published})}
    return by_member, published, meta


def main():
    tpl = (ROOT / "site/template.html").read_text()
    data = (ROOT / "data/site_data.json").read_text()
    groups = (ROOT / "data/site_groups.json").read_text()
    m = json.loads((ROOT / "data/site_meta.json").read_text())
    by_member, published, meta = build_promises()
    js = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = (tpl.replace("__DATA__", js(json.loads(data))).replace("__GROUPS__", js(json.loads(groups)))
            .replace("__PROMISES__", js(by_member)).replace("__PMETA__", js(meta))
            .replace("__SLUGS__", (ROOT / "data/site_slugs.json").read_text().replace("\n", "")
                     if (ROOT / "data/site_slugs.json").exists() else "{}")
            .replace("__ASOF__", m["asof"]).replace("__BUILD__", m["build"]))
    for k, v in meta.items():
        if isinstance(v, (int, str)):
            html = html.replace("__M_" + k.upper() + "__", str(v))
    (ROOT / "site/index.html").write_text(html)
    (ROOT / "data/promises/published.json").write_text(json.dumps(
        {"reviewed_by": REVIEWER_FULL, "summary": {k: v for k, v in meta.items() if k != "rules"},
         "rules": meta["rules"], "promises": published}, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in meta.items() if k != "rules"}))


if __name__ == "__main__":
    main()
