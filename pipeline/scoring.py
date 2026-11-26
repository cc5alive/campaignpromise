"""Which votes score each approved promise, and which position keeps it.

Decided by Claude Opus 5.5 (claude-opus-5-5) at CC's request. Every call is listed here so it can be checked.
A scored vote is one that directly tests the promise. A related vote bears on it but is not scored.
"""

# Position that keeps the promise, by bill family. Applied per promise below.
YEA, NAY = "Yea", "Nay"

LAKEN_RILEY = {"house-2025-006", "house-2025-023", "senate-1-00007"}
HR1 = {"house-2025-145", "house-2025-190", "senate-1-00372"}
RESCISSIONS = {"house-2025-168", "senate-1-00411"}

# Promises that only say "secure the border" (or similar). The Laken Riley Act is about detaining
# immigrants charged with crimes, not border security, so for these it is a related vote.
LAKEN_RILEY_RELATED = {
    "P-001", "R2-002", "R2-004", "R2-013", "R2-017", "R2-018", "R2-019", "R2-020",
    "R3-033", "R4-001", "R4-005", "R4-014", "R4-021", "R4-024", "R5-017", "R5-024",
}

# Promises where keeping it means voting against the bill (Democratic promises opposed to what the bill did,
# and Republican promises H.R.1 cut against).
AGAINST = {
    # H.R.1 cut Medicaid, extended the 2017 tax cuts and funded ICE: a no vote keeps these.
    "P-010", "P-012", "R2-026", "R2-031", "R4-033", "R4-049", "R5-006", "R2-001",
    # Round 6: repeal the 2017 tax cuts for the wealthy; protect or expand Medicaid.
    "R6-005", "R6-008", "R6-011", "R6-019", "R6-034", "R6-037", "R6-041",
}

NOTES = {
    "R2-001": "H.R.1 cut projected Medicaid spending, a central and widely reported provision, so a no vote keeps this promise.",
    "P-012": "The Laken Riley Act expanded mandatory ICE detention and H.R.1 added about $75 billion for ICE, so a no vote keeps this promise.",
    "R4-045": "H.R.1 funded new Border Patrol agents, a central provision. A no vote counts against this promise even if the member opposed the bill for other reasons.",
    "R5-036": "H.R.1 funded Border Patrol personnel and border infrastructure, a central provision. A no vote counts against this promise even if the member opposed the bill for other reasons.",
    "R6-013": "H.R.1 extended the 2017 tax cuts, a central provision. A no vote counts against this promise even if the member opposed the bill for other reasons, such as its cap on the state and local tax deduction.",
    "R6-036": "The GENIUS Act and CLARITY Act set the first federal rules for stablecoins and digital assets. A no vote counts against this statement of support for the digital asset industry.",
    "P-014": "H.R.1 barred Medicaid payments to Planned Parenthood for one year, a central provision. A no vote counts against this promise.",
}


RULES = [
    "Score a promise only with votes that directly test it; show other relevant votes as related, not scored.",
    "The Laken Riley Act (detention of immigrants charged with crimes) scores promises about immigration enforcement, deportation or ending illegal immigration. For promises that only say 'secure the border', it is a related vote.",
    "A promise is aligned when every scored vote matches it, not aligned when every scored vote goes against it, and mixed otherwise. 'Present' and 'Not voting' are not counted.",
    "A vote counts toward at most one promise per member, so a single bill cannot stack up a member's score.",
    "A member's score (promises aligned out of promises tested) is shown only once at least 3 of their promises have been tested.",
]


def plan(p, used=None):
    """Return (scored: {vote_id: keeping position}, related: [vote_id], elsewhere: [vote_id]).

    used: vote ids already scored on this member's earlier promises; they are not scored again."""
    scored, related, elsewhere = {}, [], []
    used = used if used is not None else set()
    for v in p["votes"]:
        vid = v["id"]
        if vid in used and not (vid in HR1 and p["issue"] == "Federal spending"):
            elsewhere.append(vid)
        elif vid in RESCISSIONS:
            scored[vid] = YEA
        elif vid in HR1 and p["issue"] == "Federal spending":
            related.append(vid)  # net effect on spending depends on the baseline
        elif vid in LAKEN_RILEY and p["id"] in LAKEN_RILEY_RELATED:
            related.append(vid)
        else:
            scored[vid] = NAY if p["id"] in AGAINST else YEA
    used.update(scored)
    return scored, related, elsewhere


def outcome(position, keep):
    pos = {"Aye": "Yea", "Yes": "Yea", "No": "Nay"}.get(position, position)
    if pos not in ("Yea", "Nay"):
        return "not counted"  # Present, Not Voting
    return "aligned" if pos == keep else "not aligned"
