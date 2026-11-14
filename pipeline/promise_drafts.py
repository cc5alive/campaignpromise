"""Pilot round 1: AI-drafted promise candidates. Every quote must appear verbatim in its source."""
import json, hashlib, re
from bs4 import BeautifulSoup
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def man(k): return json.loads((ROOT/f"archive/2024/{k}/manifest.json").read_text())
def page(k, orig_suffix):
    for p in man(k)["pages"]:
        if p.get("original","").rstrip("/").endswith(orig_suffix.rstrip("/")) and "error" not in p: return p
    raise KeyError((k, orig_suffix))

D = [
 # member, source page suffix, quote, kind, issue, test votes, note
 ("curtis","johncurtis.org/issues/","In the Senate, John will work to secure the border and fix our broken immigration system.","Pledge","Immigration",["senate-1-00007"],""),
 ("curtis","johncurtis.org/issues/","John has been proud to support these industries in Congress, and will continue to work hard to make sure those in Silicon Slopes and throughout Utah have the certainty from the government they need.","Pledge","Crypto",["senate-1-00318"],"\"These industries\" refers to digital assets and crypto, named in the sentences before it."),
 ("curtis","johncurtis.org/issues/","John is a pro-life, pro-Second Amendment, fiscal conservative who is committed to cutting Biden’s reckless spending.","Stated position","Federal spending",["senate-1-00372"],"Judgment needed: whether the 2025 reconciliation bill counts as cutting spending depends on which baseline you use."),
 ("lawler","lawlerforcongress.com/issues/","Never supporting any cuts to Social Security, Medicare, or veterans services that violate the sacred promises made to the hard working men and women who built this country, nor those who wore the uniform in defense of our freedoms.","Pledge","Social Security & Medicare",["house-2025-145","house-2025-190"],"Judgment needed: the 2025 reconciliation bill cut Medicaid, which this pledge does not name."),
 ("lawler","lawlerforcongress.com/issues/","Introducing both the “Middle Class Tax Relief Act” and “SALT Marriage Penalty Elimination Act” in an ongoing effort to provide tax relief to middle-class Hudson Valley families who have been negatively impacted by the SALT cap","Stated position","Taxes (SALT)",["house-2025-145","house-2025-190"],"The 2025 reconciliation bill raised the SALT deduction cap."),
 ("lawler","lawlerforcongress.com/issues/","Secure Our Border and Support Immigration Reform","Stated position","Immigration",["house-2025-006","house-2025-023"],"Section heading on the issues page."),
 ("mgp","marieforcongress.com/issues/","She will protect the benefits that seniors in Southwest Washington are counting on for their retirement and that they’ve paid into their whole working lives.","Pledge","Social Security & Medicare",["house-2025-145","house-2025-190"],"Judgment needed: which provisions of the reconciliation bill affect these benefits."),
 ("mgp","marieforcongress.com/issues/","Marie believes in fighting the drug crisis through increased border security, stricter punishments for sale and possession, expanded access to treatment and rehab, and better job opportunities.","Stated position","Immigration",["house-2025-006","house-2025-023"],""),
 ("mgp","marieforcongress.com/issues/","She supports re-introducing and expanding the Child Tax Credit","Stated position","Taxes (Child Tax Credit)",["house-2025-145","house-2025-190"],"Likely mixed: the reconciliation bill raised the credit, and she voted no on the bill as a whole."),
 ("torres","torres.nyc/issues/access-to-opportunity-for-all","Ritchie is committed to increased funding for our safety-net hospitals and facilities,like NYC’s Health + Hospitals, which serve Medicaid beneficiaries, undocumented individuals, and the uninsured.","Pledge","Medicaid",["house-2025-145","house-2025-190"],"Quote keeps the source's missing space after the comma."),
 ("torres","torres.nyc/issues/housing","Ritchie believes in assisting more families by protecting and expanding Section 8.","Stated position","Housing",[],"No pilot vote tests this yet."),
 ("aoc","ocasiocortez.com/issues","It is past time to make undocumented individuals full members of the country they call their home and abolish ICE.","Stated position","Immigration",["house-2025-006","house-2025-023","house-2025-145","house-2025-190"],"The reconciliation bill added ICE funding."),
 ("aoc","ocasiocortez.com/issues","With over 30 million unemployed, and in the face of a global pandemic, we must finally separate health insurance from unemployment and expand Medicare.","Stated position","Health care",["house-2025-145","house-2025-190"],"Text dates from 2020 but was still on the site on Nov 5, 2024."),
 ("massie","thomasmassie.com/","I will vote against government funding of abortion services and will vote to defund Planned Parenthood.","Pledge","Abortion funding",["house-2025-145","house-2025-190"],"The reconciliation bill included a one-year Medicaid funding ban for Planned Parenthood; he voted no on the bill as a whole (bundled vote)."),
 ("massie","thomasmassie.com/","I support President Trump’s efforts to stop illegal immigration and voted to fund the wall for the full amount requested by the President.","Stated position","Immigration",["house-2025-006","house-2025-023","house-2025-145","house-2025-190"],"The reconciliation bill included border wall funding."),
]
out=[]; problems=[]
for i,(k,suf,q,kind,issue,votes,note) in enumerate(D,1):
    p=page(k,suf); html=(ROOT/p["file"]).read_bytes()
    s=BeautifulSoup(html,"html.parser")
    for t in s(["script","style","noscript"]): t.decompose()
    full=re.sub(r"\s+"," ",s.get_text(" "))
    ok = re.sub(r"\s+"," ",q) in full
    if not ok: problems.append((k,q[:60]))
    out.append({"id":f"P{i:03d}","member":k,"quote":q,"kind":kind,"issue":issue,"source":{"original":p["original"],"snapshot":p["timestamp"],"wayback":p["wayback"],"file":p["file"],"sha256_html":p["sha256_html"]},"quote_verified_in_source":ok,"suggested_test_votes":votes,"note":note,"status":"draft","drafted_by":"Claude (AI)","reviewed_by":None})
