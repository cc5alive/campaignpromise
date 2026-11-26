"""Shortlist promise-like sentences from archived campaign pages for human/AI drafting.

Scores each sentence by commitment language and by the pilot issues
(immigration, the 2025 budget reconciliation bill topics, crypto) and writes
data/promises/candidates/<member>.json. This is a reading aid only: nothing
here is a promise until a drafter picks it and a reviewer approves it.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS = {
    "Immigration": r"\bborder|immigra|illegal alien|illegal immigra|\bICE\b|deport|asylum|sanctuary|\bwall\b|cartel",
    "Fentanyl": r"fentanyl|opioid|drug traffick",
    "Health care": r"affordable care act|\bACA\b|obamacare|health insurance|premiums|health care costs|cost of health care|pre-existing condition",
    "Medicaid": r"medicaid",
    "Social Security & Medicare": r"social security|medicare",
    "Taxes": r"\btax|\bSALT\b|child tax credit|tariff|IRS\b",
    "Federal spending": r"spending|deficit|national debt|balanced budget|\bdebt\b|wasteful",
    "Abortion": r"planned parenthood|abortion|reproductive|\bRoe\b|pro-life|unborn",
    "Crypto": r"crypto|digital asset|stablecoin|bitcoin|blockchain|\bCBDC\b|central bank digital",
    "Food assistance": r"\bSNAP\b|food stamp|food assistance",
    "Ukraine": r"ukrain|russia|putin",
    "Elections": r"voter id|photo id|proof of citizenship|non-?citizens? vot|election integrity|secure elections|voting rights|right to vote|voter suppression",
    "Guns": r"second amendment|2nd amendment|gun rights|right to bear arms|gun safety|gun violence|assault weapon|background check",
    "Gender": r"transgender|gender[- ]affirming|gender transition|biological (sex|male|female)|sex change|gender ideology",
    "Stock trading": r"stock trad|trading stock|ban members of congress from|insider trading|own(ing)? stocks?",
}
CUE = re.compile(r"\b(i will|will|i'll|committed to|pledge|promise|never|always|fight(s|ing)? (to|for|against)|support(s)?|oppose(s)?|vote (to|for|against)|must|believes?|stand up|protect|end|repeal|secure|cut)\b", re.I)
PAST_ONLY = re.compile(r"\b(voted|passed|introduced|helped pass|secured|delivered|led the)\b", re.I)


def sentences(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 25:
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", line):
            s = s.strip()
            if 25 <= len(s) <= 420:
                out.append(s)
    return out


def score(s):
    topics = [t for t, rx in TOPICS.items() if re.search(rx, s, re.I)]
    cue = bool(CUE.search(s))
    sc = 2 * len(topics) + (3 if cue else 0) + (2 if re.search(r"\b(will|I will|never|pledge|promise)\b", s, re.I) else 0)
    if PAST_ONLY.search(s) and not re.search(r"\bwill\b", s, re.I):
        sc -= 2
    return sc, topics


def run(key):
    folder = ROOT / "archive" / "2024" / key
    man = json.loads((folder / "manifest.json").read_text())
    seen, cands = set(), []
    for p in man["pages"]:
        if "error" in p or re.search(r"/20\d\d/\d\d/", p["original"]):
            continue  # skip news posts
        text = (ROOT / p["text_file"]).read_text(encoding="utf-8")
        for s in sentences(text):
            k = re.sub(r"\W+", "", s.lower())[:120]
            if k in seen:
                continue
            seen.add(k)
            sc, topics = score(s)
            if sc >= 5 and topics:
                cands.append({"score": sc, "topics": topics, "sentence": s, "page": p["original"], "file": p["file"], "snapshot": p["timestamp"]})
    cands.sort(key=lambda c: -c["score"])
    # CAND_DIR lets a rescan write elsewhere so earlier selections (which point at
    # candidate indexes) keep resolving to the same sentences.
    out = ROOT / "data" / "promises" / os.environ.get("CAND_DIR", "candidates")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{key}.json").write_text(json.dumps({"member": key, "pages": len(man["pages"]), "candidates": cands[:int(os.environ.get("CAND_TOP", "25"))]}, indent=1, ensure_ascii=False), encoding="utf-8")
    return len(man["pages"]), len(cands)


if __name__ == "__main__":
    keys = sys.argv[1:] or sorted(p.name for p in (ROOT / "archive" / "2024").iterdir() if p.is_dir())
    for k in keys:
        try:
            print(k, *run(k))
        except FileNotFoundError:
            print(k, "no archive yet")
