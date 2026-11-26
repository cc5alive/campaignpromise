"""Review decisions for promise drafts.

Made by Claude (AI) on 2026-11-15 at CC's request ("make your best choice for
everything"), applying the rules in RULES below. Each decision is one of:
  Approve - the cited vote directly tests what was promised; publish and score it.
  Edit    - keep it, but apply the stated action before publishing.
  Reject  - do not publish: the vote doesn't test it, it isn't a forward-looking
            promise, or the source can't be verified in our archive.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = [
    "Approve when the vote directly tests the specific commitment.",
    "A vote on a whole bill counts, in both directions, when the promised item was a central, widely reported provision (H.R.1's tax-cut extension, Medicaid and SNAP cuts, Planned Parenthood funding ban, border wall and Border Patrol/ICE money).",
    "Show as 'shown, not scored' (related vote) when the vote bears on the promise but a kept/broken call would rest on a contested reading: Social Security and Medicare (H.R.1 didn't change benefits), abortion-rights promises tested by the Born-Alive bill, child tax credit and middle-class tax promises (H.R.1 changed both in part), SALT repeal, and 'work across the aisle' promises.",
    "Test promises to cut spending against the Rescissions Act of 2025 (H.R. 4), a direct $9 billion spending cut; H.R.1, whose net effect on spending depends on the baseline, is shown as a related vote, not scored.",
    "Reject slogans and section headings, statements about past votes, text dating from earlier races that the 2024 vote can't test, and quotes our archive can't show.",
    "Reject later duplicates of the same quote.",
]
RELATED = "Related vote, not scored: show the vote on the member's page with this note, but don't count it as kept or broken."
RETESTED = "Edit applied: re-tested against the Rescissions Act of 2025 (H.R. 4), a direct spending-cut vote; H.R.1 stays as a related vote, not scored."
RESCIND = "Re-test with the Rescissions Act of 2025 (H.R. 4), a direct spending-cut vote; keep H.R.1 as a related vote, not scored."

A, E, R = "Approve", "Edit", "Reject"
D = {}
def s(ids, dec, why):
    for i in ids.split():
        D[i] = {"decision": dec, "reason": why}

# Pilot
s("P-001 P-002 P-005 P-010 P-012 P-014", A, "Vote directly tests the commitment.")
s("P-004 P-007", E, RELATED)
s("P-003", A, RETESTED)
s("P-009", E, RELATED)
s("P-008", A, "Edit applied: re-tested against the HALT Fentanyl Act (stricter punishments for drug trafficking) instead of the Laken Riley Act.")
s("P-006", R, "Section heading, not a commitment.")
s("P-011", R, "No vote tests it yet.")
s("P-013", R, "2020 text; no 2025 vote tests separating insurance from employment.")
s("P-015", R, "Describes a past vote, not a promise.")
s("P-016 P-017 P-018 P-019", R, "Our archived copy of the page doesn't show this text; re-add if an earlier snapshot proves it.")
# Round 2
s("R2-001 R2-002 R2-004 R2-007 R2-013 R2-014 R2-016 R2-017 R2-018 R2-019 R2-020 R2-022 R2-026 R2-031", A, "Vote directly tests the commitment.")
s("R2-003 R2-006 R2-015 R2-024", A, RETESTED)
s("R2-005 R2-008 R2-009 R2-010 R2-021 R2-023 R2-027 R2-028 R2-029 R2-030 R2-032 R2-034 R2-036 R2-038 R2-039", E, RELATED)
s("R2-037", A, "Edit applied: dropped the Anti-CBDC vote, which doesn't test this pro-crypto statement; GENIUS and CLARITY kept.")
s("R2-011 R2-025 R2-041", R, "Slogan or section heading, not a commitment.")
s("R2-012", R, "Duplicate: the same quote is drafted as NI-010 with the Born-Alive vote added.")
s("R2-033", R, "The Laken Riley Act doesn't address legal status or asylum processing.")
s("R2-035 R2-042", R, "Too broad for any vote so far to test.")
s("R2-040", R, "No 2025 vote tests expanding Medicare to cover everyone.")
# Round 3
s("R3-002 R3-003 R3-005 R3-007 R3-009 R3-010 R3-012 R3-013 R3-014 R3-015 R3-016 R3-017 R3-020 R3-021 R3-022 R3-031 R3-032 R3-033", A, "Vote directly tests the commitment.")
s("R3-004 R3-008 R3-030", A, RETESTED)
s("R3-001 R3-006 R3-011 R3-019 R3-023 R3-024 R3-025 R3-026 R3-027 R3-028 R3-029", E, RELATED)
s("R3-018", A, "Edit applied: quote replaced with the full sentence from the same page.")
# New issues
s("NI-002 NI-003 NI-004 NI-006 NI-007 NI-008 NI-009 NI-010 NI-011 NI-013 NI-014 NI-015 NI-027 NI-028 NI-029 NI-030 NI-031", A, "Vote directly tests the commitment.")
s("NI-001 NI-005", E, RELATED + " The statement is broader than the bill.")
s("NI-016 NI-017 NI-018 NI-019 NI-020 NI-021 NI-022 NI-023 NI-024 NI-025 NI-026", E, RELATED)
s("NI-032", E, RELATED + " A vote against extending subsidies is not a vote to repeal the ACA.")
s("NI-012", R, "Duplicate of P-014 (same quote, same votes).")
# Round 4
s("R4-001 R4-003 R4-004 R4-005 R4-006 R4-007 R4-008 R4-010 R4-011 R4-012 R4-013 R4-014 R4-015 R4-017 R4-018 R4-019 R4-020 R4-021 R4-022 R4-023 R4-024 R4-025 R4-026 R4-027 R4-028 R4-033 R4-036 R4-037 R4-045 R4-049 R4-050 R4-052 R4-053 R4-055", A, "Vote directly tests the commitment.")
s("R4-009 R4-016", A, RETESTED)
s("R4-002", E, RELATED + " A general belief in crypto's potential, not a policy commitment.")
s("R4-029 R4-030 R4-031 R4-032 R4-034 R4-035 R4-038 R4-039 R4-040 R4-041 R4-042 R4-043 R4-044 R4-046 R4-047 R4-048 R4-051 R4-054 R4-056", E, RELATED)
# Round 5
s("R5-002 R5-006 R5-007 R5-008 R5-009 R5-013 R5-015 R5-017 R5-018 R5-019 R5-020 R5-021 R5-023 R5-024 R5-025 R5-028 R5-032 R5-036 R5-037 R5-038 R5-040", A, "Vote directly tests the commitment.")
s("R5-016 R5-026 R5-027", A, RETESTED)
s("R5-001 R5-003 R5-004 R5-005 R5-010 R5-011 R5-012 R5-022 R5-029 R5-030 R5-031 R5-033 R5-034 R5-035 R5-039 R5-041 R5-042", E, RELATED)
s("R5-014", A, "Edit applied: the note labels the source as a 2022 press release that was still on the campaign site in 2024.")
# Round 6 (Nov 25, 2026): second pass over every archived member with fewer than 3 tested promises
s(" ".join(f"R6-{i:03d}" for i in range(1, 46)), A, "Vote directly tests the commitment.")
# Round 7 (Nov 25, 2026): new votes on Ukraine aid, the SAVE Act, veterans and gun background checks, and Medicaid coverage of gender transition for minors
s(" ".join(f"R7-{i:03d}" for i in range(1, 48) if i not in (7, 45)), A, "Vote directly tests the commitment.")
s("R7-007", E, RELATED + " Her support for Ukraine aid is conditioned on it not being tied to offensive military aid; the Ukraine Support Act included military financing, so a kept-or-broken call would rest on a contested reading.")
s("R7-045", E, RELATED + " The Stop Insider Trading Act was a partial ban (no new stock purchases) bundled with a voter ID requirement, so a vote against it does not clearly break a promise to end congressional stock trading.")

def all_ids():
    ids = []
    for f, pre in (("pilot_round1", "P"), ("round2", "R2"), ("round3", "R3"), ("issues", "NI"), ("round4", "R4"), ("round5", "R5"), ("round6", "R6"), ("round7", "R7")):
        d = json.loads((ROOT / f"data/promises/{f}_drafts.json").read_text())
        ps = d.get("promises") or d.get("drafts")
        ids += [f"{pre}-{i:03d}" for i in range(1, len(ps) + 1)]
    return ids

if __name__ == "__main__":
    ids = all_ids()
    missing = [i for i in ids if i not in D]; extra = [i for i in D if i not in ids]
    assert not missing and not extra, (missing, extra)
    out = {"reviewed_by": "Claude Opus 5.5 (claude-opus-5-5), an AI model made by Anthropic, at CC's request. No human approves, rejects or edits these decisions.", "date": "2026-11-25", "rules": RULES,
           "decisions": {i: D[i] for i in ids}}
    (ROOT / "data/promises/review_decisions.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    c = Counter(v["decision"] for v in D.values()); print(len(ids), dict(c))
