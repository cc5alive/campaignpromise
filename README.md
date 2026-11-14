# Campaign Promise

A nonpartisan scoreboard for every member of Congress: who funds them, what they promised, and how they voted. Every figure links to a government record.

Live prototype: published as a private Claude artifact for now; will move to campaignpromise.org.

## What's here

| Path | What it is |
| --- | --- |
| `site/index.html` | The prototype site, one self-contained page with data embedded |
| `site/template.html` | The page template the build fills with data |
| `data/members.json` | Current members from [unitedstates/congress-legislators](https://github.com/unitedstates/congress-legislators) |
| `data/fec/pas2_agg_2026.json` | Per-candidate totals from FEC bulk file `itpas2`, 2025–26: direct contributions (24K) and independent expenditures (24E for, 24A against), memo lines excluded |
| `data/fec/earmarks_15E_2026.txt` | Earmarked contributions (FEC bulk `itcont`, type 15E) by conduit, per candidate, plus each candidate's principal campaign committee (`ccl`) |
| `data/site_data.json` | Members joined with money, as embedded in the site |
| `pipeline/pilot_members.json` | The 10 members in the promise-scoring pilot |
| `pipeline/archive_campaign_pages.py` | Saves their 2024 campaign pages from the Wayback Machine with SHA-256 fingerprints |
| `archive/2024/` | Output of the archiver (written by GitHub Actions) |

## Principles

1. Every number links to its primary source.
2. Facts (a recorded vote, a reported dollar) are labeled separately from judgments (this vote tests that promise).
3. One published method for every party.
4. No score without its vote count; under 3 votes reads "Not yet tested."
5. Neutral words: aligned, not aligned, mixed, not yet tested.
6. Money is shown next to votes; the site never claims one caused the other.

## Data notes

- FEC bulk files last updated Nov 8, 2026, downloaded Nov 13, 2026.
- Money to joint fundraising committees, leadership PACs and caucus PACs is not yet counted.
- FEC type 24T (money earmarked *to* a group) is excluded; only 15E (money a group's PAC routed *to* a campaign) counts as earmarked.
