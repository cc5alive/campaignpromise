"""Archive pilot members' 2024 campaign pages from the Wayback Machine.

For each member, look up snapshots of their campaign domains taken between
the window dates, pick the latest snapshot of the home page and of each
issues/priorities page, download the original HTML (Wayback "id_" mode, no
toolbar), extract readable text, and write:

  archive/2024/<member>/<slug>.html   original bytes as served by Wayback
  archive/2024/<member>/<slug>.txt    extracted text used for promise quotes
  archive/2024/manifest.json          URL, snapshot time, Wayback link, SHA-256

Anyone can re-download a Wayback link and compare its SHA-256 to the manifest.
"""
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "pipeline" / "pilot_members.json").read_text())
OUT = ROOT / "archive" / "2024"
UA = {"User-Agent": "campaignpromise.org archiver (contact via github.com/cc5alive/campaignpromise)"}
ISSUE_RE = re.compile(r"issue|priorit|plan|polic|platform|agenda|vision|stand|record|accomplish|values|fight|position", re.I)
SKIP_RE = re.compile(r"\.(js|css|png|jpe?g|gif|svg|ico|pdf|xml|json|woff2?)(\?|$)|wp-json|/feed|/tag/|/category/|/page/\d|donate|secure|act\.|actblue|winred|/es/|privacy|terms|login|cart|shop|store", re.I)
MAX_PAGES = 14


def get(url, tries=5, timeout=60):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(10 * (i + 1))
                continue
            return r
        except requests.RequestException:
            time.sleep(10 * (i + 1))
    return None


def norm(u):
    p = urlparse(u if "://" in u else "http://" + u)
    host = p.netloc.lower().removeprefix("www.").split(":")[0]
    path = re.sub(r"/+$", "", p.path) or "/"
    return host + path.lower()


def snapshots(domain, start, end):
    url = ("https://web.archive.org/cdx/search/cdx?url=" + domain + "&matchType=domain"
           f"&from={start}&to={end}&output=json&filter=statuscode:200"
           "&filter=mimetype:text/html&fl=timestamp,original&limit=20000")
    r = get(url, timeout=120)
    if not r or r.status_code != 200:
        return []
    try:
        rows = r.json()[1:]
    except ValueError:
        return []
    latest = {}
    for ts, orig in rows:
        if SKIP_RE.search(orig) or "?" in orig:
            continue
        k = norm(orig)
        if k not in latest or ts > latest[k][0]:
            latest[k] = (ts, orig)
    return list(latest.items())


def pick(snaps):
    home = [s for s in snaps if s[0].split("/", 1)[1] == ""]
    issues = [s for s in snaps if ISSUE_RE.search(s[0].split("/", 1)[1])]
    issues.sort(key=lambda s: (s[0].count("/"), s[0]))
    chosen = home[:1] + issues
    seen, out = set(), []
    for s in chosen:
        if s[0] not in seen:
            seen.add(s[0])
            out.append(s)
    return out[:MAX_PAGES]


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "iframe", "form"]):
        t.decompose()
    for t in soup.select("nav, footer, header .menu, [aria-hidden=true]"):
        t.decompose()
    text = soup.get_text("\n")
    lines = [re.sub(r"[ \t ]+", " ", l).strip() for l in text.splitlines()]
    out, prev = [], None
    for l in lines:
        if l and l != prev:
            out.append(l)
        prev = l
    return "\n".join(out)


def slug(key):
    path = key.split("/", 1)[1]
    s = re.sub(r"[^a-z0-9]+", "-", path).strip("-")
    return s or "home"


def main():
    start, end = CFG["window"]["from"], CFG["window"]["to"]
    manifest = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "window": CFG["window"], "members": {}}
    for m in CFG["members"]:
        entry = {"name": m["name"], "domains_tried": m["domains"], "pages": []}
        for d in m["domains"]:
            snaps = snapshots(d, start, end)
            entry.setdefault("snapshots_found", {})[d] = len(snaps)
            time.sleep(3)
            if not snaps:
                continue
            for key, (ts, orig) in pick(snaps):
                wb = f"https://web.archive.org/web/{ts}id_/{orig}"
                r = get(wb)
                time.sleep(3)
                if not r or r.status_code != 200 or not r.content:
                    entry["pages"].append({"original": orig, "timestamp": ts, "error": getattr(r, "status_code", "no response")})
                    continue
                folder = OUT / m["key"]
                folder.mkdir(parents=True, exist_ok=True)
                name = slug(key)
                (folder / f"{name}.html").write_bytes(r.content)
                txt = extract_text(r.content)
                (folder / f"{name}.txt").write_text(txt, encoding="utf-8")
                entry["pages"].append({
                    "original": orig, "timestamp": ts,
                    "wayback": f"https://web.archive.org/web/{ts}/{orig}",
                    "wayback_raw": wb,
                    "file": f"archive/2024/{m['key']}/{name}.html",
                    "text_file": f"archive/2024/{m['key']}/{name}.txt",
                    "bytes": len(r.content),
                    "sha256_html": hashlib.sha256(r.content).hexdigest(),
                    "sha256_text": hashlib.sha256(txt.encode("utf-8")).hexdigest(),
                })
            if entry["pages"]:
                break  # first domain with snapshots wins
        manifest["members"][m["key"]] = entry
        print(m["key"], {k: v for k, v in entry.get("snapshots_found", {}).items()}, len(entry["pages"]), "pages", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
