# Evaluation report — run 2026-09-23_0648 (baseline)

Site: https://rx-label-search-aidancolvins-projects.vercel.app/ · Site version: main HEAD 6d02dc3 (deployed by workflow run 35844387875 at 2026-09-23T09:41Z; the site shows no build hash) · Browser: Playwright Chromium 1440x900, plus 390x844 for L01, L12, L24, L41 · Answer key: TEST_PACK.md Section 6 · Grader: scripts/grade_test_pack.py, which reads only what the browser captured.

## Grade mapping used

| Answer key | Pack grade | Site grade(s) that count as it | Site's own label |
|---|---|---|---|
| contraindicated | D | E | Avoid combination |
| major | C | D | Consider changing therapy |
| moderate | B | C, B | Monitor closely, Monitor |
| minor | A | A | Minor |

The site's scale is A–E, and it can be mapped. Site C and B both count as pack B because the site's own legend lines both up with Lexicomp C.

Scoring rules as applied (TEST_PACK.md Section 4):
- **HIT**: same drugs or a superset, an equivalent category (the key's category words appear in the alert text), and the same or a higher grade.
- **PARTIAL**: right drugs and category but one grade low, or right drugs and grade but the category not named.
- **MISS**: anything else, including flagging only a subset of a 3+ drug group.
- **Dosing-frequency and combination-parsing items**: scored on the medication card (a weekly amount and no daily total; every component shown).

## 1. Summary

| Metric | Value |
|---|---|
| Recall, grade D (contraindicated) | 0/13 hits = 0.0% (plus 0 partial) |
| Recall, grade C (major) | 0/103 hits = 0.0% (plus 0 partial) |
| Recall, grade B (moderate) | 0/68 hits = 0.0% (plus 0 partial) |
| Recall, grade A (minor) | 0/12 hits = 0.0% (plus 0 partial) |
| Precision, overall | 0/0 flags backed by the key = n/a |
| Precision, grade D | 0/0 = n/a |
| Precision, grade C | 0/0 = n/a |
| Precision, grade B | 0/0 = n/a |
| Precision, grade A | 0/0 = n/a |
| False positives on controls L11, L29 (B or above) | 0 |
| False positives, all should_not_flag rules | 0 |
| Totals correct | 0/33 |
| Duplicate, unit, weekly, and combination cases resolved | 0/22 |
| Grouping statements present | 0/57 |
| Flags with a working primary-source link | 0/0 |
| C or D flags with a working drug-specific link | 0/0 |
| Entries the site could not resolve | 244/244 |
| Input focused on load | 41/41 lists |
| Seconds from Enter to results, median / worst | 3.243 / 4.467 |
| Rulebook rows caught and named (row-list pairs) | 0/62 |

## 2. Per-list scorecard

| List | Expected | Hit | Partial | Miss | False pos. | Totals correct | Grouping present | Flags with working link | Not resolved |
|---|---|---|---|---|---|---|---|---|---|
| L01 | 4 | 0 | 0 | 4 | 0 | 0/1 | 0/2 | 0/0 | 5 |
| L02 | 3 | 0 | 0 | 3 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L03 | 4 | 0 | 0 | 4 | 0 | 0/0 | 0/2 | 0/0 | 6 |
| L04 | 6 | 0 | 0 | 6 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L05 | 5 | 0 | 0 | 5 | 0 | 0/2 | 0/3 | 0/0 | 7 |
| L06 | 5 | 0 | 0 | 5 | 0 | 0/1 | 0/2 | 0/0 | 6 |
| L07 | 4 | 0 | 0 | 4 | 0 | 0/1 | 0/0 | 0/0 | 6 |
| L08 | 6 | 0 | 0 | 6 | 0 | 0/0 | 0/0 | 0/0 | 6 |
| L09 | 4 | 0 | 0 | 4 | 0 | 0/0 | 0/3 | 0/0 | 6 |
| L10 | 3 | 0 | 0 | 3 | 0 | 0/2 | 0/1 | 0/0 | 6 |
| L11 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 | 0/0 | 5 |
| L12 | 5 | 0 | 0 | 5 | 0 | 0/5 | 0/1 | 0/0 | 6 |
| L13 | 4 | 0 | 0 | 4 | 0 | 0/1 | 0/2 | 0/0 | 6 |
| L14 | 5 | 0 | 0 | 5 | 0 | 0/1 | 0/2 | 0/0 | 6 |
| L15 | 7 | 0 | 0 | 7 | 0 | 0/1 | 0/3 | 0/0 | 6 |
| L16 | 5 | 0 | 0 | 5 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L17 | 3 | 0 | 0 | 3 | 0 | 0/1 | 0/3 | 0/0 | 6 |
| L18 | 4 | 0 | 0 | 4 | 0 | 0/0 | 0/2 | 0/0 | 6 |
| L19 | 4 | 0 | 0 | 4 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L20 | 5 | 0 | 0 | 5 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L21 | 5 | 0 | 0 | 5 | 0 | 0/0 | 0/0 | 0/0 | 6 |
| L22 | 5 | 0 | 0 | 5 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L23 | 5 | 0 | 0 | 5 | 0 | 0/2 | 0/4 | 0/0 | 6 |
| L24 | 5 | 0 | 0 | 5 | 0 | 0/4 | 0/1 | 0/0 | 6 |
| L25 | 5 | 0 | 0 | 5 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L26 | 7 | 0 | 0 | 7 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L27 | 6 | 0 | 0 | 6 | 0 | 0/0 | 0/2 | 0/0 | 6 |
| L28 | 5 | 0 | 0 | 5 | 0 | 0/0 | 0/5 | 0/0 | 6 |
| L29 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 | 0/0 | 6 |
| L30 | 7 | 0 | 0 | 7 | 0 | 0/0 | 0/0 | 0/0 | 6 |
| L31 | 6 | 0 | 0 | 6 | 0 | 0/2 | 0/3 | 0/0 | 6 |
| L32 | 5 | 0 | 0 | 5 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L33 | 7 | 0 | 0 | 7 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L34 | 6 | 0 | 0 | 6 | 0 | 0/0 | 0/1 | 0/0 | 6 |
| L35 | 5 | 0 | 0 | 5 | 0 | 0/3 | 0/2 | 0/0 | 6 |
| L36 | 4 | 0 | 0 | 4 | 0 | 0/0 | 0/2 | 0/0 | 6 |
| L37 | 8 | 0 | 0 | 8 | 0 | 0/1 | 0/1 | 0/0 | 6 |
| L38 | 4 | 0 | 0 | 4 | 0 | 0/1 | 0/0 | 0/0 | 6 |
| L39 | 7 | 0 | 0 | 7 | 0 | 0/0 | 0/0 | 0/0 | 6 |
| L40 | 4 | 0 | 0 | 4 | 0 | 0/1 | 0/0 | 0/0 | 5 |
| L41 | 4 | 0 | 0 | 4 | 0 | 0/3 | 0/0 | 0/0 | 6 |


## 3. Every MISS and PARTIAL

| List | Drugs | Expected category, grade | Status | Site showed | Rulebook row | Black-box hypothesis |
|---|---|---|---|---|---|---|
| L01 | olanzapine, olanzapine | duplicate entry, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L01 | alprazolam, zolpidem, olanzapine | CNS depression, C (major) | MISS | not flagged | — | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L01 | amphetamine/dextroamphetamine | dose ceiling, B (moderate) | MISS | not flagged | — | parser: 1 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L01 | amphetamine/dextroamphetamine, alprazolam, olanzapine | opposing pharmacology, A (minor) | MISS | not flagged | — | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L02 | sertraline, tramadol, sumatriptan, cyclobenzaprine, ondansetron | serotonin syndrome, C (major) | MISS | not flagged | 7 | parser: 5 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L02 | tramadol, sertraline | seizure threshold, B (moderate) | MISS | not flagged | 7 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L02 | ondansetron, tramadol | efficacy loss, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L03 | citalopram, haloperidol, azithromycin, fluconazole | QT prolongation, C (major) | MISS | not flagged | 23 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L03 | citalopram, fluconazole | CYP inhibition, C (major) | MISS | not flagged | 23 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L03 | haloperidol, fluconazole | CYP inhibition, B (moderate) | MISS | not flagged | 23 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L03 | furosemide, citalopram, haloperidol, azithromycin, fluconazole | electrolyte, B (moderate) | MISS | not flagged | 23 | parser: 5 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L04 | lithium, lisinopril | lithium toxicity, C (major) | MISS | not flagged | 16 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L04 | lithium, hydrochlorothiazide | lithium toxicity, C (major) | MISS | not flagged | 16 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L04 | lithium, ibuprofen | lithium toxicity, C (major) | MISS | not flagged | 16 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L04 | lisinopril, hydrochlorothiazide, ibuprofen | nephrotoxicity, C (major) | MISS | not flagged | 14, 16 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L04 | metformin, topiramate | metabolic acidosis, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L04 | topiramate, hydrochlorothiazide | electrolyte, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L05 | warfarin, sulfamethoxazole/trimethoprim | bleeding, C (major) | MISS | not flagged | 10 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L05 | warfarin, amiodarone | bleeding, C (major) | MISS | not flagged | 10 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L05 | warfarin, aspirin, clopidogrel | bleeding, C (major) | MISS | not flagged | 9, 12, 13 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L05 | escitalopram, warfarin, aspirin, clopidogrel | bleeding, B (moderate) | MISS | not flagged | 9, 12, 13 | parser: 5 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L05 | escitalopram, amiodarone | QT prolongation, C (major) | MISS | not flagged | 23 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L06 | oxycodone ER, oxycodone IR | duplicate entry, C (major) | MISS | not flagged | 1, 2 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L06 | oxycodone, clonazepam | respiratory depression, C (major) | MISS | not flagged | 1 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L06 | oxycodone, gabapentin | respiratory depression, C (major) | MISS | not flagged | 2 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L06 | oxycodone, carisoprodol, clonazepam | CNS depression, C (major) | MISS | not flagged | 1 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L06 | hydroxyzine, oxycodone, clonazepam | CNS depression, B (moderate) | MISS | not flagged | 1 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L07 | phenelzine, bupropion | hypertensive crisis, D (contraindicated) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L07 | phenelzine, meperidine | serotonin syndrome, D (contraindicated) | MISS | not flagged | 7 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L07 | phenelzine, methylphenidate | hypertensive crisis, D (contraindicated) | MISS | not flagged | 24 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L07 | phenelzine, amlodipine | hypotension, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L08 | clozapine, carbamazepine | myelosuppression, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L08 | clozapine, fluvoxamine | CYP inhibition, C (major) | MISS | not flagged | 5 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L08 | clozapine, ciprofloxacin | CYP inhibition, C (major) | MISS | not flagged | 5 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L08 | clozapine, lorazepam | respiratory depression, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L08 | carbamazepine, divalproex | CYP induction, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L08 | clozapine, ciprofloxacin | QT prolongation, B (moderate) | MISS | not flagged | 5 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L09 | fluoxetine, paroxetine | duplicate therapy, C (major) | MISS | not flagged | 7, 13 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L09 | fluoxetine, paroxetine, tamoxifen | efficacy loss, C (major) | MISS | not flagged | 7, 13 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L09 | fluoxetine, paroxetine, metoprolol | CYP inhibition, B (moderate) | MISS | not flagged | 7, 13 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L09 | fluoxetine, paroxetine, naproxen | bleeding, B (moderate) | MISS | not flagged | 7, 13 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L10 | simvastatin, clarithromycin | myopathy/rhabdomyolysis, D (contraindicated) | MISS | not flagged | 27 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L10 | spironolactone, enalapril, potassium chloride | hyperkalemia, C (major) | MISS | not flagged | 15 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L10 | methotrexate | dosing frequency, C (major) | MISS | card does not show a weekly amount without a daily total | — | parser: 1 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L12 | olanzapine/fluoxetine, fluoxetine | duplicate therapy, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L12 | hydrocodone/acetaminophen, acetaminophen | dose ceiling, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L12 | alprazolam, alprazolam ER | duplicate entry, B (moderate) | MISS | not flagged | 1 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L12 | hydrocodone, alprazolam, olanzapine | respiratory depression, C (major) | MISS | not flagged | 1 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L12 | fluoxetine, hydrocodone | CYP inhibition, B (moderate) | MISS | not flagged | — | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L13 | linezolid, venlafaxine | serotonin syndrome, D (contraindicated) | MISS | not flagged | 7 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L13 | linezolid, buspirone, fentanyl, metoclopramide | serotonin syndrome, C (major) | MISS | not flagged | 7 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L13 | fentanyl, methocarbamol | respiratory depression, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L13 | metoclopramide, venlafaxine, buspirone | serotonin syndrome, B (moderate) | MISS | not flagged | 7 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L14 | fentanyl, diazepam, temazepam | respiratory depression, C (major) | MISS | not flagged | 1 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L14 | diazepam, temazepam | duplicate therapy, C (major) | MISS | not flagged | 1 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L14 | fentanyl, pregabalin | respiratory depression, C (major) | MISS | not flagged | 2 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L14 | fentanyl, promethazine | respiratory depression, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L14 | tizanidine, fentanyl, diazepam, temazepam, pregabalin, promethazine | CNS depression, B (moderate) | MISS | not flagged | 1, 2 | parser: 6 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L15 | metoprolol, diltiazem | bradycardia/AV block, C (major) | MISS | not flagged | 20 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L15 | digoxin, amiodarone | digoxin toxicity, C (major) | MISS | not flagged | 18 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L15 | digoxin, diltiazem | digoxin toxicity, B (moderate) | MISS | not flagged | 18 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L15 | digoxin, metoprolol, diltiazem, amiodarone | bradycardia/AV block, C (major) | MISS | not flagged | 18, 20 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L15 | donepezil, metoprolol, diltiazem, digoxin | bradycardia/AV block, B (moderate) | MISS | not flagged | 18, 20 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L15 | furosemide, digoxin, amiodarone | electrolyte, B (moderate) | MISS | not flagged | 18 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L15 | amiodarone, metoprolol | CYP inhibition, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L16 | sildenafil, nitroglycerin | hypotension, D (contraindicated) | MISS | not flagged | 21, 22 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L16 | sildenafil, isosorbide mononitrate | hypotension, D (contraindicated) | MISS | not flagged | 21, 22 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L16 | sildenafil, tamsulosin | hypotension, B (moderate) | MISS | not flagged | 22 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L16 | clonidine, carvedilol | bradycardia/AV block, C (major) | MISS | not flagged | 22, 25 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L16 | carvedilol, tamsulosin, clonidine, isosorbide mononitrate | hypotension, B (moderate) | MISS | not flagged | 22, 25 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L17 | trimethoprim, spironolactone, losartan, potassium chloride | hyperkalemia, C (major) | MISS | not flagged | 14, 15 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L17 | losartan, spironolactone, celecoxib | nephrotoxicity, C (major) | MISS | not flagged | 14, 15 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L17 | empagliflozin, spironolactone, celecoxib, losartan | nephrotoxicity, B (moderate) | MISS | not flagged | 14, 15 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L18 | amitriptyline, oxybutynin, hydroxyzine, benztropine, paroxetine | anticholinergic burden, C (major) | MISS | not flagged | 6 | parser: 5 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L18 | donepezil, amitriptyline, oxybutynin, hydroxyzine, benztropine | therapeutic antagonism, C (major) | MISS | not flagged | 6 | parser: 5 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L18 | paroxetine, amitriptyline | CYP inhibition, C (major) | MISS | not flagged | 6 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L18 | amitriptyline, hydroxyzine | QT prolongation, B (moderate) | MISS | not flagged | 6 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L19 | bupropion, tramadol, theophylline, ciprofloxacin, quetiapine | seizure threshold, C (major) | MISS | not flagged | 8, 23, 35 | parser: 5 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L19 | theophylline, ciprofloxacin | CYP inhibition, C (major) | MISS | not flagged | 8 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L19 | ciprofloxacin, quetiapine | QT prolongation, B (moderate) | MISS | not flagged | 8, 23 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L19 | bupropion, tramadol | CYP inhibition, B (moderate) | MISS | not flagged | 8, 35 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L20 | rifampin, rivaroxaban | efficacy loss, C (major) | MISS | not flagged | 33 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L20 | rifampin, norgestimate/ethinyl estradiol | efficacy loss, C (major) | MISS | not flagged | 33 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L20 | rifampin, tacrolimus | efficacy loss, C (major) | MISS | not flagged | 33 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L20 | rifampin, lurasidone | CYP induction, D (contraindicated) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L20 | rifampin, methadone | efficacy loss, C (major) | MISS | not flagged | 33 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L21 | ketoconazole, triazolam | CYP inhibition, D (contraindicated) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L21 | ketoconazole, alprazolam | CYP inhibition, D (contraindicated) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L21 | ketoconazole, apixaban | bleeding, C (major) | MISS | not flagged | 11 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L21 | ketoconazole, atorvastatin | myopathy/rhabdomyolysis, C (major) | MISS | not flagged | 27 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L21 | ketoconazole, amlodipine | CYP inhibition, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L22 | tacrolimus, fluconazole | CYP inhibition, C (major) | MISS | not flagged | 34 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L22 | tacrolimus, fluconazole, ondansetron | QT prolongation, C (major) | MISS | not flagged | 23, 34 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L22 | mycophenolate mofetil, omeprazole | absorption/timing, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L22 | simvastatin, fluconazole | myopathy/rhabdomyolysis, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L22 | tacrolimus, omeprazole | CYP inhibition, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L23 | glipizide, insulin glargine, semaglutide | hypoglycemia, C (major) | MISS | not flagged | — | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L23 | glipizide, sulfamethoxazole/trimethoprim | hypoglycemia, C (major) | MISS | not flagged | 26 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L23 | levofloxacin, glipizide, insulin glargine | hypoglycemia, C (major) | MISS | not flagged | — | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L23 | propranolol, glipizide, insulin glargine | hypoglycemia, B (moderate) | MISS | not flagged | 26 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L23 | semaglutide, glipizide | absorption/timing, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L24 | hydrocodone/acetaminophen, oxycodone/acetaminophen | duplicate therapy, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L24 | acetaminophen, acetaminophen | duplicate entry, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L24 | zolpidem, eszopiclone | duplicate therapy, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L24 | meloxicam, naproxen sodium | duplicate therapy, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L24 | hydrocodone, oxycodone, zolpidem, eszopiclone | CNS depression, C (major) | MISS | not flagged | — | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L25 | methadone, quetiapine, ondansetron, levofloxacin, fluconazole | QT prolongation, C (major) | MISS | not flagged | 23 | parser: 5 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L25 | methadone, fluconazole | CYP inhibition, C (major) | MISS | not flagged | 23 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L25 | methadone, venlafaxine | serotonin syndrome, B (moderate) | MISS | not flagged | 7 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L25 | methadone, quetiapine | respiratory depression, C (major) | MISS | not flagged | 23 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L25 | quetiapine, fluconazole | CYP inhibition, B (moderate) | MISS | not flagged | 23 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L26 | divalproex, lamotrigine | CYP inhibition, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L26 | carbamazepine, lamotrigine | CYP induction, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L26 | carbamazepine, divalproex | CYP induction, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L26 | divalproex, topiramate | hyperammonemia, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L26 | divalproex, aspirin | bleeding, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L26 | carbamazepine, clonazepam | CYP induction, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L26 | divalproex, lamotrigine, topiramate, carbamazepine, clonazepam | CNS depression, B (moderate) | MISS | not flagged | — | parser: 5 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L27 | carbidopa/levodopa, metoclopramide | therapeutic antagonism, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L27 | carbidopa/levodopa, haloperidol | therapeutic antagonism, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L27 | rasagiline, meperidine | serotonin syndrome, D (contraindicated) | MISS | not flagged | 7 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L27 | rasagiline, escitalopram | serotonin syndrome, B (moderate) | MISS | not flagged | 7 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L27 | metoclopramide, haloperidol | duplicate therapy, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L27 | haloperidol, escitalopram | QT prolongation, B (moderate) | MISS | not flagged | 23 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L28 | darunavir/cobicistat, atorvastatin | myopathy/rhabdomyolysis, C (major) | MISS | not flagged | 27 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L28 | darunavir/cobicistat, alprazolam | CYP inhibition, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L28 | darunavir/cobicistat, fluticasone propionate | adrenal suppression, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L28 | darunavir/cobicistat, sildenafil | hypotension, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L28 | darunavir/cobicistat, tenofovir disoproxil fumarate | nephrotoxicity, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L30 | levothyroxine, calcium carbonate | absorption/timing, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L30 | levothyroxine, ferrous sulfate | absorption/timing, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L30 | ciprofloxacin, calcium carbonate | absorption/timing, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L30 | ciprofloxacin, ferrous sulfate | absorption/timing, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L30 | clopidogrel, omeprazole | efficacy loss, C (major) | MISS | not flagged | 31 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L30 | ferrous sulfate, omeprazole | absorption/timing, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L30 | levothyroxine, omeprazole | absorption/timing, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L31 | vancomycin, gentamicin | nephrotoxicity, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L31 | vancomycin, piperacillin/tazobactam | nephrotoxicity, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L31 | gentamicin, furosemide | ototoxicity, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L31 | ketorolac, lisinopril, furosemide | nephrotoxicity, C (major) | MISS | not flagged | 14 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L31 | ketorolac, gentamicin, vancomycin | nephrotoxicity, C (major) | MISS | not flagged | — | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L31 | ketorolac, lisinopril | hyperkalemia, B (moderate) | MISS | not flagged | 14 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L32 | methotrexate, sulfamethoxazole/trimethoprim | myelosuppression, C (major) | MISS | not flagged | 30 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L32 | azathioprine, allopurinol | myelosuppression, C (major) | MISS | not flagged | 29 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L32 | methotrexate, ibuprofen | nephrotoxicity, B (moderate) | MISS | not flagged | 30 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L32 | methotrexate, azathioprine | myelosuppression, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L32 | methotrexate | dosing frequency, C (major) | MISS | card does not show a weekly amount without a daily total | 30 | parser: 1 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L33 | phenytoin, norgestimate/ethinyl estradiol | efficacy loss, C (major) | MISS | not flagged | 33 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L33 | phenytoin, fluoxetine | CYP inhibition, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L33 | phenytoin, fluconazole | CYP inhibition, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L33 | phenytoin, warfarin | bleeding, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L33 | warfarin, fluconazole | bleeding, C (major) | MISS | not flagged | 10 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L33 | warfarin, fluoxetine | bleeding, B (moderate) | MISS | not flagged | 13 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L33 | phenytoin, atorvastatin | efficacy loss, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L34 | guanfacine, clonidine | duplicate therapy, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L34 | paroxetine, atomoxetine | CYP inhibition, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L34 | lisdexamfetamine, atomoxetine | duplicate therapy, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L34 | lisdexamfetamine, paroxetine | serotonin syndrome, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L34 | quetiapine, guanfacine, clonidine | hypotension, B (moderate) | MISS | not flagged | — | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L34 | lisdexamfetamine, quetiapine | opposing pharmacology, A (minor) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L35 | sumatriptan, rizatriptan | duplicate therapy, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L35 | rizatriptan, propranolol | CYP inhibition, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L35 | sumatriptan, rizatriptan, amitriptyline | serotonin syndrome, B (moderate) | MISS | not flagged | — | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L35 | butalbital, amitriptyline, topiramate | CNS depression, B (moderate) | MISS | not flagged | — | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L35 | butalbital/acetaminophen/caffeine | combination parsing, B (moderate) | MISS | components shown: ['acetaminophen', 'butalbital', 'caffeine'] | — | parser: 1 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L36 | buprenorphine/naloxone, naltrexone | therapeutic antagonism, D (contraindicated) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L36 | buprenorphine, clonazepam | respiratory depression, C (major) | MISS | not flagged | 1 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L36 | buprenorphine, gabapentin | respiratory depression, C (major) | MISS | not flagged | 2 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L36 | buprenorphine, quetiapine, clonazepam, gabapentin | CNS depression, B (moderate) | MISS | not flagged | 1, 2 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L37 | dabigatran, dronedarone | P-gp, C (major) | MISS | not flagged | 11 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L37 | dabigatran, verapamil | P-gp, B (moderate) | MISS | not flagged | 11 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L37 | digoxin, dronedarone | digoxin toxicity, C (major) | MISS | not flagged | 18 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L37 | digoxin, verapamil | digoxin toxicity, B (moderate) | MISS | not flagged | 18 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L37 | dronedarone, verapamil | bradycardia/AV block, C (major) | MISS | not flagged | 11, 18 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L37 | simvastatin, dronedarone | myopathy/rhabdomyolysis, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L37 | simvastatin, verapamil | myopathy/rhabdomyolysis, B (moderate) | MISS | not flagged | 27 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L37 | furosemide, digoxin, dronedarone | electrolyte, B (moderate) | MISS | not flagged | 18 | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L38 | risperidone, paliperidone | duplicate therapy, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L38 | risperidone, paliperidone, olanzapine | duplicate therapy, C (major) | MISS | not flagged | — | parser: 3 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L38 | benztropine, olanzapine | anticholinergic burden, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L38 | clonazepam, olanzapine | CNS depression, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L39 | colchicine, erythromycin | P-gp, C (major) | MISS | not flagged | 28 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L39 | simvastatin, erythromycin | myopathy/rhabdomyolysis, D (contraindicated) | MISS | not flagged | 27 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L39 | simvastatin, diltiazem | myopathy/rhabdomyolysis, C (major) | MISS | not flagged | 27 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L39 | colchicine, diltiazem | P-gp, B (moderate) | MISS | not flagged | 28 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L39 | colchicine, simvastatin | myopathy/rhabdomyolysis, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L39 | erythromycin, diltiazem | QT prolongation, C (major) | MISS | not flagged | 27, 28 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L39 | furosemide, erythromycin | electrolyte, B (moderate) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L40 | trazodone, suvorexant, zolpidem, alprazolam | duplicate therapy, C (major) | MISS | not flagged | — | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L40 | trazodone, sertraline | serotonin syndrome, B (moderate) | MISS | not flagged | 7 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L40 | trazodone | QT prolongation, A (minor) | MISS | not flagged | 7 | parser: 1 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L40 | sertraline | dose ceiling, A (minor) | MISS | not flagged | 7 | parser: 1 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L41 | sertraline, sertraline | duplicate entry, C (major) | MISS | not flagged | 13 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L41 | levothyroxine, levothyroxine | unit normalization, C (major) | MISS | not flagged | — | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L41 | ibuprofen, ibuprofen | dose ceiling, C (major) | MISS | not flagged | 13 | parser: 2 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |
| L41 | sertraline, ibuprofen | bleeding, B (moderate) | MISS | not flagged | 13 | parser: 4 of these entries came back "not found" (the Brand (generic) dose = total line was not split into name and dose) |


## 4. False positives and medically inaccurate or misleading statements

**False positives.** None. No flag appeared at B or above on L11 or L29, and none matched a should_not_flag entry. This is trivially true: the site flagged nothing on any list.

**Inaccurate or misleading statements.** The site made no statement about mechanism or danger, so there is nothing to check against the rulebook. Four statements it did make are misleading:

| Where | What the site said | Why it misleads | Correct statement and source |
|---|---|---|---|
| All 41 lists, Interactions column | "No warning found in the labels checked." printed under "0 of N medications checked" | Reads as reassurance when zero labels were checked. L05 holds warfarin + TMP-SMX + amiodarone + aspirin + clopidogrel (rulebook rows 9, 10, 12). | "Nothing was checked: none of these entries could be matched to a drug." A negative claim needs at least one checked label. |
| All lists, A–E strip | "–" in every grade box with 0 checked | Looks identical to "no interactions". | The strip should say "not checked" when nothing was checked. |
| "Did you mean" suggestions | L01 "alprazolam 3 mg [xanax]" for Xanax 1 mg TID; L23 "glipizide 5 mg [glucotrol]" first for 10 mg BID; "propranolol hydrochloride 80 mg [inderal]" for 40 mg BID | The suggestion takes the daily total after "=" (or another strength) as the unit strength. Clicking it records the wrong strength. | Strength is the number before the frequency; the "= total" is the daily amount (Xanax label: 0.25, 0.5, 1, 2 mg tablets). |
| "What the labels say about …" | Coumadin → "Campath / alemtuzumab"; Ambien → "GOCOVRI / amantadine"; Inderal → "Ergomar / ergotamine" | Under a medication, this implies the labels are about that medication. | Show label snippets only for real label-text searches, not for unresolved medication lines. |

## 5. UX findings, ranked by how much they slow or confuse a doctor

1. **The standard prescribing line is rejected.** All 244 entries were rejected as "not found" or "Not a medication name we know." Nothing else on the site works until this does. (All lists.)
2. **Correct suggestions need one click each.** The right drug appears as "Did you mean", but each needs a click. A 6-drug list means 6 clicks and re-entering doses. (All lists.)
3. **"No warning found" shows even when nothing was checked.** This is a false reassurance. (All lists.)
4. **Unrelated label snippets fill the page.** The page grows to about 7,000 px on desktop and about 9,800 px on phone, which buries the grade strip. (All lists; worst on mobile L41.)
5. **Suggestions carry the wrong strength.** (L01, L23, and others.)
6. **Good: the input is focused on load.** 41/41 lists; Return works; the page settles in a median 3.2 s (worst 4.5 s); no console errors; no failed requests; all 466 links return HTTP 200.
7. **Good: the A–E strip is readable at a glance.** It fits one row on a 390 px phone.

## 6. Prioritized fix list

Every fix is a general rule or data change, never a per-list special case.

| Priority | What is wrong | Lists | General fix | How it will be verified on the public site |
|---|---|---|---|---|
| P0 | All 13 contraindicated pairs missed: MAOI + bupropion/meperidine/methylphenidate, rasagiline + meperidine, linezolid + SNRI, PDE5 + nitrate, strong CYP3A4 inhibitor + triazolam/alprazolam/simvastatin, erythromycin + simvastatin, rifampin + lurasidone, naltrexone + buprenorphine | L07, L10, L13, L16, L20, L21, L27, L36, L39 | (a) Parse `Brand (generic) dose frequency = total`: the generic in parentheses is the drug, the text before "=" is dose and frequency, and "= total" cross-checks. (b) Add a class-level interaction layer. Drug classes come from FDA Established Pharmacologic Class / mechanism-of-action data where available, plus a curated property table (strong CYP3A4 inhibitor, MAOI, nitrate, PDE5 inhibitor, opioid agonist/antagonist). Rules come from rulebook rows and label contraindications, and each rule cites its rulebook row and an FDA label section. | Re-run the pack; D recall 13/13; plus the six generalization lists (rows 4, 17, 21, 32, 35, 36) |
| P0 | No false D today; guard it | L11, L29 and all should_not_flag | Class rules fire only on the named classes; controls must stay empty at B or above | Re-run; 0 false positives |
| P1 | 103 major items missed, including opioid + benzodiazepine/gabapentinoid, QT stacks, triple whammy, lithium, digoxin, warfarin 2C9, beta-blocker + non-DHP CCB, anticholinergic burden, and CYP1A2/2D6/2C9/2C19/3A4 inhibition and induction | 39 of 41 lists | Same class layer; group rules (shared-effect classes of 3+ drugs) and pair rules (perpetrator class × victim class); site grade D for major | C recall ≥ 95% |
| P1 | Misleading "No warning found" when nothing was checked | All | Show "Nothing checked" state; strip shows "not checked" | Browser check on an unresolvable list |
| P2 | 0/33 totals, 0/22 duplicate/unit/weekly/combination cases, 0/57 grouping statements | L01, L05, L06, L07, L10, L12, L13, L14, L15, L17, L23, L24, L31, L35, L37, L38, L40, L41 | Per-molecule totals across entries after unit normalization (mcg↔mg↔g); combination products split into components; weekly and specific-day schedules stay weekly; PRN maxima; a dose-ceiling table from labeled maximum daily doses; active-metabolite map (risperidone ↔ paliperidone, fluoxetine in Symbyax); count-based grouping statement ("3 CNS depressants — …") | Totals, duplicate, and grouping rows in the re-run scorecard |
| P3 | One click per suggestion; wrong-strength suggestions; unrelated snippets under medication lines | All | Auto-accept a single confident match and say so; drop snippets for medication lines | Re-run: 0 unresolved entries; page height drops |
| P4 | No interaction links, because there are no flags | All | Every C/D flag carries a DailyMed setid link for the label that states it | "C or D flags with a working drug-specific link" = all |