# Gallego: archived Nov 1, 2024 snapshot lacks the issue text; quoted by Ballotpedia from his 2024 campaign site.
G=[("He will continue to stand up to any attempt to privatize or cut Medicare on behalf of the 1.45 million Arizonans who rely on it—and he will fight every day to expand Medicare benefits.","Pledge","Social Security & Medicare",["senate-1-00372"]),
   ("He is an unwavering supporter of Medicaid expansion, and he stood up to Republican attempts to gut Arizona’s Medicaid program and dismantle the Affordable Care Act time and again.","Stated position","Medicaid",["senate-1-00372"]),
   ("We need smart ways to keep our border secure, allow for a prosperous cross-border economy, reform a broken immigration system, and stop the flow of fentanyl into our communities.","Stated position","Immigration",["senate-1-00007"]),
   ("It is inexcusable that billionaires and corporations continuously exploit our tax code — Ruben is committed to making sure they pay their fair share","Pledge","Taxes",["senate-1-00372"])]
for q,kind,issue,votes in G:
    out.append({"id":f"P{len(out)+1:03d}","member":"gallego","quote":q,"kind":kind,"issue":issue,"source":{"original":"https://gallegoforarizona.com/issues/","quoted_by":"https://ballotpedia.org/Ruben_Gallego (Campaign themes, 2024)","wayback":None},"quote_verified_in_source":"ballotpedia","suggested_test_votes":votes,"note":"Our Nov 1, 2024 Wayback copy of the issues page does not show this text (content likely loaded by script). Needs an earlier snapshot before approval.","status":"draft","drafted_by":"Claude (AI)","reviewed_by":None})
gaps={"moreno":"Archived 2024 campaign homepage has no issue statements and no issues page was archived. Next: debate transcripts and ads.",
      "warren":"Archived 2024 campaign homepage has no issue statements; the /plans page dates from her 2020 presidential race. Next: 2024 debate transcripts.",
      "salazar":"Archived 2024 campaign homepage has only a biography. Next: issues pages under other paths, debates."}
json.dump({"round":1,"generated":"2026-11-14","promises":out,"gaps":gaps},open(ROOT/"data/promises/pilot_round1_drafts.json","w"),indent=1,ensure_ascii=False)
print(len(out),"drafts; problems:",problems)
