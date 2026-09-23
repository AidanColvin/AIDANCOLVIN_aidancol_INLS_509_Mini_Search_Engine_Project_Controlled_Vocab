# Evaluation report — run 2026-09-23_0804 (after cycle 1 fixes)

Site: https://rx-label-search-aidancolvins-projects.vercel.app/. Site version: main HEAD 928b6b8, deployed by workflow run 35856741406. Browser: Playwright Chromium at 1440x900, plus 390x844 for L01, L12, L24, and L41. Answer key: TEST_PACK.md Section 6. Grader: scripts/grade_test_pack.py (reads only what the browser captured). Generalization lists G01–G06 are in generalization/.

## Grade mapping used

| Answer key | Pack grade | Site grade(s) that count as it | Site's own label |
|---|---|---|---|
| contraindicated | D | E | Avoid combination |
| major | C | D | Consider changing therapy |
| moderate | B | C, B | Monitor closely, Monitor |
| minor | A | A | Minor |

The scoring rules are the same as in the baseline report, with four grader corrections made in cycle 1. Each is logged in LESSONS_LEARNED.md:

- The key's category name counts as naming the category.
- "Three or more drugs" counts drugs, not the ingredients of one combination product.
- A should-not-flag ingredient inside a product whose flag is an expected item is not a false positive.
- Any 2xx HTTP status counts as working (PubMed answers scripted requests with 203).

The grouping denominator is 43 here, against 57 in the baseline, because of the second correction.

## 1. Summary

| Metric | Value |
|---|---|
| Recall, grade D (contraindicated) | 13/13 hits = 100.0% (plus 0 partial) |
| Recall, grade C (major) | 103/103 hits = 100.0% (plus 0 partial) |
| Recall, grade B (moderate) | 68/68 hits = 100.0% (plus 0 partial) |
| Recall, grade A (minor) | 12/12 hits = 100.0% (plus 0 partial) |
| Precision, overall | 197/232 flags backed by the key = 84.9% |
| Precision, grade D | 13/13 = 100.0% |
| Precision, grade C | 100/104 = 96.2% |
| Precision, grade B | 61/66 = 92.4% |
| Precision, grade A | 23/49 = 46.9% |
| False positives on controls L11, L29 (B or above) | 0 |
| False positives, all should_not_flag rules | 0 |
| Totals correct | 33/33 |
| Duplicate, unit, weekly, and combination cases resolved | 22/22 |
| Grouping statements present | 43/43 |
| Flags with a working primary-source link | 232/232 |
| C or D flags with a working drug-specific link | 117/117 |
| Entries the site could not resolve | 0/244 |
| Input focused on load | 41/41 lists |
| Seconds from Enter to results, median / worst | 0.407 / 1.618 |
| Rulebook rows caught and named (row-list pairs) | 58/62 |

## 2. Per-list scorecard

| List | Expected | Hit | Partial | Miss | False pos. | Totals correct | Grouping present | Flags with working link | Not resolved |
|---|---|---|---|---|---|---|---|---|---|
| L01 | 4 | 4 | 0 | 0 | 0 | 1/1 | 2/2 | 6/6 | 0 |
| L02 | 3 | 3 | 0 | 0 | 0 | 0/0 | 1/1 | 7/7 | 0 |
| L03 | 4 | 4 | 0 | 0 | 0 | 0/0 | 2/2 | 6/6 | 0 |
| L04 | 6 | 6 | 0 | 0 | 0 | 0/0 | 1/1 | 5/5 | 0 |
| L05 | 5 | 5 | 0 | 0 | 0 | 2/2 | 2/2 | 3/3 | 0 |
| L06 | 5 | 5 | 0 | 0 | 0 | 1/1 | 2/2 | 2/2 | 0 |
| L07 | 4 | 4 | 0 | 0 | 0 | 1/1 | 0/0 | 7/7 | 0 |
| L08 | 6 | 6 | 0 | 0 | 0 | 0/0 | 0/0 | 6/6 | 0 |
| L09 | 4 | 4 | 0 | 0 | 0 | 0/0 | 3/3 | 6/6 | 0 |
| L10 | 3 | 3 | 0 | 0 | 0 | 2/2 | 1/1 | 3/3 | 0 |
| L11 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 | 0/0 | 0 |
| L12 | 5 | 5 | 0 | 0 | 0 | 5/5 | 1/1 | 7/7 | 0 |
| L13 | 4 | 4 | 0 | 0 | 0 | 1/1 | 2/2 | 3/3 | 0 |
| L14 | 5 | 5 | 0 | 0 | 0 | 1/1 | 2/2 | 3/3 | 0 |
| L15 | 7 | 7 | 0 | 0 | 0 | 1/1 | 3/3 | 6/6 | 0 |
| L16 | 5 | 5 | 0 | 0 | 0 | 0/0 | 1/1 | 5/5 | 0 |
| L17 | 3 | 3 | 0 | 0 | 0 | 1/1 | 3/3 | 3/3 | 0 |
| L18 | 4 | 4 | 0 | 0 | 0 | 0/0 | 2/2 | 7/7 | 0 |
| L19 | 4 | 4 | 0 | 0 | 0 | 0/0 | 1/1 | 10/10 | 0 |
| L20 | 5 | 5 | 0 | 0 | 0 | 0/0 | 0/0 | 7/7 | 0 |
| L21 | 5 | 5 | 0 | 0 | 0 | 0/0 | 0/0 | 9/9 | 0 |
| L22 | 5 | 5 | 0 | 0 | 0 | 0/0 | 1/1 | 6/6 | 0 |
| L23 | 5 | 5 | 0 | 0 | 0 | 2/2 | 3/3 | 3/3 | 0 |
| L24 | 5 | 5 | 0 | 0 | 0 | 4/4 | 1/1 | 10/10 | 0 |
| L25 | 5 | 5 | 0 | 0 | 0 | 0/0 | 1/1 | 6/6 | 0 |
| L26 | 7 | 7 | 0 | 0 | 0 | 0/0 | 1/1 | 7/7 | 0 |
| L27 | 6 | 6 | 0 | 0 | 0 | 0/0 | 0/0 | 6/6 | 0 |
| L28 | 5 | 5 | 0 | 0 | 0 | 0/0 | 0/0 | 7/7 | 0 |
| L29 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 | 0/0 | 0 |
| L30 | 7 | 7 | 0 | 0 | 0 | 0/0 | 0/0 | 6/6 | 0 |
| L31 | 6 | 6 | 0 | 0 | 0 | 2/2 | 2/2 | 4/4 | 0 |
| L32 | 5 | 5 | 0 | 0 | 0 | 0/0 | 0/0 | 5/5 | 0 |
| L33 | 7 | 7 | 0 | 0 | 0 | 0/0 | 0/0 | 7/7 | 0 |
| L34 | 6 | 6 | 0 | 0 | 0 | 0/0 | 1/1 | 10/10 | 0 |
| L35 | 5 | 5 | 0 | 0 | 0 | 3/3 | 2/2 | 8/8 | 0 |
| L36 | 4 | 4 | 0 | 0 | 0 | 0/0 | 1/1 | 3/3 | 0 |
| L37 | 8 | 8 | 0 | 0 | 0 | 1/1 | 1/1 | 8/8 | 0 |
| L38 | 4 | 4 | 0 | 0 | 0 | 1/1 | 0/0 | 5/5 | 0 |
| L39 | 7 | 7 | 0 | 0 | 0 | 0/0 | 0/0 | 9/9 | 0 |
| L40 | 4 | 4 | 0 | 0 | 0 | 1/1 | 0/0 | 6/6 | 0 |
| L41 | 4 | 4 | 0 | 0 | 0 | 3/3 | 0/0 | 5/5 | 0 |


