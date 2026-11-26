"""Write a static page for every member, a member index, and the sitemap.

Usage: python pipeline/build_member_pages.py OUT_DIR   (OUT_DIR gets m/<slug>/index.html, m/index.html, sitemap.xml)
Reads data/site_data.json, data/site_groups.json and data/promises/published.json. Standard library only.
"""
import json, re, sys, unicodedata
from datetime import date
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://campaignpromise.org"
STATES = {"AL":"Alabama","AK":"Alaska","AS":"American Samoa","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","GU":"Guam","HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","MP":"Northern Mariana Islands","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","PR":"Puerto Rico","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VI":"U.S. Virgin Islands","VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"}
PARTY = {"D": "Democrat", "R": "Republican", "I": "Independent"}
VS = {"aligned": ("vs-aligned", "Aligned"), "not aligned": ("vs-notaligned", "Not aligned"), "mixed": ("vs-mixed", "Mixed"),
      "not yet tested": ("vs-muted", "Not yet tested"), "shown, not scored": ("vs-muted", "Shown, not scored")}
ORDER = ["not aligned", "mixed", "aligned", "not yet tested", "shown, not scored"]
TESTED = ("aligned", "not aligned", "mixed")


def slug_for(r):
    s = unicodedata.normalize("NFKD", r["n"]).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") + "-" + r["s"].lower()


def where(r):
    if r["c"] == "S":
        return f"Senator, {STATES.get(r['s'], r['s'])}"
    role = "Delegate" if r.get("dl") else "Representative"
    dist = f", District {r['d']}" if r.get("d") else (" (at large)" if r.get("d") == 0 else "")
    return f"{role}, {STATES.get(r['s'], r['s'])}{dist}"


def money(v):
    a = abs(v)
    s = f"{a/1e6:.2f}".rstrip("0").rstrip(".") + "M" if a >= 1e6 else (f"{round(a/1e3)}K" if a >= 1e3 else str(round(a)))
    return ("−$" if v < 0 else "$") + s


def vote_row(v):
    if v["role"] == "related":
        o = '<span class="vs vs-muted">Related, not scored</span>'
    elif v["role"] == "elsewhere":
        o = '<span class="vs vs-muted">Counted on another promise</span>'
    elif v["out"] == "not counted":
        o = '<span class="vs vs-muted">Not counted</span>'
    else:
        o = f'<span class="vs {"vs-aligned" if v["out"] == "aligned" else "vs-notaligned"}">{"Aligned" if v["out"] == "aligned" else "Not aligned"}</span>'
    keep = f' · a {"yes" if v["keep"] == "Yea" else "no"} vote keeps this promise' if v.get("keep") else ""
    return (f'<div class="vrow"><div>{e(v["bill"])} <span class="vq">· {e(v["q"])} · {e(v["date"])}</span></div><div>{o}</div>'
            f'<div class="vq">Voted <a href="{e(v["src"])}">{e(v["pos"])}</a>{keep}</div><div></div></div>')


def card(p):
    cls, lab = VS[p["status"]]
    src = p["src"]
    link = f'<a href="{e(src["wb"])}">Campaign site, archived {e(src["date"])}</a>' if src.get("wb") else ""
    q = re.sub(r'^[“"]+|[”"]+$', "", p["quote"])
    dec = "approved" if p["decision"] == "Approve" else "shown, not scored"
    return (f'<article class="prom"><div class="ph"><span class="small">{e(p["issue"])} · {e(p["kind"])}</span><span class="vs {cls}">{lab}</span></div>'
            f'<blockquote>“{e(q)}”</blockquote><div class="small">{link}</div>'
            + "".join(vote_row(v) for v in p["votes"])
            + (f'<div class="small">{e(p["note"])}</div>' if p.get("note") else "")
            + f'<details class="small"><summary>Decision by Claude Opus 5.5: {dec}</summary><p>{e(p["reason"])}</p></details></article>')