## 3. Every MISS and PARTIAL

| List | Drugs | Expected category, grade | Status | Site showed | Rulebook row | Black-box hypothesis |
|---|---|---|---|---|---|---|


No MISS or PARTIAL remains: all 196 expected items are hits.

## 4. False positives and medically inaccurate statements

**False positives.** None. There is no flag at B or above on L11 or L29, and no should-not-flag entry is reported at B or above.

**Accuracy review.** I read every alert's mechanism and action text against the rulebook row it cites and against the quoted label sentence. I found no medically wrong statement. Four things are worth noting, and none of them is an error:

- The bleeding groups (L05, L09, L33, L41) quote the warfarin label's general "Risk factors for bleeding include … certain concomitant drugs" sentence. It is accurate but not specific to the pair. The rule's own mechanism text carries the specific point (rulebook rows 9, 12, 13).
- The clopidogrel and omeprazole alert (L30) states that the harm is contested and cites COGENT. This matches rulebook row 31's own caveat.
- L19 flags tramadol with ciprofloxacin (grade D, the opioid boxed warning on CYP3A4 inhibitors). The key does not list it. Ciprofloxacin is a moderate CYP3A inhibitor in the FDA table, and the tramadol label's boxed warning covers CYP3A4 inhibitors. So the flag is supported, even though it is not in the key.
- 26 grade A notes are not backed by the key. Most say a dose is "at the labeled maximum". A few say "both labels mention this risk", for label-only groups that no class rule covers. Grade A never counts toward the B-or-above control rule.

## 5. UX findings, ranked by how much they slow or confuse a doctor

1. **Long pages on a phone.** L24 is 9,583 px tall at 390 px wide, and L41 is 5,882 px. Every alert shows its label quote, "Why it happens", "What to do", and sources in full. The grade strip and the first alert are readable at a glance. Everything below is a wall of text. (P3)
2. **Label quotes are sometimes generic** (see section 4). (P4 quality, not a missing link.)
3. **Good: entry.** The input is focused on load (41/41 lists), paste works, Return works, no entry is left unresolved (0/244), and no click is needed.
4. **Good: grade at a glance.** The A–E strip counts every grade. Each card leads with a grade badge and a count statement ("4 drugs: risk of serious bleeding").
5. **Good: speed.** The page settles within the runner's 0.4 s poll after Return (worst 1.6 s). The check starts on paste, so most of the work is done before Return.
6. **Good: totals.** Totals by ingredient sit above the medication cards, with merged entries in bold and the MME total.

## 6. Prioritized fix list (cycle 2)

| Priority | What is wrong | Lists | General fix | How it will be verified |
|---|---|---|---|---|
| P0 | None | — | — | — |
| P1 | None | — | — | — |
| P2 | Rulebook row 19 (metformin plus an AKI cause) is never named | L04 | List metformin in the kidney-injury group when the group fires, with its lactic-acidosis note | RULEBOOK_COVERAGE row 19 is named on L04 |
| P2 | Row 27 statin alerts say "muscle injury" but not "myopathy" | L21, L28, L37 | Name myopathy and rhabdomyolysis in the statin rules' risk text | RULEBOOK_COVERAGE row 27 is named on all 5 lists |
| P3 | Long alert cards on a phone | L24, L41 mobile | Show grade, drugs, count statement, "What to do", and the label links. Put the quote, "Why it happens", and the included pair notes behind a "Why, and the label sentence" toggle. | Page height at 390 px drops; no alert text is lost from the DOM |