def head(title, desc, url):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><meta name="theme-color" content="#0e6b5c">
<meta property="og:type" content="profile"><meta property="og:site_name" content="Campaign Promise"><meta property="og:url" content="{url}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:image" content="{BASE}/assets/og.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{BASE}/assets/og.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&family=Newsreader:opsz,wght@6..72,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/member.css"></head><body>
<div class="beta"><b>Beta.</b> Every promise decision on this site is made by Claude Opus 5.5, an AI model. <a href="/#method">How it works</a></div>
<header class="top"><div class="wrap topbar"><a class="brand" href="/">Campaign <span>Promise</span></a><nav><a href="/#scoreboard">Scoreboard</a><a href="/m/">All members</a><a href="/#method">How we know</a><a href="/#corrections">Corrections</a></nav></div></header>
<main class="wrap">"""


FOOT = """</main><footer class="wrap">Campaign Promise · Every quote links to its archived campaign page, every vote to the official roll call, every dollar to its FEC filing. Every promise decision is made by Claude Opus 5.5, an AI model made by Anthropic; the rules and every decision, including rejections, are <a href="https://github.com/cc5alive/campaignpromise/blob/main/data/promises/published.json">public</a>. Not affiliated with any party, candidate or group.</footer></body></html>"""


def member_page(r, ps, groups, slug):
    tested = [p for p in ps if p["status"] in TESTED]
    a = sum(p["status"] == "aligned" for p in tested)
    t = len(tested)
    if t >= 3:
        summ = f"{a} of {t} tested campaign promises aligned with votes"
    elif t:
        summ = f"{t} campaign promise{'s' if t > 1 else ''} tested so far"
    elif ps:
        summ = f"{len(ps)} campaign promise{'s' if len(ps) > 1 else ''} reviewed, none tested by a vote yet"
    else:
        summ = "Campaign promises not yet reviewed"
    party = PARTY.get(r["p"], r["p"])
    title = f"{r['n']} ({r['p']}-{r['s']}): campaign promises, votes and donors · Campaign Promise"
    desc = f"{where(r)}, {party}. {summ}. Every quote links to the archived campaign site and every vote to the official roll call."
    url = f"{BASE}/m/{slug}/"
    out = [head(title, desc, url)]
    out.append(f'<span class="pchip p-{r["p"]}">{e(party)}</span><h1>{e(r["n"])}</h1>'
               f'<div class="meta">{e(where(r))} · in Congress since {r["fy"]} · current term ends {r["te"][:4]}</div>')
    out.append('<h2>Promises and votes</h2>')
    if t >= 3:
        out.append(f'<div class="score"><b>{a} of {t}</b><span>tested promises aligned with votes</span></div>')
    elif ps:
        out.append(f'<p class="small">{e(summ)}. A score appears once at least 3 promises are tested.</p>')
    else:
        out.append('<p class="small">Not yet reviewed. We have not yet archived and reviewed this member\'s campaign promises.</p>')
    out += [card(p) for p in sorted(ps, key=lambda p: ORDER.index(p["status"]))]
    # money
    rows = []
    for k, g in groups.items():
        m = r["m"].get(k)
        if not m:
            continue
        for lab, v in (("Contributions (direct + earmarked)", m.get("d", 0) + m.get("e", 0)), ("Outside spending for", m.get("s", 0)), ("Outside spending against", m.get("o", 0))):
            if v:
                rows.append(f'<tr><td>{e(g["name"])} <span class="small">· {e(g["cat"])}</span></td><td>{lab}</td><td class="num">{money(v)}</td></tr>')
    out.append('<h2>Money from tracked groups, 2025–26 cycle</h2>')
    out.append(f'<table><tbody>{"".join(rows)}</tbody></table>' if rows else '<p class="small">No money recorded from the 9 tracked groups.</p>')
    if r.get("pcc"):
        out.append(f'<p class="small">Campaign committee: <a href="https://www.fec.gov/data/committee/{r["pcc"]}/?cycle=2026">{r["pcc"]} on FEC.gov</a></p>')
    out.append(f'<a class="btn" href="/#m-{r["id"]}">Open in the scoreboard</a>')
    ld = {"@context": "https://schema.org", "@type": "Person", "name": r["n"], "jobTitle": where(r), "affiliation": party, "url": url}
    out.append(f'<script type="application/ld+json">{json.dumps(ld)}</script>')
    out.append(FOOT)
    return "".join(out)


def main(out_dir):
    out = Path(out_dir)
    data = json.loads((ROOT / "data/site_data.json").read_text())
    groups = json.loads((ROOT / "data/site_groups.json").read_text())
    pub = json.loads((ROOT / "data/promises/published.json").read_text())["promises"]
    by = {}
    for p in pub:
        if p["status"] != "rejected":
            by.setdefault(p["bioguide"], []).append(p)
    slugs, urls = {}, [f"{BASE}/", f"{BASE}/m/"]
    for r in sorted(data, key=lambda r: (r["l"], r["n"])):
        s = slug_for(r)
        while s in slugs.values():
            s += "-2"
        slugs[r["id"]] = s
        d = out / "m" / s
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(member_page(r, by.get(r["id"], []), groups, s))
        urls.append(f"{BASE}/m/{s}/")
    # index page, grouped by state
    idx = [head("All members of Congress · Campaign Promise", "Every current member of Congress: campaign promises, votes and donors.", f"{BASE}/m/"),
           "<h1>All members of Congress</h1><p class='meta'>Senators and representatives by state.</p>"]
    for st in sorted({r["s"] for r in data}, key=lambda s: STATES.get(s, s)):
        rs = sorted([r for r in data if r["s"] == st], key=lambda r: (r["c"] != "S", r["l"]))
        idx.append(f"<h2>{e(STATES.get(st, st))}</h2><div class='idx'>" +
                   "".join(f'<a href="/m/{slugs[r["id"]]}/">{e(r["n"])} <span class="small">({r["p"]}{", Sen." if r["c"] == "S" else ""})</span></a>' for r in rs) + "</div>")
    idx.append(FOOT)
    (out / "m" / "index.html").write_text("".join(idx))
    today = date.today().isoformat()
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                     "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    (ROOT / "data/site_slugs.json").write_text(json.dumps(slugs, indent=0))
    print(len(slugs), "member pages")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "site")
