# Drug Interaction Screen — Black-Box Test and Evaluation Pack
Version 2026-09-23 v2

How to use: save this file as TEST_PACK.md in the repository root, fill in PUBLIC_URL in Section 1, then send the coding agent this one message:
"Read TEST_PACK.md. Execute the prompt in Section 1 exactly as written. Do not fix anything until Phase 1 and Phase 2 reports are written."

Repository notes (added when the pack was saved, 2026-09-23): PUBLIC_URL is filled in below. Section 6 holds the answer key from data/reference/drug_interaction_screen_fixture.json (created 2026-09-22), because Part 2 was not pasted with the pack. The site grades on an A–E scale; Phase 2 maps it to the pack's A–D scale (site E = pack D, site D = pack C, site C and B = pack B, site A = pack A). The AI tool's name was replaced with "the coding agent" to satisfy the repository's no-attribution test.

---

## Section 1 — Prompt for the coding agent

===== BEGIN PROMPT =====

You are a QA engineer and clinical pharmacologist testing the Drug Interaction Screen, a public website where US doctors enter a patient's prescription list and get back drug-drug interactions, categories, count-based grouping statements, and an A–D severity grade.

PUBLIC_URL: https://rx-label-search-aidancolvins-projects.vercel.app/

If PUBLIC_URL is blank, find it read-only in the deployment config (vercel.json, README, package.json, CI files), load it in a browser to confirm it is the live public site, write the URL you used into the run log, and continue. Do not ask me.

Everything you need is in this file: Section 3 is the clinical rulebook, Section 4 is the severity scale and scoring rules, Section 5 holds the 41 blind test lists, Section 6 holds the answer key.

HARD RULES

1. Phases 1 and 2 are black-box. Use only a real browser pointed at PUBLIC_URL. Do not import, run, call, or read the application code, the API, the database, seed data, or any local server during these phases. If a doctor with a browser cannot do it, you do not do it.
2. Each test list is one hypothetical patient entered by one doctor. Treat every list as a fresh visit: new browser context, cleared cookies and storage, load PUBLIC_URL from scratch.
3. Enter the drugs the way a doctor would: paste the whole line into the input, press Enter. Do not click a submit button unless Enter does nothing. If you had to click anything to type or to submit, that is a defect. Log it.
4. Never edit the test lists, the answer key, or the rulebook.
5. Never special-case, hardcode, or teach to the test. The answer key is for scoring only. Every fix you make later must be a general rule or data change that would also catch drugs not in this pack.
6. Capture everything before you fix anything. All 41 lists run against one version of the site. Record the deployed version (build hash if the site exposes one; otherwise git HEAD of main plus timestamp).
7. Work end to end without stopping to ask. Log open questions in OPEN_QUESTIONS.md.
8. The rulebook in Section 3 is the clinical reference. Every mechanism or danger statement you write, grade, or fix must agree with it or with an FDA label. Say which one.

TOOLING

Use Playwright (npx playwright install chromium if missing). Desktop viewport 1440x900. After the main run, repeat L01, L12, L24, and L41 at 390x844 for mobile readability. Write all output under test_runs/<YYYY-MM-DD_HHMM>/.

PHASE 1 — RUN THE SITE AS 41 USERS

For each list L01 through L41 in Section 5, in order:

a. New context. Load PUBLIC_URL. Wait for network idle.
b. Record: did the input have focus on load without a click? Was it obvious where to type? Seconds to interactive?
c. Paste the full line for that list into the input. Press Enter.
d. Wait until results stop changing (max 30 s). If the page errors or hangs, screenshot it, retry once, log both attempts.
e. Capture, in this order:
   - the exact input string you submitted (this proves the tag)
   - full visible text of the results region, verbatim
   - every severity grade, category label, and grouping statement the site shows (for example "3 CNS depressants")
   - every hyperlink in the results: link text, href, and whether the href returns HTTP 200
   - any per-drug or per-molecule daily totals the site computed
   - whether the site merged duplicate lines, brand/generic pairs, IR/ER forms, or combination-product components
   - full-page screenshot: screenshots/L01.png
   - outerHTML of the results region: dom/L01.html
   - browser console errors and any 4xx/5xx network responses
   - wall-clock seconds from Enter to final results
f. Write results/L01.md with this exact header:
   # L01 — Results from current website
   Site version: <hash or HEAD + timestamp>
   Input submitted: <the exact line>
   then the captured material.

When all 41 are done, build RESULTS_FROM_WEBSITE.md: one section per list, headed "## L01 — Results from current website" through L41, each holding the input line and the verbatim site output. Verify: exactly 41 sections, IDs L01–L41 each once, and the input line under every ID matches Section 5 character for character. Fix the file if not and log the mismatch.

Write USER_FEEDBACK.md as the doctor who just did this 41 times. Be concrete; quote what you saw. Cover at least: where to type and whether it needed a click; whether Enter worked; whether results were readable at a glance or a wall of text; whether the A–D grade was visible without reading; whether the language was plain or intimidating; whether every flag told you what to do next; whether links to a primary source (FDA label on DailyMed, NIH, PubMed) were present, specific, and working; whether totals and merged duplicates were shown; speed; anything confusing, missing, or wrong; mobile findings.

PHASE 2 — GRADE AGAINST THE ANSWER KEY AND THE RULEBOOK

Parse the answer key in Section 6. Map its severities to the A–D scale in Section 4: contraindicated = D, major = C, moderate = B, minor = A. Map the site's own labels to A–D and write the mapping table you used into the report. If the site's scale cannot be mapped, say so and grade on drug set and category only.

For each list, for each item in expected:
  HIT      site flagged the same drugs (or a superset) under an equivalent category at the same or higher grade
  PARTIAL  right drugs but grade off by one, or right drugs and grade but category wrong or missing
  MISS     not flagged, or off by two or more grades
For each list also record:
  FALSE POSITIVE  anything in should_not_flag reported at B or above, and any B-or-above flag on control lists L11 and L29
  TOTALS          for each entry in totals, did the site compute the same per-molecule daily amount, units normalized
  GROUPING        where the key has three or more drugs in one category, did the site produce a count-based statement with the resulting risk (for example "3 CNS depressants — risk of respiratory depression, falls, overdose")
  ACCURACY        for every site statement about mechanism or danger, compare it to the key's "why" and to the rulebook row; log anything medically wrong or misleading, with the correct statement and its source (rulebook row number, FDA label, or PubMed ID)
  LINKS           count of flags carrying a working primary-source link specific to that interaction or drug
  RULEBOOK ROWS   which of rulebook rows 1–36 apply to this list, and for each whether the site named that syndrome

Compute and report:
  - recall by grade: D, C, B, A (D recall is the headline number)
  - precision overall and per grade
  - false positives on control lists (must be zero at B or above)
  - totals correct / totals expected
  - duplicate handling: duplicate-entry, brand/generic, IR/ER, unit-normalization, combination-product cases resolved correctly
  - grouping statements present / expected
  - rulebook coverage: for each of the 36 rows, how many lists it applies to and how many times the site caught it (write RULEBOOK_COVERAGE.md)
  - links present and working / flags shown
  - median and worst seconds to results

Write EVALUATION_REPORT.md in this order:
  1. Summary table of the metrics above
  2. Per-list scorecard L01–L41: expected items, hits, partials, misses, false positives, totals correct, grouping present, links present
  3. Every MISS and PARTIAL: list ID, drugs, expected category and grade, what the site said instead, rulebook row, and your black-box hypothesis for why (missing pair in the data, no class-level rule, no metabolite mapping, no unit normalization, parser split on the wrong token, and so on)
  4. Every FALSE POSITIVE and every medically inaccurate statement, with the correction and source
  5. UX findings from USER_FEEDBACK.md, ranked by how much they slow or confuse a doctor
  6. Prioritized fix list:
       P0  any D-grade miss; any false D
       P1  C-grade misses; false positives on control lists; medically wrong statements
       P2  totals, unit normalization, duplicate and combination parsing, grouping statements
       P3  input focused on load, Enter submits, readability, plain language, grade visible at a glance
       P4  primary-source links on every flag
     Each item: what is wrong, which lists show it, the general fix (not a special case), and how you will verify it on the public site.

Stop here. Commit all reports under test_runs/ before continuing.

PHASE 3 — LEARN, FIX, DEPLOY, RE-TEST

Now you may read and change the application code. Follow the repository's coding standards and its agent instructions file.

Learn first. Create LESSONS_LEARNED.md (append across runs, never overwrite). For every MISS, PARTIAL, and FALSE POSITIVE write one entry: list ID, what the site did, root cause found in the code, pattern class (missing pair, missing class rule, no active-metabolite map, no combination-product parse, unit not normalized, duplicate not merged, severity mapped wrong, grouping absent, copy unreadable, link absent), rulebook row, the general fix, and the regression test you added. Re-read this file at the start of every later Phase 3 cycle so the same class of mistake is not made twice.

Then fix, in priority order. For each fix: implement it as a general rule or data change; add a unit test that would have caught it; commit with a message naming the list IDs it addresses; push main; deploy; wait until the public site serves the new version.

Generalization check. Before re-running the pack, write six new patient lists built from rulebook rows that L01–L41 do not already cover — at minimum: valproate + meropenem (row 32); tizanidine + ciprofloxacin (row 4); codeine + paroxetine (row 35); a fluoroquinolone + a systemic corticosteroid (row 36); a thiazide + an SSRI + carbamazepine (row 17); riociguat + a nitrate (row 21). Run them through the public site exactly as in Phase 1 and grade them against the rulebook row. If a fix passes the pack but fails these, it was a special case. Redo it as a general rule.

Re-run Phase 1 and Phase 2 in full against the public site into a new test_runs/<timestamp>/ folder. Write DIFF_VS_PREVIOUS_RUN.md showing every metric and every list whose result changed, better or worse. Any regression is P0.

Repeat Phase 3 until all of these hold on the public site:
  - D recall = 100%, no false D
  - C recall >= 95%
  - zero B-or-above flags on L11 and L29
  - every totals entry correct
  - every duplicate, brand/generic, IR/ER, unit, and combination case resolved
  - grouping statement present wherever three or more drugs share a category
  - input focused on load, Enter submits, grade visible at a glance, plain language
  - every C or D flag carries a working primary-source link
  - all six generalization lists graded correctly

Finish with FINAL_SUMMARY.md: starting scores, ending scores, every fix made, what still fails and why, and what to do next.

===== END PROMPT =====

---

## Section 2 — What the coding agent produces

All under test_runs/<timestamp>/:

| File | What it is |
|---|---|
| RESULTS_FROM_WEBSITE.md | Verbatim site output per list, tagged L01–L41 |
| USER_FEEDBACK.md | Friction a real doctor would hit |
| EVALUATION_REPORT.md | Scores, misses, why, prioritized fix list |
| RULEBOOK_COVERAGE.md | Which of the 36 syndromes the site catches |
| LESSONS_LEARNED.md | Every mistake, root cause, general fix, regression test (cumulative) |
| DIFF_VS_PREVIOUS_RUN.md | What changed between runs |
| FINAL_SUMMARY.md | Start vs end |

---

## Section 3 — Clinical rulebook: the interactions that actually present

In NHANES 2011–12, five or more prescription drugs was 15% of all adults and 39% of adults 65 and older, up from 24% a decade earlier (Kantor et al., JAMA 2015).

Two framing facts before the list:

1. Interactions are a minority of drug-related admissions. In a 13-study meta-analysis (Dechanont et al., Pharmacoepidemiol Drug Saf 2014), DDIs accounted for a median 1.1% of hospital admissions and 22.2% of admissions that were due to adverse drug reactions; aspirin (23.5%) and other NSAIDs (12.9%) were the drugs most often involved, and GI bleeding (40.4%) and cardiac arrhythmia (29.8%) were the most frequent events. Most drug-related admissions are single-drug dose effects: in adults 65+, warfarin, insulins, oral antiplatelets, and oral hypoglycemics cause about two-thirds of emergency ADE hospitalizations (Budnitz et al., NEJM 2011). The interactions that matter clinically are mostly the ones that push those classes over the edge.
2. On "hypertension syndrome": the only true hypertensive DDI syndrome is MAOI + sympathomimetic (hypertensive crisis), and it is rare. Hypotension, bradycardia, and syncope from stacked cardiovascular drugs are far more common presentations.

Three dozen that actually present, grouped by syndrome. Evidence class is in the last column where it matters.

| Syndrome | Combination | Mechanism | Presents as / evidence |
|---|---|---|---|
| CNS / respiratory depression | 1. Opioid + benzodiazepine | Additive μ-opioid and GABA-A suppression of medullary respiratory drive; boxed warning on both classes (FDA 2016) | Hypoventilation, hypercapnic respiratory failure, aspiration, overdose death |
| | 2. Opioid + gabapentinoid (gabapentin, pregabalin) | Additive respiratory depression; both renally cleared, so AKI stacks exposure; FDA warning 2019 | Same, plus delirium and falls |
| | 3. Oxycodone, fentanyl, or methadone + strong CYP3A4 inhibitor (clarithromycin, ritonavir/cobicistat, itraconazole, voriconazole) | Loss of 3A4 clearance; fentanyl and oxycodone exposure rises 2–3×; methadone also CYP2B6 | Opioid toxidrome days after the antibiotic or antifungal starts; label contraindication for fentanyl |
| | 4. Tizanidine + ciprofloxacin or fluvoxamine | CYP1A2 inhibition; AUC ~10× (cipro), ~33× (fluvoxamine); label contraindication | Profound hypotension, bradycardia, somnolence |
| | 5. Clozapine + fluvoxamine or ciprofloxacin; clozapine after smoking cessation | CYP1A2 inhibition, or loss of tobacco-smoke 1A2 induction (levels rise ~50% within a week of quitting) | Sedation, seizures, hypotension, ileus, aspiration |
| | 6. Anticholinergic burden: diphenhydramine + TCA + oxybutynin + paroxetine + antipsychotic or benztropine | Additive muscarinic antagonism (M1 central, M3 peripheral); Beers list | Anticholinergic toxidrome: delirium, urinary retention, ileus, hyperthermia, falls |
| Serotonergic | 7. SSRI/SNRI + tramadol, meperidine, linezolid, methylene blue, dextromethorphan, lithium, or an MAOI | Synergistic 5-HT2A stimulation; MAO-A inhibition (phenelzine, tranylcypromine, linezolid, methylene blue) plus reuptake blockade is the lethal pair | Serotonin syndrome by Hunter criteria: inducible or spontaneous clonus, hyperreflexia, hyperthermia, autonomic instability. Linezolid: observational. Triptan + SSRI: FDA advisory, thin evidence |
| | 8. Tramadol or bupropion + other threshold-lowering drug; tramadol + CYP2D6 inhibitor (paroxetine, fluoxetine, bupropion) | Parent tramadol is serotonergic; 2D6 blockade cuts the O-desmethyl (M1) opioid metabolite and leaves more parent | Seizures, serotonin syndrome, analgesic failure |
| Bleeding | 9. Warfarin + NSAID (incl. low-dose aspirin) | COX-1 platelet inhibition plus gastric mucosal injury on top of anticoagulation; minor CYP2C9 displacement | Upper GI bleed; the leading DDI admission in Dechanont |
| | 10. Warfarin + TMP-SMX, fluconazole, metronidazole, or amiodarone | CYP2C9 inhibition of S-warfarin (the potent enantiomer); amiodarone also inhibits 3A4 with a weeks-long tail; fluoroquinolones and gut-flora vitamin K loss are weaker | INR >5, GI or intracranial bleed. Rifampin does the reverse (2C9 induction → thrombosis) |
| | 11. Apixaban/rivaroxaban + ketoconazole, itraconazole, ritonavir, or dronedarone; dabigatran + P-gp inhibitor (dronedarone, ketoconazole) | Combined strong CYP3A4 + P-glycoprotein inhibition; dabigatran ~80% renal, so CKD compounds it; labeled contraindications | Major bleeding |
| | 12. Oral anticoagulant + DAPT (triple therapy); anticoagulant + antiplatelet + NSAID | Additive antithrombotic effect | Bleeding. WOEST and AUGUSTUS (RCTs) support dropping aspirin |
| | 13. SSRI + NSAID or anticoagulant | SERT blockade depletes platelet serotonin (platelets cannot synthesize it) | Upper GI bleed; observational, OR ~1.5–2 for SSRI alone, higher with NSAID |
| Kidney / electrolytes | 14. "Triple whammy": ACE inhibitor or ARB + diuretic + NSAID | NSAID removes PGE2/PGI2 afferent arteriolar dilation, RAAS blocker removes efferent constriction, diuretic depletes volume | Acute kidney injury; nested case-control (Lapi, BMJ 2013) ~30% higher risk, highest in first 30 days |
| | 15. ACE inhibitor/ARB + spironolactone or eplerenone ± potassium ± TMP-SMX | Reduced aldosterone plus mineralocorticoid-receptor blockade; trimethoprim blocks ENaC like amiloride | Hyperkalemia, bradyarrhythmia, sudden death. Hyperkalemia admissions rose after RALES (Juurlink, NEJM 2004); TMP-SMX + spironolactone sudden-death signal in Antoniou's Ontario case-control series |
| | 16. Lithium + NSAID, ACE inhibitor/ARB, or thiazide | Lithium is reabsorbed with sodium in the proximal tubule; these raise reabsorption or lower GFR; thiazides raise lithium ~25–40% | Lithium toxicity: coarse tremor, ataxia, confusion, nephrogenic diabetes insipidus, arrhythmia; therapeutic 0.6–1.2 mEq/L |
| | 17. Thiazide + SSRI ± carbamazepine/oxcarbazepine | Thiazide natriuresis plus SIADH-like effect | Hyponatremia, seizures, falls; older women |
| | 18. Digoxin + amiodarone, dronedarone, verapamil, diltiazem, clarithromycin, or itraconazole; digoxin + loop/thiazide | P-gp inhibition raises digoxin 50–100% (halve dose with amiodarone); hypokalemia/hypomagnesemia increase Na+/K+-ATPase binding | Digoxin toxicity: bradycardia, AV block, ventricular ectopy, nausea, xanthopsia; level >2 ng/mL, HF target 0.5–0.9 |
| | 19. Metformin + iodinated contrast or other cause of AKI | Accumulation when GFR falls | Lactic acidosis; rare, causation contested, hold at eGFR <30 |
| Cardiovascular | 20. Beta-blocker + verapamil or diltiazem | Additive AV-nodal blockade and negative inotropy; verapamil also inhibits CYP3A4/P-gp | Bradycardia, high-grade AV block, cardiogenic shock; BRASH syndrome when AKI and hyperkalemia join |
| | 21. Nitrate + PDE5 inhibitor (sildenafil, tadalafil, vardenafil) or riociguat | NO raises cGMP, PDE5 inhibition stops its breakdown | Refractory hypotension; contraindicated; washout 24 h sildenafil, 48 h tadalafil |
| | 22. Alpha-1 blocker (tamsulosin, doxazosin, prazosin) + PDE5 inhibitor or added antihypertensive | Additive vasodilation | Orthostatic hypotension, syncope, hip fracture |
| | 23. Stacked QT prolongers: methadone, ondansetron, haloperidol, quetiapine, citalopram/escitalopram, azithromycin/clarithromycin, fluoroquinolones, azoles, hydroxychloroquine, amiodarone, sotalol, dofetilide + diuretic-induced hypokalemia/hypomagnesemia, or a CYP inhibitor raising one of them | Additive hERG (IKr) blockade | Torsades de pointes, syncope, sudden death; QTc >500 ms is the action threshold; ~30% of DDI admissions in Dechanont were arrhythmias |
| | 24. MAOI (phenelzine, tranylcypromine, selegiline >10 mg, linezolid) + sympathomimetic (pseudoephedrine, phenylephrine, amphetamine) or tyramine | MAO-A inhibition plus indirect norepinephrine release | Hypertensive crisis, intracranial hemorrhage; rare now |
| | 25. Clonidine + beta-blocker | Unopposed alpha-agonism on abrupt clonidine stop | Rebound hypertensive crisis |
| Metabolic / hematologic / other | 26. Sulfonylurea (glipizide, glyburide, glimepiride) + fluconazole, TMP-SMX, or clarithromycin; sulfonylurea + beta-blocker | CYP2C9 inhibition; glyburide's active metabolites are renally cleared; beta-blockers blunt adrenergic warning symptoms | Prolonged hypoglycemia, often >24 h in the elderly; insulin and sulfonylureas are top ADE-admission causes in 65+ (Budnitz) |
| | 27. Simvastatin, lovastatin, or atorvastatin + clarithromycin, itraconazole, ritonavir, or cyclosporine; any statin + gemfibrozil; simvastatin + amiodarone/verapamil/diltiazem | CYP3A4 inhibition; gemfibrozil inhibits OATP1B1 and glucuronidation; label caps simvastatin at 10 mg with amiodarone/verapamil/diltiazem; SLCO1B1 variants raise risk | Myopathy to rhabdomyolysis with myoglobinuric AKI; CK >10× ULN |
| | 28. Colchicine + clarithromycin, cyclosporine, ritonavir, or strong azole | CYP3A4 + P-gp inhibition; contraindicated with renal or hepatic impairment | Pancytopenia, multi-organ failure, death; case series |
| | 29. Allopurinol or febuxostat + azathioprine or 6-mercaptopurine | Xanthine oxidase inhibition blocks 6-MP catabolism, shunting to 6-thioguanine nucleotides | Pancytopenia; cut thiopurine to 25–33% or avoid; TPMT status compounds it |
| | 30. Methotrexate + TMP-SMX, NSAID, PPI, or penicillin | Additive antifolate (DHFR + trimethoprim); reduced OAT1/3 tubular secretion | Pancytopenia, mucositis, hepatotoxicity, AKI; worst with daily-instead-of-weekly dosing error |
| | 31. Clopidogrel + omeprazole or esomeprazole | CYP2C19 inhibition cuts the active thiol metabolite; FDA label warning | Stent thrombosis, MI in observational data; COGENT (RCT) found no harm; contested; pantoprazole preferred |
| | 32. Valproate + carbapenem (meropenem, ertapenem, imipenem) | Carbapenem blocks acylpeptide hydrolase, so valproate-glucuronide cannot be recycled; levels fall 60–100% within 24 h; extra valproate does not rescue | Breakthrough seizures, status epilepticus |
| | 33. Rifampin, carbamazepine, phenytoin, phenobarbital, or St John's wort + DOAC, tacrolimus/cyclosporine, protease inhibitor, oral contraceptive, or methadone | PXR-mediated CYP3A4/P-gp induction; onset 1–2 weeks, offset 2–4 weeks | Therapeutic failure: stroke or VTE, graft rejection, virologic failure, pregnancy, opioid withdrawal |
| | 34. Tacrolimus or cyclosporine + azole, clarithromycin, diltiazem, or verapamil | CYP3A4/P-gp inhibition; narrow therapeutic index | Nephrotoxicity, neurotoxicity, hyperkalemia, hypertension |
| | 35. Codeine or tramadol + CYP2D6 inhibitor (fluoxetine, paroxetine, bupropion, quinidine); or CYP2D6 ultrarapid metabolizer | 2D6 produces the active morphine / M1; inhibitors cause failure, ultrarapid status causes toxicity (pediatric codeine deaths → FDA contraindication under 12) | Analgesic failure or opioid toxidrome; pharmacogenomic |
| | 36. Fluoroquinolone + systemic corticosteroid | Tendon matrix injury; boxed warning; risk highest over 60 | Tendinopathy, Achilles rupture |

Where the evidence is thin or disputed: #31 (clopidogrel–PPI: label warning versus a null RCT), #19 (metformin–contrast: mechanism-plausible, poorly supported), and triptan + SSRI in #7 (advisory built on case reports). Everything else in the table rests on labeled contraindications, RCT signals, or consistent observational data plus a clear mechanism. One caveat on the Dechanont figures: the pooled studies are international, not US-only, and older than the DOAC era, so anticoagulant rows have shifted toward #11 since.

---

## Section 4 — Severity scale A–D and scoring rules

Scale the site should use, and the mapping from the answer key's words:

| Grade | Key word | Meaning |
|---|---|---|
| A | minor | Real but small. Note it; usually no action. |
| B | moderate | Clinically meaningful. Adjust dose or timing, or monitor a named parameter. |
| C | major | Dangerous. High risk of serious harm. Can be prescribed together only with a specific reason and active monitoring. |
| D | contraindicated | Never together. Life-threatening or lethal. |

The line between C and D matters: C is dangerous but still prescribable with care; D should never happen.

Answer-key fields:
- theme — what the list was built to test
- expected[] — drugs, category, severity, why
- totals — per-molecule daily amounts the site should compute after merging duplicate lines, brands, IR/ER forms, and combination-product components
- should_not_flag — drugs or pairs with no clinically significant interaction in that list; reporting them at B or above is a false positive

Control lists: L11 and L29. Any B-or-above flag on them is a false positive.

Scoring: HIT = same drugs (or superset), equivalent category, same or higher grade. PARTIAL = right drugs, grade off by one, or category wrong/missing. MISS = not flagged, or off by two or more grades.

Headline metrics: D recall (must be 100%), C recall, false positives on controls (must be zero), totals correct, duplicate handling, grouping statements present, rulebook coverage, primary-source links present and working.

What the 41 lists cover: serotonin syndrome, CNS and respiratory depression, QT prolongation, bleeding, CYP inhibition and induction, P-gp, hyperkalemia, hypoglycemia, hypotension, bradycardia/AV block, nephrotoxicity, ototoxicity, myelosuppression, myopathy, lithium and digoxin toxicity, seizure threshold, anticholinergic burden, hyperammonemia, adrenal suppression, therapeutic antagonism, absorption/timing; plus parsing cases — same drug on two lines, brand vs generic duplicates, IR + ER of one molecule, active metabolite next to its parent (risperidone + paliperidone), combination-product components (Symbyax, Norco, Fioricet, Bactrim), unit normalization (0.1 mg = 100 mcg), units beyond mg (mcg, mEq, g, units, mcg/h), weekly and alternating-day schedules, PRN maxima, dose ceilings (acetaminophen 4 g, ibuprofen 3.2 g, Adderall 40 mg).

---

## Section 5 — Blind test lists (L01–L41)

One line per list. Drugs separated by commas. No commas inside any entry. Paste the whole line for a list into the site's input.

L01
Ambien (zolpidem) 10 mg once daily at bedtime = 10 mg/day, Xanax (alprazolam) 1 mg three times daily = 3 mg/day, Adderall (amphetamine/dextroamphetamine) 20 mg three times daily = 60 mg/day, Zyprexa (olanzapine) 10 mg once daily = 10 mg/day, Zyprexa (olanzapine) 2.5 mg once daily = 2.5 mg/day

L02
Zoloft (sertraline) 100 mg once daily = 100 mg/day, Ultram (tramadol) 50 mg four times daily = 200 mg/day, Imitrex (sumatriptan) 50 mg as needed may repeat once after 2 hours = 100 mg/day max, Flexeril (cyclobenzaprine) 10 mg three times daily = 30 mg/day, Zofran (ondansetron) 8 mg twice daily = 16 mg/day, Lipitor (atorvastatin) 40 mg once daily = 40 mg/day

L03
Celexa (citalopram) 40 mg once daily = 40 mg/day, Haldol (haloperidol) 5 mg twice daily = 10 mg/day, Zithromax (azithromycin) 500 mg once daily = 500 mg/day, Diflucan (fluconazole) 200 mg once daily = 200 mg/day, Lasix (furosemide) 40 mg once daily = 40 mg/day, Protonix (pantoprazole) 40 mg once daily = 40 mg/day

L04
Lithobid (lithium carbonate ER) 300 mg three times daily = 900 mg/day, Zestril (lisinopril) 20 mg once daily = 20 mg/day, Microzide (hydrochlorothiazide) 25 mg once daily = 25 mg/day, Motrin (ibuprofen) 800 mg three times daily = 2400 mg/day, Topamax (topiramate) 100 mg twice daily = 200 mg/day, Glucophage (metformin) 1000 mg twice daily = 2000 mg/day

L05
Coumadin (warfarin) 5 mg once daily Mon/Wed/Fri = 5 mg on those days, Coumadin (warfarin) 2.5 mg once daily Tue/Thu/Sat/Sun = 2.5 mg on those days, Bactrim DS (sulfamethoxazole/trimethoprim) 800/160 mg twice daily = 1600/320 mg/day, Cordarone (amiodarone) 200 mg once daily = 200 mg/day, Lexapro (escitalopram) 10 mg once daily = 10 mg/day, Bayer (aspirin OTC) 81 mg once daily = 81 mg/day, Plavix (clopidogrel) 75 mg once daily = 75 mg/day

L06
OxyContin (oxycodone ER) 30 mg twice daily = 60 mg/day, Roxicodone (oxycodone IR) 10 mg every 4 hours as needed max 6 doses/day = 60 mg/day max, Klonopin (clonazepam) 1 mg twice daily = 2 mg/day, Neurontin (gabapentin) 600 mg three times daily = 1800 mg/day, Soma (carisoprodol) 350 mg three times daily = 1050 mg/day, Vistaril (hydroxyzine) 25 mg three times daily = 75 mg/day

L07
Nardil (phenelzine) 15 mg three times daily = 45 mg/day, Wellbutrin SR (bupropion SR) 150 mg twice daily = 300 mg/day, Demerol (meperidine) 50 mg every 6 hours as needed max 4 doses/day = 200 mg/day max, Ritalin (methylphenidate) 10 mg twice daily = 20 mg/day, Norvasc (amlodipine) 10 mg once daily = 10 mg/day, Synthroid (levothyroxine) 100 mcg once daily = 100 mcg/day

L08
Clozaril (clozapine) 200 mg twice daily = 400 mg/day, Tegretol (carbamazepine) 400 mg twice daily = 800 mg/day, Luvox (fluvoxamine) 100 mg twice daily = 200 mg/day, Cipro (ciprofloxacin) 500 mg twice daily = 1000 mg/day, Ativan (lorazepam) 1 mg twice daily = 2 mg/day, Depakote (divalproex sodium) 500 mg twice daily = 1000 mg/day

L09
Prozac (fluoxetine) 40 mg once daily = 40 mg/day, Paxil (paroxetine) 20 mg once daily = 20 mg/day, Nolvadex (tamoxifen) 20 mg once daily = 20 mg/day, Toprol-XL (metoprolol succinate) 100 mg once daily = 100 mg/day, Naprosyn (naproxen) 500 mg twice daily = 1000 mg/day, Nexium (esomeprazole) 40 mg once daily = 40 mg/day

L10
Zocor (simvastatin) 40 mg once daily at bedtime = 40 mg/day, Biaxin (clarithromycin) 500 mg twice daily = 1000 mg/day, Aldactone (spironolactone) 25 mg once daily = 25 mg/day, Vasotec (enalapril) 10 mg twice daily = 20 mg/day, Klor-Con (potassium chloride ER) 20 mEq once daily = 20 mEq/day, Trexall (methotrexate) 15 mg once weekly = 15 mg/week

L11
Synthroid (levothyroxine) 75 mcg once daily = 75 mcg/day, Lipitor (atorvastatin) 20 mg once daily = 20 mg/day, Zestril (lisinopril) 10 mg once daily = 10 mg/day, Lexapro (escitalopram) 10 mg once daily = 10 mg/day, Singulair (montelukast) 10 mg once daily = 10 mg/day

L12
Symbyax (olanzapine/fluoxetine) 6/25 mg once daily = 6/25 mg/day, Prozac (fluoxetine) 20 mg once daily = 20 mg/day, Norco (hydrocodone/acetaminophen) 10/325 mg four times daily = 40/1300 mg/day, Tylenol (acetaminophen OTC) 500 mg 2 tablets three times daily = 3000 mg/day, Xanax (alprazolam) 0.5 mg three times daily = 1.5 mg/day, Xanax XR (alprazolam ER) 1 mg once daily = 1 mg/day

L13
Zyvox (linezolid) 600 mg twice daily = 1200 mg/day, Effexor XR (venlafaxine ER) 225 mg once daily = 225 mg/day, Buspar (buspirone) 15 mg twice daily = 30 mg/day, Reglan (metoclopramide) 10 mg four times daily before meals and at bedtime = 40 mg/day, Duragesic (fentanyl) 25 mcg/h transdermal patch one patch every 72 hours = 25 mcg/h continuous, Robaxin (methocarbamol) 750 mg four times daily = 3000 mg/day

L14
Duragesic (fentanyl) 50 mcg/h transdermal patch one patch every 72 hours = 50 mcg/h continuous, Valium (diazepam) 10 mg three times daily = 30 mg/day, Restoril (temazepam) 30 mg once daily at bedtime = 30 mg/day, Lyrica (pregabalin) 150 mg twice daily = 300 mg/day, Phenergan (promethazine) 25 mg every 6 hours as needed max 4 doses/day = 100 mg/day max, Zanaflex (tizanidine) 4 mg three times daily = 12 mg/day

L15
Toprol-XL (metoprolol succinate) 200 mg once daily = 200 mg/day, Cardizem CD (diltiazem ER) 240 mg once daily = 240 mg/day, Lanoxin (digoxin) 0.25 mg once daily = 0.25 mg/day, Cordarone (amiodarone) 200 mg once daily = 200 mg/day, Aricept (donepezil) 10 mg once daily at bedtime = 10 mg/day, Lasix (furosemide) 40 mg once daily = 40 mg/day

L16
Viagra (sildenafil) 100 mg as needed no more than once daily = 100 mg/day max, Nitrostat (nitroglycerin sublingual) 0.4 mg as needed for chest pain up to 3 tablets in 15 minutes = 1.2 mg per episode, Imdur (isosorbide mononitrate ER) 60 mg once daily = 60 mg/day, Flomax (tamsulosin) 0.4 mg once daily = 0.4 mg/day, Catapres (clonidine) 0.1 mg twice daily = 0.2 mg/day, Coreg (carvedilol) 25 mg twice daily = 50 mg/day

L17
Bactrim DS (sulfamethoxazole/trimethoprim) 800/160 mg twice daily = 1600/320 mg/day, Aldactone (spironolactone) 50 mg once daily = 50 mg/day, Cozaar (losartan) 100 mg once daily = 100 mg/day, Klor-Con (potassium chloride ER) 40 mEq once daily = 40 mEq/day, Celebrex (celecoxib) 200 mg twice daily = 400 mg/day, Jardiance (empagliflozin) 10 mg once daily = 10 mg/day

L18
Elavil (amitriptyline) 75 mg once daily at bedtime = 75 mg/day, Ditropan (oxybutynin) 5 mg three times daily = 15 mg/day, Vistaril (hydroxyzine) 50 mg three times daily = 150 mg/day, Cogentin (benztropine) 1 mg twice daily = 2 mg/day, Aricept (donepezil) 10 mg once daily = 10 mg/day, Paxil (paroxetine) 40 mg once daily = 40 mg/day

L19
Wellbutrin XL (bupropion XL) 450 mg once daily = 450 mg/day, Ultram (tramadol) 100 mg four times daily = 400 mg/day, Theo-24 (theophylline ER) 400 mg once daily = 400 mg/day, Cipro (ciprofloxacin) 500 mg twice daily = 1000 mg/day, Seroquel (quetiapine) 400 mg once daily at bedtime = 400 mg/day, Lipitor (atorvastatin) 10 mg once daily = 10 mg/day

L20
Rifadin (rifampin) 600 mg once daily = 600 mg/day, Xarelto (rivaroxaban) 20 mg once daily with the evening meal = 20 mg/day, Sprintec (norgestimate/ethinyl estradiol) 0.25 mg/35 mcg once daily = 0.25 mg/35 mcg/day, Prograf (tacrolimus) 2 mg twice daily = 4 mg/day, Latuda (lurasidone) 80 mg once daily with food = 80 mg/day, Dolophine (methadone) 60 mg once daily = 60 mg/day

L21
Nizoral (ketoconazole) 200 mg once daily = 200 mg/day, Halcion (triazolam) 0.25 mg once daily at bedtime = 0.25 mg/day, Xanax (alprazolam) 1 mg three times daily = 3 mg/day, Eliquis (apixaban) 5 mg twice daily = 10 mg/day, Lipitor (atorvastatin) 80 mg once daily = 80 mg/day, Norvasc (amlodipine) 10 mg once daily = 10 mg/day

L22
Prograf (tacrolimus) 3 mg twice daily = 6 mg/day, CellCept (mycophenolate mofetil) 1000 mg twice daily = 2000 mg/day, Diflucan (fluconazole) 400 mg once daily = 400 mg/day, Zocor (simvastatin) 40 mg once daily at bedtime = 40 mg/day, Prilosec (omeprazole) 20 mg once daily = 20 mg/day, Zofran (ondansetron) 8 mg twice daily = 16 mg/day

L23
Glucotrol (glipizide) 10 mg twice daily = 20 mg/day, Lantus (insulin glargine) 40 units subcutaneous once daily at bedtime = 40 units/day, Inderal (propranolol) 40 mg twice daily = 80 mg/day, Bactrim DS (sulfamethoxazole/trimethoprim) 800/160 mg twice daily = 1600/320 mg/day, Levaquin (levofloxacin) 750 mg once daily = 750 mg/day, Ozempic (semaglutide) 1 mg subcutaneous once weekly = 1 mg/week

L24
Norco (hydrocodone/acetaminophen) 10/325 mg every 6 hours = 40/1300 mg/day, Percocet (oxycodone/acetaminophen) 5/325 mg every 6 hours as needed max 4 doses/day = 20/1300 mg/day max, Ambien (zolpidem) 10 mg once daily at bedtime = 10 mg/day, Lunesta (eszopiclone) 3 mg once daily at bedtime = 3 mg/day, Mobic (meloxicam) 15 mg once daily = 15 mg/day, Aleve (naproxen sodium OTC) 220 mg twice daily = 440 mg/day

L25
Dolophine (methadone) 40 mg twice daily = 80 mg/day, Seroquel (quetiapine) 300 mg once daily at bedtime = 300 mg/day, Zofran (ondansetron) 8 mg twice daily = 16 mg/day, Levaquin (levofloxacin) 500 mg once daily = 500 mg/day, Effexor XR (venlafaxine ER) 150 mg once daily = 150 mg/day, Diflucan (fluconazole) 200 mg once daily = 200 mg/day

L26
Depakote (divalproex sodium DR) 750 mg twice daily = 1500 mg/day, Lamictal (lamotrigine) 200 mg once daily = 200 mg/day, Topamax (topiramate) 100 mg twice daily = 200 mg/day, Bayer (aspirin OTC) 325 mg once daily = 325 mg/day, Tegretol (carbamazepine) 400 mg twice daily = 800 mg/day, Klonopin (clonazepam) 0.5 mg twice daily = 1 mg/day

L27
Sinemet (carbidopa/levodopa) 25/100 mg three times daily = 75/300 mg/day, Azilect (rasagiline) 1 mg once daily = 1 mg/day, Reglan (metoclopramide) 10 mg four times daily before meals and at bedtime = 40 mg/day, Haldol (haloperidol) 2 mg once daily at bedtime = 2 mg/day, Demerol (meperidine) 50 mg every 6 hours as needed max 4 doses/day = 200 mg/day max, Lexapro (escitalopram) 10 mg once daily = 10 mg/day

L28
Prezcobix (darunavir/cobicistat) 800/150 mg once daily with food = 800/150 mg/day, Truvada (emtricitabine/tenofovir disoproxil fumarate) 200/300 mg once daily = 200/300 mg/day, Lipitor (atorvastatin) 80 mg once daily = 80 mg/day, Xanax (alprazolam) 0.5 mg three times daily = 1.5 mg/day, Flonase (fluticasone propionate nasal) 50 mcg per spray 2 sprays each nostril once daily = 200 mcg/day, Viagra (sildenafil) 50 mg as needed no more than once daily = 50 mg/day max

L29
Amoxil (amoxicillin) 500 mg three times daily = 1500 mg/day, Claritin (loratadine OTC) 10 mg once daily = 10 mg/day, Singulair (montelukast) 10 mg once daily = 10 mg/day, Norvasc (amlodipine) 5 mg once daily = 5 mg/day, Zoloft (sertraline) 50 mg once daily = 50 mg/day, Glucophage (metformin) 500 mg twice daily = 1000 mg/day

L30
Synthroid (levothyroxine) 100 mcg once daily = 100 mcg/day, Tums Ultra (calcium carbonate OTC) 1000 mg twice daily = 2000 mg/day, Cipro (ciprofloxacin) 500 mg twice daily = 1000 mg/day, Feosol (ferrous sulfate OTC) 325 mg twice daily = 650 mg/day, Prilosec (omeprazole) 20 mg once daily = 20 mg/day, Plavix (clopidogrel) 75 mg once daily = 75 mg/day

L31
Vancocin (vancomycin) 1000 mg IV every 12 hours = 2000 mg/day, Garamycin (gentamicin) 80 mg IV every 8 hours = 240 mg/day, Lasix (furosemide) 40 mg IV twice daily = 80 mg/day, Toradol (ketorolac) 30 mg IV every 6 hours not to exceed 5 days = 120 mg/day, Zestril (lisinopril) 10 mg once daily = 10 mg/day, Zosyn (piperacillin/tazobactam) 3.375 g IV every 6 hours = 13.5 g/day

L32
Trexall (methotrexate) 20 mg once weekly = 20 mg/week, Bactrim DS (sulfamethoxazole/trimethoprim) 800/160 mg twice daily = 1600/320 mg/day, Imuran (azathioprine) 100 mg once daily = 100 mg/day, Zyloprim (allopurinol) 300 mg once daily = 300 mg/day, Motrin (ibuprofen) 600 mg three times daily = 1800 mg/day, folic acid (generic) 1 mg once daily = 1 mg/day

L33
Dilantin (phenytoin ER) 300 mg once daily at bedtime = 300 mg/day, Coumadin (warfarin) 5 mg once daily = 5 mg/day, Sprintec (norgestimate/ethinyl estradiol) 0.25 mg/35 mcg once daily = 0.25 mg/35 mcg/day, Prozac (fluoxetine) 20 mg once daily = 20 mg/day, Diflucan (fluconazole) 100 mg once daily = 100 mg/day, Lipitor (atorvastatin) 20 mg once daily = 20 mg/day

L34
Vyvanse (lisdexamfetamine) 70 mg once daily in the morning = 70 mg/day, Strattera (atomoxetine) 80 mg once daily = 80 mg/day, Intuniv (guanfacine ER) 3 mg once daily at bedtime = 3 mg/day, Kapvay (clonidine ER) 0.1 mg twice daily = 0.2 mg/day, Paxil (paroxetine) 20 mg once daily = 20 mg/day, Seroquel (quetiapine) 100 mg once daily at bedtime = 100 mg/day

L35
Imitrex (sumatriptan) 100 mg as needed may repeat once after 2 hours max 200 mg/day = 200 mg/day max, Maxalt (rizatriptan) 10 mg as needed may repeat after 2 hours max 30 mg/day = 30 mg/day max, Inderal LA (propranolol ER) 80 mg once daily = 80 mg/day, Elavil (amitriptyline) 50 mg once daily at bedtime = 50 mg/day, Topamax (topiramate) 50 mg twice daily = 100 mg/day, Fioricet (butalbital/acetaminophen/caffeine) 50/325/40 mg 2 tablets every 4 hours as needed max 6 tablets/day = 300/1950/240 mg/day max

L36
Suboxone (buprenorphine/naloxone) 8/2 mg sublingual twice daily = 16/4 mg/day, Revia (naltrexone) 50 mg once daily = 50 mg/day, Campral (acamprosate) 666 mg three times daily = 1998 mg/day, Klonopin (clonazepam) 0.5 mg twice daily = 1 mg/day, Neurontin (gabapentin) 300 mg three times daily = 900 mg/day, Seroquel (quetiapine) 50 mg once daily at bedtime = 50 mg/day

L37
Pradaxa (dabigatran etexilate) 150 mg twice daily = 300 mg/day, Multaq (dronedarone) 400 mg twice daily with meals = 800 mg/day, Calan SR (verapamil ER) 240 mg once daily = 240 mg/day, Lanoxin (digoxin) 0.125 mg once daily = 0.125 mg/day, Zocor (simvastatin) 20 mg once daily at bedtime = 20 mg/day, Lasix (furosemide) 20 mg once daily = 20 mg/day

L38
Risperdal (risperidone) 2 mg twice daily = 4 mg/day, Invega (paliperidone ER) 6 mg once daily = 6 mg/day, Zyprexa (olanzapine) 10 mg once daily at bedtime = 10 mg/day, Cogentin (benztropine) 1 mg twice daily = 2 mg/day, Klonopin (clonazepam) 1 mg twice daily = 2 mg/day, Lipitor (atorvastatin) 20 mg once daily = 20 mg/day

L39
Colcrys (colchicine) 0.6 mg twice daily = 1.2 mg/day, Ery-Tab (erythromycin) 500 mg four times daily = 2000 mg/day, Zocor (simvastatin) 40 mg once daily at bedtime = 40 mg/day, Zyloprim (allopurinol) 300 mg once daily = 300 mg/day, Cardizem CD (diltiazem ER) 240 mg once daily = 240 mg/day, Lasix (furosemide) 40 mg once daily = 40 mg/day

L40
Desyrel (trazodone) 100 mg once daily at bedtime = 100 mg/day, Zoloft (sertraline) 200 mg once daily = 200 mg/day, Belsomra (suvorexant) 20 mg once daily at bedtime = 20 mg/day, Ambien (zolpidem) 10 mg once daily at bedtime = 10 mg/day, Xanax (alprazolam) 0.5 mg three times daily as needed max 3 doses/day = 1.5 mg/day max

L41
Zoloft (sertraline) 50 mg once daily = 50 mg/day, sertraline (generic) 50 mg once daily = 50 mg/day, Synthroid (levothyroxine) 0.1 mg once daily = 0.1 mg/day, levothyroxine (generic) 100 mcg once daily = 100 mcg/day, Motrin (ibuprofen) 800 mg three times daily = 2400 mg/day, Advil (ibuprofen OTC) 200 mg 2 tablets twice daily = 800 mg/day

---

## Section 6 — Answer key (JSON)

One JSON object with a single key, "answer_key", holding entries L01 through L41. Copied from data/reference/drug_interaction_screen_fixture.json (created 2026-09-22).

```json
{
 "answer_key": {
  "L01": {
   "theme": "Same drug entered twice; sedative stacking; stimulant above labeled maximum",
   "expected": [
    {
     "drugs": [
      "olanzapine",
      "olanzapine"
     ],
     "category": "duplicate entry",
     "severity": "moderate",
     "why": "Two Zyprexa lines are one drug. Daily olanzapine is 12.5 mg, not 10 or 2.5."
    },
    {
     "drugs": [
      "alprazolam",
      "zolpidem",
      "olanzapine"
     ],
     "category": "CNS depression",
     "severity": "major",
     "why": "Benzodiazepine + Z-drug + sedating antipsychotic: additive sedation, respiratory depression, falls. Zolpidem + a benzodiazepine is also duplicate sedative-hypnotic therapy."
    },
    {
     "drugs": [
      "amphetamine/dextroamphetamine"
     ],
     "category": "dose ceiling",
     "severity": "moderate",
     "why": "60 mg/day exceeds the Adderall IR labeled maximum of 40 mg/day."
    },
    {
     "drugs": [
      "amphetamine/dextroamphetamine",
      "alprazolam",
      "olanzapine"
     ],
     "category": "opposing pharmacology",
     "severity": "minor",
     "why": "Stimulant against a benzodiazepine and a D2 antagonist; effects partly cancel."
    }
   ],
   "totals": {
    "olanzapine": "12.5 mg"
   }
  },
  "L02": {
   "theme": "Serotonin syndrome cluster; PRN max dosing",
   "expected": [
    {
     "drugs": [
      "sertraline",
      "tramadol",
      "sumatriptan",
      "cyclobenzaprine",
      "ondansetron"
     ],
     "category": "serotonin syndrome",
     "severity": "major",
     "why": "Five serotonergic agents: SSRI, tramadol (reuptake inhibitor + opioid), triptan, cyclobenzaprine (tricyclic-like), ondansetron (FDA 2012 label warning). Sertraline + tramadol alone is major."
    },
    {
     "drugs": [
      "tramadol",
      "sertraline"
     ],
     "category": "seizure threshold",
     "severity": "moderate",
     "why": "Tramadol lowers seizure threshold; SSRI co-use raises the risk."
    },
    {
     "drugs": [
      "ondansetron",
      "tramadol"
     ],
     "category": "efficacy loss",
     "severity": "minor",
     "why": "5-HT3 blockade may reduce tramadol analgesia."
    }
   ],
   "should_not_flag": [
    "atorvastatin"
   ]
  },
  "L03": {
   "theme": "QT prolongation; CYP2C19 inhibition pushing citalopram past its cap; diuretic electrolyte loss",
   "expected": [
    {
     "drugs": [
      "citalopram",
      "haloperidol",
      "azithromycin",
      "fluconazole"
     ],
     "category": "QT prolongation",
     "severity": "major",
     "why": "Four QT-prolonging drugs; torsades risk is additive. Citalopram's QT effect is dose-dependent."
    },
    {
     "drugs": [
      "citalopram",
      "fluconazole"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Fluconazole inhibits CYP2C19. Celexa label caps citalopram at 20 mg/day with CYP2C19 inhibitors; 40 mg here is over the cap."
    },
    {
     "drugs": [
      "haloperidol",
      "fluconazole"
     ],
     "category": "CYP inhibition",
     "severity": "moderate",
     "why": "CYP3A4 inhibition raises haloperidol; more QT and EPS risk."
    },
    {
     "drugs": [
      "furosemide",
      "citalopram",
      "haloperidol",
      "azithromycin",
      "fluconazole"
     ],
     "category": "electrolyte",
     "severity": "moderate",
     "why": "Loop-diuretic hypokalemia and hypomagnesemia amplify QT risk."
    }
   ],
   "should_not_flag": [
    "pantoprazole at moderate or above (weak CYP2C19 effect; not the omeprazole-class problem)"
   ]
  },
  "L04": {
   "theme": "Lithium toxicity from three renal-handling interactions; triple whammy; metformin + topiramate",
   "expected": [
    {
     "drugs": [
      "lithium",
      "lisinopril"
     ],
     "category": "lithium toxicity",
     "severity": "major",
     "why": "ACE inhibitor reduces lithium clearance; levels can rise several-fold over weeks."
    },
    {
     "drugs": [
      "lithium",
      "hydrochlorothiazide"
     ],
     "category": "lithium toxicity",
     "severity": "major",
     "why": "Thiazide sodium loss increases proximal lithium reabsorption; roughly 25-40% level rise."
    },
    {
     "drugs": [
      "lithium",
      "ibuprofen"
     ],
     "category": "lithium toxicity",
     "severity": "major",
     "why": "NSAID lowers renal prostaglandins and lithium clearance; 2,400 mg/day is a full anti-inflammatory dose."
    },
    {
     "drugs": [
      "lisinopril",
      "hydrochlorothiazide",
      "ibuprofen"
     ],
     "category": "nephrotoxicity",
     "severity": "major",
     "why": "Triple whammy: ACE inhibitor + diuretic + NSAID -> acute kidney injury."
    },
    {
     "drugs": [
      "metformin",
      "topiramate"
     ],
     "category": "metabolic acidosis",
     "severity": "moderate",
     "why": "Topiramate (carbonic anhydrase inhibition) and metformin both predispose to metabolic acidosis; Topamax label warns."
    },
    {
     "drugs": [
      "topiramate",
      "hydrochlorothiazide"
     ],
     "category": "electrolyte",
     "severity": "minor",
     "why": "HCTZ raises topiramate exposure ~30%; both cause hypokalemia."
    }
   ]
  },
  "L05": {
   "theme": "Warfarin potentiation; multi-agent bleeding; alternating-day dosing; combination product",
   "expected": [
    {
     "drugs": [
      "warfarin",
      "sulfamethoxazole/trimethoprim"
     ],
     "category": "bleeding",
     "severity": "major",
     "why": "Sulfamethoxazole inhibits CYP2C9 (S-warfarin) and displaces warfarin from albumin; INR often rises sharply within days."
    },
    {
     "drugs": [
      "warfarin",
      "amiodarone"
     ],
     "category": "bleeding",
     "severity": "major",
     "why": "Amiodarone inhibits CYP2C9 and 3A4; warfarin usually needs a 30-50% cut, and the effect persists for weeks after amiodarone stops."
    },
    {
     "drugs": [
      "warfarin",
      "aspirin",
      "clopidogrel"
     ],
     "category": "bleeding",
     "severity": "major",
     "why": "Triple antithrombotic therapy: anticoagulant plus two antiplatelets."
    },
    {
     "drugs": [
      "escitalopram",
      "warfarin",
      "aspirin",
      "clopidogrel"
     ],
     "category": "bleeding",
     "severity": "moderate",
     "why": "SSRI platelet serotonin depletion adds GI bleeding risk on top of antithrombotics."
    },
    {
     "drugs": [
      "escitalopram",
      "amiodarone"
     ],
     "category": "QT prolongation",
     "severity": "major",
     "why": "Both prolong QT; escitalopram's effect is dose-dependent."
    }
   ],
   "totals": {
    "warfarin": "5 mg Mon/Wed/Fri, 2.5 mg other days = 25 mg/week; there is no single daily number",
    "sulfamethoxazole/trimethoprim": "1,600 mg / 320 mg"
   }
  },
  "L06": {
   "theme": "Opioid + benzodiazepine boxed warning; ER and IR of one opioid; MME; sedative burden",
   "expected": [
    {
     "drugs": [
      "oxycodone ER",
      "oxycodone IR"
     ],
     "category": "duplicate entry",
     "severity": "major",
     "why": "Two brands, one molecule: 60 mg scheduled + up to 60 mg PRN = 120 mg/day oxycodone = 180 MME (CDC: reassess at 50, avoid 90+)."
    },
    {
     "drugs": [
      "oxycodone",
      "clonazepam"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "FDA boxed warning: opioid + benzodiazepine -> profound sedation, respiratory depression, death."
    },
    {
     "drugs": [
      "oxycodone",
      "gabapentin"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "FDA 2019 warning: gabapentinoid + opioid respiratory depression."
    },
    {
     "drugs": [
      "oxycodone",
      "carisoprodol",
      "clonazepam"
     ],
     "category": "CNS depression",
     "severity": "major",
     "why": "Carisoprodol (metabolized to meprobamate) + opioid + benzodiazepine is the 'holy trinity' overdose combination."
    },
    {
     "drugs": [
      "hydroxyzine",
      "oxycodone",
      "clonazepam"
     ],
     "category": "CNS depression",
     "severity": "moderate",
     "why": "Sedating antihistamine adds to sedation."
    }
   ],
   "totals": {
    "oxycodone": "120 mg/day max (60 mg ER + 60 mg IR) = 180 MME"
   }
  },
  "L07": {
   "theme": "MAOI contraindications; microgram unit; PRN max",
   "expected": [
    {
     "drugs": [
      "phenelzine",
      "bupropion"
     ],
     "category": "hypertensive crisis",
     "severity": "contraindicated",
     "why": "Wellbutrin label: contraindicated with MAOIs or within 14 days; hypertensive reactions."
    },
    {
     "drugs": [
      "phenelzine",
      "meperidine"
     ],
     "category": "serotonin syndrome",
     "severity": "contraindicated",
     "why": "Meperidine + MAOI causes fatal serotonin syndrome and hyperpyrexia; label contraindication."
    },
    {
     "drugs": [
      "phenelzine",
      "methylphenidate"
     ],
     "category": "hypertensive crisis",
     "severity": "contraindicated",
     "why": "Ritalin label: contraindicated during or within 14 days of MAOI treatment."
    },
    {
     "drugs": [
      "phenelzine",
      "amlodipine"
     ],
     "category": "hypotension",
     "severity": "moderate",
     "why": "MAOIs cause orthostatic hypotension; additive with antihypertensives."
    }
   ],
   "totals": {
    "levothyroxine": "100 mcg = 0.1 mg"
   },
   "should_not_flag": [
    "levothyroxine at moderate or above"
   ]
  },
  "L08": {
   "theme": "Clozapine with opposing CYP effects; bone marrow suppression; respiratory arrest",
   "expected": [
    {
     "drugs": [
      "clozapine",
      "carbamazepine"
     ],
     "category": "myelosuppression",
     "severity": "major",
     "why": "Both cause agranulocytosis; carbamazepine also induces CYP3A4 and cuts clozapine levels roughly in half. Avoid the combination."
    },
    {
     "drugs": [
      "clozapine",
      "fluvoxamine"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Fluvoxamine is a potent CYP1A2 inhibitor; clozapine levels rise 3-5x."
    },
    {
     "drugs": [
      "clozapine",
      "ciprofloxacin"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Ciprofloxacin inhibits CYP1A2; clozapine levels roughly double."
    },
    {
     "drugs": [
      "clozapine",
      "lorazepam"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "Clozapine + benzodiazepine: reported respiratory and cardiac arrest, especially early in treatment."
    },
    {
     "drugs": [
      "carbamazepine",
      "divalproex"
     ],
     "category": "CYP induction",
     "severity": "moderate",
     "why": "Valproate raises carbamazepine-10,11-epoxide (toxicity); carbamazepine lowers valproate levels."
    },
    {
     "drugs": [
      "clozapine",
      "ciprofloxacin"
     ],
     "category": "QT prolongation",
     "severity": "moderate",
     "why": "Additive QT effect."
    }
   ],
   "note": "Net effect on clozapine is unpredictable: one inducer against two inhibitors. The app should surface both directions, not cancel them out."
  },
  "L09": {
   "theme": "Duplicate SSRI; CYP2D6 inhibition of a prodrug and of a substrate; SSRI + NSAID bleeding",
   "expected": [
    {
     "drugs": [
      "fluoxetine",
      "paroxetine"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Two SSRIs: no added benefit, additive serotonin syndrome risk; fluoxetine's long half-life complicates any switch."
    },
    {
     "drugs": [
      "fluoxetine",
      "paroxetine",
      "tamoxifen"
     ],
     "category": "efficacy loss",
     "severity": "major",
     "why": "Strong CYP2D6 inhibitors block conversion of tamoxifen to endoxifen; associated with higher breast cancer recurrence. Avoid."
    },
    {
     "drugs": [
      "fluoxetine",
      "paroxetine",
      "metoprolol"
     ],
     "category": "CYP inhibition",
     "severity": "moderate",
     "why": "Metoprolol is a CYP2D6 substrate; levels rise 2-5x -> bradycardia, hypotension."
    },
    {
     "drugs": [
      "fluoxetine",
      "paroxetine",
      "naproxen"
     ],
     "category": "bleeding",
     "severity": "moderate",
     "why": "SSRI + NSAID: 3-6x upper GI bleeding vs either alone."
    }
   ],
   "should_not_flag": [
    "esomeprazole at moderate or above"
   ]
  },
  "L10": {
   "theme": "Contraindicated statin-macrolide pair; hyperkalemia triad; mEq unit; weekly dosing",
   "expected": [
    {
     "drugs": [
      "simvastatin",
      "clarithromycin"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "contraindicated",
     "why": "Clarithromycin (strong CYP3A4 inhibitor) raises simvastatin roughly 10x; Zocor label contraindication."
    },
    {
     "drugs": [
      "spironolactone",
      "enalapril",
      "potassium chloride"
     ],
     "category": "hyperkalemia",
     "severity": "major",
     "why": "Aldosterone antagonist + ACE inhibitor + potassium supplement."
    },
    {
     "drugs": [
      "methotrexate"
     ],
     "category": "dosing frequency",
     "severity": "major",
     "why": "Once weekly. Treating 15 mg as daily (105 mg/week) is a well-documented fatal error; the app must not compute a daily total for it."
    }
   ],
   "totals": {
    "methotrexate": "15 mg per week (not per day)",
    "potassium chloride": "20 mEq (about 1.5 g KCl)"
   }
  },
  "L11": {
   "theme": "Control: no clinically significant interactions",
   "expected": [],
   "should_not_flag": [
    "any pair at moderate or above; escitalopram + lisinopril hyponatremia is at most minor"
   ]
  },
  "L12": {
   "theme": "Hidden duplicates inside combination products; acetaminophen ceiling; IR + ER summing",
   "expected": [
    {
     "drugs": [
      "olanzapine/fluoxetine",
      "fluoxetine"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Symbyax already contains 25 mg fluoxetine; adding Prozac 20 mg makes 45 mg/day of one drug written twice."
    },
    {
     "drugs": [
      "hydrocodone/acetaminophen",
      "acetaminophen"
     ],
     "category": "dose ceiling",
     "severity": "major",
     "why": "Acetaminophen 1,300 mg (Norco) + 3,000 mg (Tylenol) = 4,300 mg/day, above the 4,000 mg/day ceiling; hepatotoxicity."
    },
    {
     "drugs": [
      "alprazolam",
      "alprazolam ER"
     ],
     "category": "duplicate entry",
     "severity": "moderate",
     "why": "IR + XR of one benzodiazepine: 2.5 mg/day total."
    },
    {
     "drugs": [
      "hydrocodone",
      "alprazolam",
      "olanzapine"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "Opioid + benzodiazepine boxed warning; olanzapine adds sedation."
    },
    {
     "drugs": [
      "fluoxetine",
      "hydrocodone"
     ],
     "category": "CYP inhibition",
     "severity": "moderate",
     "why": "Fluoxetine blocks CYP2D6 conversion of hydrocodone to hydromorphone (less analgesia); hydrocodone is also mildly serotonergic."
    }
   ],
   "totals": {
    "fluoxetine": "45 mg",
    "acetaminophen": "4,300 mg",
    "alprazolam": "2.5 mg",
    "hydrocodone": "40 mg",
    "olanzapine": "6 mg"
   }
  },
  "L13": {
   "theme": "Linezolid acting as an MAOI; serotonergic load; fentanyl patch units",
   "expected": [
    {
     "drugs": [
      "linezolid",
      "venlafaxine"
     ],
     "category": "serotonin syndrome",
     "severity": "contraindicated",
     "why": "Linezolid is a reversible non-selective MAOI. Zyvox label: do not combine with SNRIs/SSRIs unless benefit outweighs risk with close monitoring."
    },
    {
     "drugs": [
      "linezolid",
      "buspirone",
      "fentanyl",
      "metoclopramide"
     ],
     "category": "serotonin syndrome",
     "severity": "major",
     "why": "Each adds serotonergic activity; buspirone is named in the linezolid label."
    },
    {
     "drugs": [
      "fentanyl",
      "methocarbamol"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "Opioid + skeletal muscle relaxant: additive CNS and respiratory depression."
    },
    {
     "drugs": [
      "metoclopramide",
      "venlafaxine",
      "buspirone"
     ],
     "category": "serotonin syndrome",
     "severity": "moderate",
     "why": "Metoclopramide is serotonergic (5-HT4 agonist, 5-HT3 antagonist) on top of an SNRI."
    }
   ],
   "totals": {
    "fentanyl": "25 mcg/h continuous = 600 mcg/day = about 60 MME"
   }
  },
  "L14": {
   "theme": "Respiratory depression stacking; duplicate benzodiazepines; fentanyl MME",
   "expected": [
    {
     "drugs": [
      "fentanyl",
      "diazepam",
      "temazepam"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "Opioid + benzodiazepine boxed warning, with two benzodiazepines present."
    },
    {
     "drugs": [
      "diazepam",
      "temazepam"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Two benzodiazepines."
    },
    {
     "drugs": [
      "fentanyl",
      "pregabalin"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "FDA 2019: gabapentinoid + opioid."
    },
    {
     "drugs": [
      "fentanyl",
      "promethazine"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "Phenothiazine antihistamine potentiates opioid respiratory depression; Phenergan label warns with opioids."
    },
    {
     "drugs": [
      "tizanidine",
      "fentanyl",
      "diazepam",
      "temazepam",
      "pregabalin",
      "promethazine"
     ],
     "category": "CNS depression",
     "severity": "moderate",
     "why": "Alpha-2 agonist: additive sedation and hypotension."
    }
   ],
   "totals": {
    "fentanyl": "50 mcg/h continuous = 1,200 mcg/day = about 120 MME"
   }
  },
  "L15": {
   "theme": "Bradycardia and AV block; digoxin level elevation; electrolyte-driven digoxin toxicity",
   "expected": [
    {
     "drugs": [
      "metoprolol",
      "diltiazem"
     ],
     "category": "bradycardia/AV block",
     "severity": "major",
     "why": "Beta-blocker + non-dihydropyridine calcium channel blocker: additive negative chronotropy, inotropy, and AV conduction slowing."
    },
    {
     "drugs": [
      "digoxin",
      "amiodarone"
     ],
     "category": "digoxin toxicity",
     "severity": "major",
     "why": "Amiodarone inhibits P-gp; digoxin levels rise about 70%. Cut digoxin 30-50%."
    },
    {
     "drugs": [
      "digoxin",
      "diltiazem"
     ],
     "category": "digoxin toxicity",
     "severity": "moderate",
     "why": "Diltiazem raises digoxin 20-50%."
    },
    {
     "drugs": [
      "digoxin",
      "metoprolol",
      "diltiazem",
      "amiodarone"
     ],
     "category": "bradycardia/AV block",
     "severity": "major",
     "why": "Four AV-nodal depressants."
    },
    {
     "drugs": [
      "donepezil",
      "metoprolol",
      "diltiazem",
      "digoxin"
     ],
     "category": "bradycardia/AV block",
     "severity": "moderate",
     "why": "Cholinesterase inhibitor vagotonic effect: bradycardia, syncope, heart block with other rate-slowing drugs."
    },
    {
     "drugs": [
      "furosemide",
      "digoxin",
      "amiodarone"
     ],
     "category": "electrolyte",
     "severity": "moderate",
     "why": "Hypokalemia and hypomagnesemia increase digoxin toxicity and amiodarone QT risk."
    },
    {
     "drugs": [
      "amiodarone",
      "metoprolol"
     ],
     "category": "CYP inhibition",
     "severity": "moderate",
     "why": "Amiodarone inhibits CYP2D6 -> higher metoprolol, plus additive bradycardia."
    }
   ],
   "totals": {
    "digoxin": "0.25 mg = 250 mcg"
   }
  },
  "L16": {
   "theme": "Nitrate + PDE5 contraindication; additive hypotension; clonidine with a beta-blocker",
   "expected": [
    {
     "drugs": [
      "sildenafil",
      "nitroglycerin"
     ],
     "category": "hypotension",
     "severity": "contraindicated",
     "why": "PDE5 inhibitor + nitrate: cGMP accumulation -> severe, refractory hypotension."
    },
    {
     "drugs": [
      "sildenafil",
      "isosorbide mononitrate"
     ],
     "category": "hypotension",
     "severity": "contraindicated",
     "why": "Same mechanism; a long-acting nitrate leaves no safe window."
    },
    {
     "drugs": [
      "sildenafil",
      "tamsulosin"
     ],
     "category": "hypotension",
     "severity": "moderate",
     "why": "Alpha-1 blocker + PDE5 inhibitor: symptomatic orthostatic hypotension; Viagra label advises a stable alpha-blocker dose first."
    },
    {
     "drugs": [
      "clonidine",
      "carvedilol"
     ],
     "category": "bradycardia/AV block",
     "severity": "major",
     "why": "Additive bradycardia; if clonidine is stopped, unopposed alpha stimulation under beta-blockade causes rebound hypertensive crisis. Taper the beta-blocker first."
    },
    {
     "drugs": [
      "carvedilol",
      "tamsulosin",
      "clonidine",
      "isosorbide mononitrate"
     ],
     "category": "hypotension",
     "severity": "moderate",
     "why": "Additive vasodilation and orthostasis."
    }
   ]
  },
  "L17": {
   "theme": "Hyperkalemia from four directions; triple whammy AKI; SGLT2 volume depletion",
   "expected": [
    {
     "drugs": [
      "trimethoprim",
      "spironolactone",
      "losartan",
      "potassium chloride"
     ],
     "category": "hyperkalemia",
     "severity": "major",
     "why": "Trimethoprim blocks ENaC like amiloride; with an aldosterone antagonist, an ARB, and 40 mEq KCl, hyperkalemia risk is high."
    },
    {
     "drugs": [
      "losartan",
      "spironolactone",
      "celecoxib"
     ],
     "category": "nephrotoxicity",
     "severity": "major",
     "why": "Triple whammy: RAS blocker + diuretic + NSAID -> AKI; the NSAID also blunts the ARB's BP effect."
    },
    {
     "drugs": [
      "empagliflozin",
      "spironolactone",
      "celecoxib",
      "losartan"
     ],
     "category": "nephrotoxicity",
     "severity": "moderate",
     "why": "SGLT2 osmotic diuresis plus diuretic and NSAID: volume depletion and AKI."
    }
   ],
   "totals": {
    "sulfamethoxazole/trimethoprim": "1,600 mg / 320 mg"
   }
  },
  "L18": {
   "theme": "Anticholinergic burden; cholinesterase inhibitor opposed by anticholinergics; CYP2D6 raising a TCA",
   "expected": [
    {
     "drugs": [
      "amitriptyline",
      "oxybutynin",
      "hydroxyzine",
      "benztropine",
      "paroxetine"
     ],
     "category": "anticholinergic burden",
     "severity": "major",
     "why": "Five anticholinergic drugs: delirium, urinary retention, constipation/ileus, blurred vision, falls, hyperthermia."
    },
    {
     "drugs": [
      "donepezil",
      "amitriptyline",
      "oxybutynin",
      "hydroxyzine",
      "benztropine"
     ],
     "category": "therapeutic antagonism",
     "severity": "major",
     "why": "Anticholinergics directly oppose a cholinesterase inhibitor and worsen cognition."
    },
    {
     "drugs": [
      "paroxetine",
      "amitriptyline"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Paroxetine is a strong CYP2D6 inhibitor; amitriptyline and nortriptyline levels rise -> TCA toxicity, QT prolongation, seizures; also serotonin syndrome risk."
    },
    {
     "drugs": [
      "amitriptyline",
      "hydroxyzine"
     ],
     "category": "QT prolongation",
     "severity": "moderate",
     "why": "Additive QT effect."
    }
   ]
  },
  "L19": {
   "theme": "Seizure threshold at labeled maximums; CYP1A2 inhibition of theophylline; QT",
   "expected": [
    {
     "drugs": [
      "bupropion",
      "tramadol",
      "theophylline",
      "ciprofloxacin",
      "quetiapine"
     ],
     "category": "seizure threshold",
     "severity": "major",
     "why": "Bupropion at 450 mg (labeled max; seizure risk is dose-dependent), tramadol at 400 mg (max), theophylline, a fluoroquinolone, and an antipsychotic each lower seizure threshold."
    },
    {
     "drugs": [
      "theophylline",
      "ciprofloxacin"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Ciprofloxacin inhibits CYP1A2; theophylline levels can rise 20-100%+ -> seizures, arrhythmias. Cipro label: avoid or monitor levels."
    },
    {
     "drugs": [
      "ciprofloxacin",
      "quetiapine"
     ],
     "category": "QT prolongation",
     "severity": "moderate",
     "why": "Additive QT effect."
    },
    {
     "drugs": [
      "bupropion",
      "tramadol"
     ],
     "category": "CYP inhibition",
     "severity": "moderate",
     "why": "Bupropion (strong CYP2D6 inhibitor) blocks tramadol activation to O-desmethyltramadol: less analgesia, more parent-drug seizure and serotonin risk."
    }
   ],
   "should_not_flag": [
    "atorvastatin"
   ]
  },
  "L20": {
   "theme": "Strong CYP3A4/P-gp inducer undermining five drugs",
   "expected": [
    {
     "drugs": [
      "rifampin",
      "rivaroxaban"
     ],
     "category": "efficacy loss",
     "severity": "major",
     "why": "Rivaroxaban exposure falls about 50%; Xarelto label: avoid with combined P-gp and strong CYP3A4 inducers. Thrombosis risk."
    },
    {
     "drugs": [
      "rifampin",
      "norgestimate/ethinyl estradiol"
     ],
     "category": "efficacy loss",
     "severity": "major",
     "why": "Contraceptive failure; non-hormonal backup during and for 28 days after rifampin."
    },
    {
     "drugs": [
      "rifampin",
      "tacrolimus"
     ],
     "category": "efficacy loss",
     "severity": "major",
     "why": "Tacrolimus levels fall sharply -> graft rejection; needs dose increase and level monitoring."
    },
    {
     "drugs": [
      "rifampin",
      "lurasidone"
     ],
     "category": "CYP induction",
     "severity": "contraindicated",
     "why": "Latuda label: contraindicated with strong CYP3A4 inducers."
    },
    {
     "drugs": [
      "rifampin",
      "methadone"
     ],
     "category": "efficacy loss",
     "severity": "major",
     "why": "Methadone levels drop -> opioid withdrawal within days; dose increase required."
    }
   ]
  },
  "L21": {
   "theme": "Strong CYP3A4 inhibitor against benzodiazepines, a DOAC, and a statin",
   "expected": [
    {
     "drugs": [
      "ketoconazole",
      "triazolam"
     ],
     "category": "CYP inhibition",
     "severity": "contraindicated",
     "why": "Triazolam AUC rises more than 20x; profound, prolonged sedation. Both labels contraindicate."
    },
    {
     "drugs": [
      "ketoconazole",
      "alprazolam"
     ],
     "category": "CYP inhibition",
     "severity": "contraindicated",
     "why": "Alprazolam AUC about 4x; Xanax label contraindicates ketoconazole and itraconazole."
    },
    {
     "drugs": [
      "ketoconazole",
      "apixaban"
     ],
     "category": "bleeding",
     "severity": "major",
     "why": "Combined strong CYP3A4 + P-gp inhibitor: Eliquis label -> reduce to 2.5 mg twice daily."
    },
    {
     "drugs": [
      "ketoconazole",
      "atorvastatin"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "major",
     "why": "Atorvastatin exposure at least doubles; 80 mg is the maximum dose -> myopathy risk."
    },
    {
     "drugs": [
      "ketoconazole",
      "amlodipine"
     ],
     "category": "CYP inhibition",
     "severity": "minor",
     "why": "Amlodipine exposure rises modestly; hypotension, edema."
    }
   ]
  },
  "L22": {
   "theme": "Transplant regimen: azole raising tacrolimus; QT; PPI reducing mycophenolate",
   "expected": [
    {
     "drugs": [
      "tacrolimus",
      "fluconazole"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Fluconazole 400 mg inhibits CYP3A4; tacrolimus rises -> nephrotoxicity, neurotoxicity, hyperkalemia. Preemptive dose reduction and levels."
    },
    {
     "drugs": [
      "tacrolimus",
      "fluconazole",
      "ondansetron"
     ],
     "category": "QT prolongation",
     "severity": "major",
     "why": "Three QT-prolonging drugs."
    },
    {
     "drugs": [
      "mycophenolate mofetil",
      "omeprazole"
     ],
     "category": "absorption/timing",
     "severity": "moderate",
     "why": "Higher gastric pH reduces mycophenolate mofetil dissolution; MPA exposure falls 25-35%. Less of an issue with enteric-coated mycophenolate sodium."
    },
    {
     "drugs": [
      "simvastatin",
      "fluconazole"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "moderate",
     "why": "Moderate CYP3A4 inhibition; simvastatin 40 mg is at the upper end."
    },
    {
     "drugs": [
      "tacrolimus",
      "omeprazole"
     ],
     "category": "CYP inhibition",
     "severity": "minor",
     "why": "Omeprazole (CYP2C19/3A4) can modestly raise tacrolimus."
    }
   ]
  },
  "L23": {
   "theme": "Hypoglycemia; CYP2C9 on a sulfonylurea; beta-blocker masking; weekly injectable and unit-based dosing",
   "expected": [
    {
     "drugs": [
      "glipizide",
      "insulin glargine",
      "semaglutide"
     ],
     "category": "hypoglycemia",
     "severity": "major",
     "why": "Three glucose-lowering agents; adding a GLP-1 agonist to insulin + sulfonylurea calls for dose cuts in the latter two."
    },
    {
     "drugs": [
      "glipizide",
      "sulfamethoxazole/trimethoprim"
     ],
     "category": "hypoglycemia",
     "severity": "major",
     "why": "Sulfamethoxazole inhibits CYP2C9 -> glipizide accumulates; severe hypoglycemia reported."
    },
    {
     "drugs": [
      "levofloxacin",
      "glipizide",
      "insulin glargine"
     ],
     "category": "hypoglycemia",
     "severity": "major",
     "why": "Fluoroquinolone boxed warning: dysglycemia, worst with sulfonylureas and insulin."
    },
    {
     "drugs": [
      "propranolol",
      "glipizide",
      "insulin glargine"
     ],
     "category": "hypoglycemia",
     "severity": "moderate",
     "why": "Non-selective beta-blockade masks tachycardia and tremor and delays glucose recovery."
    },
    {
     "drugs": [
      "semaglutide",
      "glipizide"
     ],
     "category": "absorption/timing",
     "severity": "minor",
     "why": "Delayed gastric emptying alters oral drug absorption."
    }
   ],
   "totals": {
    "insulin glargine": "40 units (units, not mg)",
    "semaglutide": "1 mg per week (not per day)"
   }
  },
  "L24": {
   "theme": "Duplicate therapy across three classes; hidden acetaminophen total; MME",
   "expected": [
    {
     "drugs": [
      "hydrocodone/acetaminophen",
      "oxycodone/acetaminophen"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Two full-agonist opioids; hydrocodone 40 mg + oxycodone 20 mg is about 70 MME."
    },
    {
     "drugs": [
      "acetaminophen",
      "acetaminophen"
     ],
     "category": "duplicate entry",
     "severity": "moderate",
     "why": "1,300 + 1,300 = 2,600 mg/day. Under the 4,000 mg ceiling: the app should compute it and not flag a ceiling breach."
    },
    {
     "drugs": [
      "zolpidem",
      "eszopiclone"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Two Z-drugs at bedtime; both labels warn against other sedative-hypnotics; complex sleep behavior boxed warning."
    },
    {
     "drugs": [
      "meloxicam",
      "naproxen sodium"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Two NSAIDs: additive GI bleeding, renal, and cardiovascular risk with no added benefit."
    },
    {
     "drugs": [
      "hydrocodone",
      "oxycodone",
      "zolpidem",
      "eszopiclone"
     ],
     "category": "CNS depression",
     "severity": "major",
     "why": "Opioids + sedative-hypnotics: respiratory depression."
    }
   ],
   "totals": {
    "acetaminophen": "2,600 mg",
    "hydrocodone": "40 mg",
    "oxycodone": "20 mg max",
    "combined opioid": "about 70 MME"
   }
  },
  "L25": {
   "theme": "Methadone QT stacking; azole raising methadone; serotonin",
   "expected": [
    {
     "drugs": [
      "methadone",
      "quetiapine",
      "ondansetron",
      "levofloxacin",
      "fluconazole"
     ],
     "category": "QT prolongation",
     "severity": "major",
     "why": "Five QT-prolonging drugs; methadone at 80 mg/day carries independent torsades risk."
    },
    {
     "drugs": [
      "methadone",
      "fluconazole"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Fluconazole inhibits CYP3A4, 2C9, 2C19; methadone exposure rises about 35% -> respiratory depression and more QT."
    },
    {
     "drugs": [
      "methadone",
      "venlafaxine"
     ],
     "category": "serotonin syndrome",
     "severity": "moderate",
     "why": "Methadone is serotonergic; SNRI co-use."
    },
    {
     "drugs": [
      "methadone",
      "quetiapine"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "Opioid + sedating antipsychotic."
    },
    {
     "drugs": [
      "quetiapine",
      "fluconazole"
     ],
     "category": "CYP inhibition",
     "severity": "moderate",
     "why": "CYP3A4 inhibition raises quetiapine."
    }
   ]
  },
  "L26": {
   "theme": "Valproate-lamotrigine; enzyme induction; hyperammonemia; salicylate displacement",
   "expected": [
    {
     "drugs": [
      "divalproex",
      "lamotrigine"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Valproate inhibits lamotrigine glucuronidation and about doubles its half-life -> SJS/TEN risk. Lamictal label: with valproate, bipolar maintenance dose is 100 mg/day; 200 mg here needs review."
    },
    {
     "drugs": [
      "carbamazepine",
      "lamotrigine"
     ],
     "category": "CYP induction",
     "severity": "moderate",
     "why": "Carbamazepine lowers lamotrigine about 40%; with valproate also present, net level is unpredictable."
    },
    {
     "drugs": [
      "carbamazepine",
      "divalproex"
     ],
     "category": "CYP induction",
     "severity": "moderate",
     "why": "Valproate raises carbamazepine-10,11-epoxide; carbamazepine lowers valproate."
    },
    {
     "drugs": [
      "divalproex",
      "topiramate"
     ],
     "category": "hyperammonemia",
     "severity": "major",
     "why": "Hyperammonemic encephalopathy and hypothermia; both labels warn."
    },
    {
     "drugs": [
      "divalproex",
      "aspirin"
     ],
     "category": "bleeding",
     "severity": "moderate",
     "why": "Salicylate displaces valproate from albumin and inhibits its metabolism -> higher free levels; valproate thrombocytopenia plus aspirin platelet inhibition."
    },
    {
     "drugs": [
      "carbamazepine",
      "clonazepam"
     ],
     "category": "CYP induction",
     "severity": "minor",
     "why": "Carbamazepine lowers clonazepam 20-30%."
    },
    {
     "drugs": [
      "divalproex",
      "lamotrigine",
      "topiramate",
      "carbamazepine",
      "clonazepam"
     ],
     "category": "CNS depression",
     "severity": "moderate",
     "why": "Five CNS-active agents: sedation, cognitive slowing, ataxia."
    }
   ]
  },
  "L27": {
   "theme": "Dopamine antagonists opposing levodopa; MAO-B inhibitor with meperidine; serotonergic caution",
   "expected": [
    {
     "drugs": [
      "carbidopa/levodopa",
      "metoclopramide"
     ],
     "category": "therapeutic antagonism",
     "severity": "major",
     "why": "Metoclopramide blocks D2 receptors: worsens parkinsonism and negates levodopa. Avoid in Parkinson's disease."
    },
    {
     "drugs": [
      "carbidopa/levodopa",
      "haloperidol"
     ],
     "category": "therapeutic antagonism",
     "severity": "major",
     "why": "Potent D2 antagonist; same problem. If an antipsychotic is needed, quetiapine or clozapine."
    },
    {
     "drugs": [
      "rasagiline",
      "meperidine"
     ],
     "category": "serotonin syndrome",
     "severity": "contraindicated",
     "why": "Azilect label: contraindicated with meperidine (also tramadol, methadone, dextromethorphan)."
    },
    {
     "drugs": [
      "rasagiline",
      "escitalopram"
     ],
     "category": "serotonin syndrome",
     "severity": "moderate",
     "why": "Cases reported with MAO-B inhibitors + SSRIs; use the lowest SSRI dose and monitor."
    },
    {
     "drugs": [
      "metoclopramide",
      "haloperidol"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Two D2 antagonists: additive extrapyramidal symptoms, tardive dyskinesia, NMS risk."
    },
    {
     "drugs": [
      "haloperidol",
      "escitalopram"
     ],
     "category": "QT prolongation",
     "severity": "moderate",
     "why": "Additive QT effect."
    }
   ]
  },
  "L28": {
   "theme": "Cobicistat boosting: statin, benzodiazepine, inhaled steroid, PDE5 inhibitor, tenofovir",
   "expected": [
    {
     "drugs": [
      "darunavir/cobicistat",
      "atorvastatin"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "major",
     "why": "Cobicistat (strong CYP3A4 inhibitor) raises atorvastatin several-fold; Prezcobix label: start at the lowest dose and titrate. 80 mg is unsafe."
    },
    {
     "drugs": [
      "darunavir/cobicistat",
      "alprazolam"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Alprazolam exposure rises; prolonged sedation and respiratory depression. Monitor or switch to lorazepam."
    },
    {
     "drugs": [
      "darunavir/cobicistat",
      "fluticasone propionate"
     ],
     "category": "adrenal suppression",
     "severity": "major",
     "why": "Cobicistat blocks CYP3A4 clearance of fluticasone -> systemic corticosteroid exposure, Cushing's syndrome, adrenal suppression. Label: avoid; use beclomethasone."
    },
    {
     "drugs": [
      "darunavir/cobicistat",
      "sildenafil"
     ],
     "category": "hypotension",
     "severity": "major",
     "why": "Sildenafil exposure rises up to 10x; label: 25 mg no more than once per 48 hours."
    },
    {
     "drugs": [
      "darunavir/cobicistat",
      "tenofovir disoproxil fumarate"
     ],
     "category": "nephrotoxicity",
     "severity": "moderate",
     "why": "Cobicistat raises tenofovir exposure and blocks tubular creatinine secretion (MATE1); serum creatinine rises without true GFR loss. Monitor renal function."
    }
   ],
   "should_not_flag": [
    "emtricitabine"
   ]
  },
  "L29": {
   "theme": "Control: no clinically significant interactions",
   "expected": [],
   "should_not_flag": [
    "any pair at moderate or above"
   ]
  },
  "L30": {
   "theme": "Absorption and timing interactions versus one true CYP problem",
   "expected": [
    {
     "drugs": [
      "levothyroxine",
      "calcium carbonate"
     ],
     "category": "absorption/timing",
     "severity": "moderate",
     "why": "Calcium binds levothyroxine in the gut; separate by 4 hours."
    },
    {
     "drugs": [
      "levothyroxine",
      "ferrous sulfate"
     ],
     "category": "absorption/timing",
     "severity": "moderate",
     "why": "Iron binds levothyroxine; separate by 4 hours."
    },
    {
     "drugs": [
      "ciprofloxacin",
      "calcium carbonate"
     ],
     "category": "absorption/timing",
     "severity": "major",
     "why": "Divalent cations chelate fluoroquinolones; cipro AUC falls up to about 40%. Take cipro 2 hours before or 6 hours after."
    },
    {
     "drugs": [
      "ciprofloxacin",
      "ferrous sulfate"
     ],
     "category": "absorption/timing",
     "severity": "major",
     "why": "Iron chelation cuts cipro absorption about 50%; same spacing rule."
    },
    {
     "drugs": [
      "clopidogrel",
      "omeprazole"
     ],
     "category": "efficacy loss",
     "severity": "major",
     "why": "Omeprazole inhibits CYP2C19 activation of clopidogrel; FDA: avoid omeprazole and esomeprazole, use pantoprazole."
    },
    {
     "drugs": [
      "ferrous sulfate",
      "omeprazole"
     ],
     "category": "absorption/timing",
     "severity": "minor",
     "why": "Acid suppression reduces non-heme iron absorption."
    },
    {
     "drugs": [
      "levothyroxine",
      "omeprazole"
     ],
     "category": "absorption/timing",
     "severity": "minor",
     "why": "Acid suppression modestly reduces levothyroxine absorption."
    }
   ],
   "note": "Correct output distinguishes spacing advice from a contraindication; nothing in this list is contraindicated."
  },
  "L31": {
   "theme": "Additive nephrotoxicity and ototoxicity; IV routes; gram unit",
   "expected": [
    {
     "drugs": [
      "vancomycin",
      "gentamicin"
     ],
     "category": "nephrotoxicity",
     "severity": "major",
     "why": "Glycopeptide + aminoglycoside: synergistic nephrotoxicity."
    },
    {
     "drugs": [
      "vancomycin",
      "piperacillin/tazobactam"
     ],
     "category": "nephrotoxicity",
     "severity": "moderate",
     "why": "Observational data show higher AKI rates than vancomycin + cefepime or meropenem; part may be a creatinine-secretion artifact. Contested."
    },
    {
     "drugs": [
      "gentamicin",
      "furosemide"
     ],
     "category": "ototoxicity",
     "severity": "major",
     "why": "Loop diuretic + aminoglycoside: additive, sometimes permanent hearing loss."
    },
    {
     "drugs": [
      "ketorolac",
      "lisinopril",
      "furosemide"
     ],
     "category": "nephrotoxicity",
     "severity": "major",
     "why": "Triple whammy with a parenteral NSAID; Toradol label warns in volume depletion and renal impairment; 5-day limit."
    },
    {
     "drugs": [
      "ketorolac",
      "gentamicin",
      "vancomycin"
     ],
     "category": "nephrotoxicity",
     "severity": "major",
     "why": "NSAID removes renal prostaglandin protection during nephrotoxin exposure."
    },
    {
     "drugs": [
      "ketorolac",
      "lisinopril"
     ],
     "category": "hyperkalemia",
     "severity": "moderate",
     "why": "NSAID + ACE inhibitor."
    }
   ],
   "totals": {
    "piperacillin/tazobactam": "13.5 g per day (3.375 g x 4)",
    "vancomycin": "2 g per day"
   }
  },
  "L32": {
   "theme": "Antifolate stacking; xanthine oxidase inhibition on azathioprine; NSAID on methotrexate; weekly dosing",
   "expected": [
    {
     "drugs": [
      "methotrexate",
      "sulfamethoxazole/trimethoprim"
     ],
     "category": "myelosuppression",
     "severity": "major",
     "why": "Additive dihydrofolate reductase inhibition plus reduced renal MTX clearance; fatal pancytopenia reported even at low weekly doses."
    },
    {
     "drugs": [
      "azathioprine",
      "allopurinol"
     ],
     "category": "myelosuppression",
     "severity": "major",
     "why": "Allopurinol blocks xanthine oxidase, a main 6-mercaptopurine elimination route. Reduce azathioprine to 25-33% of dose or avoid."
    },
    {
     "drugs": [
      "methotrexate",
      "ibuprofen"
     ],
     "category": "nephrotoxicity",
     "severity": "moderate",
     "why": "NSAIDs reduce MTX renal clearance; risk is mainly at high MTX doses, but 1,800 mg/day ibuprofen with 20 mg/week warrants caution."
    },
    {
     "drugs": [
      "methotrexate",
      "azathioprine"
     ],
     "category": "myelosuppression",
     "severity": "moderate",
     "why": "Additive marrow suppression."
    },
    {
     "drugs": [
      "methotrexate"
     ],
     "category": "dosing frequency",
     "severity": "major",
     "why": "Once weekly; 20 mg/day would be lethal. The app must not compute a daily total."
    }
   ],
   "should_not_flag": [
    "folic acid (it reduces methotrexate toxicity)"
   ]
  },
  "L33": {
   "theme": "Phenytoin: induction of contraceptive and statin; CYP2C9 inhibitors raising phenytoin; warfarin",
   "expected": [
    {
     "drugs": [
      "phenytoin",
      "norgestimate/ethinyl estradiol"
     ],
     "category": "efficacy loss",
     "severity": "major",
     "why": "Contraceptive failure; non-hormonal backup needed."
    },
    {
     "drugs": [
      "phenytoin",
      "fluoxetine"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Fluoxetine inhibits CYP2C9; phenytoin's saturable kinetics mean a small clearance change causes a large level rise -> ataxia, nystagmus."
    },
    {
     "drugs": [
      "phenytoin",
      "fluconazole"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Fluconazole inhibits CYP2C9 -> phenytoin toxicity; Diflucan label."
    },
    {
     "drugs": [
      "phenytoin",
      "warfarin"
     ],
     "category": "bleeding",
     "severity": "major",
     "why": "Bidirectional: early protein displacement raises INR, later induction lowers it, and phenytoin levels may rise. Monitor INR and phenytoin levels."
    },
    {
     "drugs": [
      "warfarin",
      "fluconazole"
     ],
     "category": "bleeding",
     "severity": "major",
     "why": "Fluconazole inhibits CYP2C9 -> INR rises sharply."
    },
    {
     "drugs": [
      "warfarin",
      "fluoxetine"
     ],
     "category": "bleeding",
     "severity": "moderate",
     "why": "SSRI antiplatelet effect plus mild CYP2C9 inhibition."
    },
    {
     "drugs": [
      "phenytoin",
      "atorvastatin"
     ],
     "category": "efficacy loss",
     "severity": "moderate",
     "why": "CYP3A4 induction lowers atorvastatin exposure."
    }
   ]
  },
  "L34": {
   "theme": "Duplicate alpha-2 agonists; CYP2D6 inhibition of atomoxetine; stimulant + SSRI; sedation and hypotension",
   "expected": [
    {
     "drugs": [
      "guanfacine",
      "clonidine"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Two central alpha-2 agonists: hypotension, bradycardia, sedation; abrupt stop -> rebound hypertension."
    },
    {
     "drugs": [
      "paroxetine",
      "atomoxetine"
     ],
     "category": "CYP inhibition",
     "severity": "major",
     "why": "Strong CYP2D6 inhibitor raises atomoxetine exposure 6-8x (poor-metabolizer phenotype). Strattera label: start 40 mg, go to 80 mg only after 4 weeks if needed."
    },
    {
     "drugs": [
      "lisdexamfetamine",
      "atomoxetine"
     ],
     "category": "duplicate therapy",
     "severity": "moderate",
     "why": "Two ADHD agents raising heart rate and BP; the combination is off-label."
    },
    {
     "drugs": [
      "lisdexamfetamine",
      "paroxetine"
     ],
     "category": "serotonin syndrome",
     "severity": "moderate",
     "why": "Vyvanse label: serotonin syndrome reported with SSRIs; amphetamine is also a CYP2D6 substrate."
    },
    {
     "drugs": [
      "quetiapine",
      "guanfacine",
      "clonidine"
     ],
     "category": "hypotension",
     "severity": "moderate",
     "why": "Additive hypotension and sedation."
    },
    {
     "drugs": [
      "lisdexamfetamine",
      "quetiapine"
     ],
     "category": "opposing pharmacology",
     "severity": "minor",
     "why": "Stimulant against a sedating antipsychotic."
    }
   ]
  },
  "L35": {
   "theme": "Two triptans; propranolol on rizatriptan; TCA + triptan; three-component barbiturate product; overuse",
   "expected": [
    {
     "drugs": [
      "sumatriptan",
      "rizatriptan"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Do not use two triptans within 24 hours; additive vasoconstriction, coronary spasm."
    },
    {
     "drugs": [
      "rizatriptan",
      "propranolol"
     ],
     "category": "CYP inhibition",
     "severity": "moderate",
     "why": "Propranolol raises rizatriptan plasma concentration about 70%; Maxalt label: use the 5 mg dose, max 15 mg/day."
    },
    {
     "drugs": [
      "sumatriptan",
      "rizatriptan",
      "amitriptyline"
     ],
     "category": "serotonin syndrome",
     "severity": "moderate",
     "why": "Triptan + tricyclic; FDA 2006 alert."
    },
    {
     "drugs": [
      "butalbital",
      "amitriptyline",
      "topiramate"
     ],
     "category": "CNS depression",
     "severity": "moderate",
     "why": "Barbiturate + tricyclic + topiramate: sedation, cognitive slowing."
    },
    {
     "drugs": [
      "butalbital/acetaminophen/caffeine"
     ],
     "category": "combination parsing",
     "severity": "moderate",
     "why": "Three components. Acetaminophen 1,950 mg/day max is under the ceiling; butalbital 300 mg/day used daily -> dependence and medication-overuse headache."
    }
   ],
   "totals": {
    "acetaminophen": "1,950 mg max",
    "butalbital": "300 mg max",
    "caffeine": "240 mg max"
   }
  },
  "L36": {
   "theme": "Opioid antagonist against a partial agonist; buprenorphine + benzodiazepine; a drug that should not flag",
   "expected": [
    {
     "drugs": [
      "buprenorphine/naloxone",
      "naltrexone"
     ],
     "category": "therapeutic antagonism",
     "severity": "contraindicated",
     "why": "Naltrexone blocks buprenorphine and precipitates withdrawal; Suboxone label names naltrexone. One of these prescriptions is an error."
    },
    {
     "drugs": [
      "buprenorphine",
      "clonazepam"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "Boxed warning. FDA also says MAT should not be withheld over it: flag and manage, do not stop buprenorphine."
    },
    {
     "drugs": [
      "buprenorphine",
      "gabapentin"
     ],
     "category": "respiratory depression",
     "severity": "major",
     "why": "Gabapentinoid + opioid; gabapentin misuse is common alongside buprenorphine."
    },
    {
     "drugs": [
      "buprenorphine",
      "quetiapine",
      "clonazepam",
      "gabapentin"
     ],
     "category": "CNS depression",
     "severity": "moderate",
     "why": "Additive sedation."
    }
   ],
   "should_not_flag": [
    "acamprosate (renally cleared; no pharmacokinetic or pharmacodynamic interaction here)"
   ]
  },
  "L37": {
   "theme": "P-gp inhibitors on dabigatran; dronedarone on digoxin, verapamil, simvastatin; rate-control stacking",
   "expected": [
    {
     "drugs": [
      "dabigatran",
      "dronedarone"
     ],
     "category": "P-gp",
     "severity": "major",
     "why": "Dronedarone raises dabigatran exposure about 1.7-2x -> bleeding. Pradaxa label: reduce to 75 mg twice daily when CrCl is 30-50 mL/min; avoid below that."
    },
    {
     "drugs": [
      "dabigatran",
      "verapamil"
     ],
     "category": "P-gp",
     "severity": "moderate",
     "why": "Verapamil raises dabigatran 50-180% depending on timing; take dabigatran at least 2 hours before verapamil."
    },
    {
     "drugs": [
      "digoxin",
      "dronedarone"
     ],
     "category": "digoxin toxicity",
     "severity": "major",
     "why": "Dronedarone raises digoxin about 2.5x; Multaq label: halve digoxin and monitor levels."
    },
    {
     "drugs": [
      "digoxin",
      "verapamil"
     ],
     "category": "digoxin toxicity",
     "severity": "moderate",
     "why": "Verapamil raises digoxin 50-75%."
    },
    {
     "drugs": [
      "dronedarone",
      "verapamil"
     ],
     "category": "bradycardia/AV block",
     "severity": "major",
     "why": "Verapamil (CYP3A4 inhibitor) raises dronedarone about 1.4x; additive AV block. Multaq label: start non-DHP calcium channel blockers low."
    },
    {
     "drugs": [
      "simvastatin",
      "dronedarone"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "moderate",
     "why": "Multaq label: simvastatin max 10 mg."
    },
    {
     "drugs": [
      "simvastatin",
      "verapamil"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "moderate",
     "why": "Zocor label: max 10 mg with verapamil."
    },
    {
     "drugs": [
      "furosemide",
      "digoxin",
      "dronedarone"
     ],
     "category": "electrolyte",
     "severity": "moderate",
     "why": "Hypokalemia potentiates digoxin toxicity and dronedarone QT/torsades."
    }
   ],
   "totals": {
    "digoxin": "0.125 mg = 125 mcg"
   }
  },
  "L38": {
   "theme": "Hidden duplicate: active metabolite prescribed alongside its parent; three antipsychotics",
   "expected": [
    {
     "drugs": [
      "risperidone",
      "paliperidone"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Paliperidone is 9-hydroxyrisperidone, risperidone's active metabolite. Prescribing both is one drug twice: 4 mg risperidone plus 6 mg paliperidone."
    },
    {
     "drugs": [
      "risperidone",
      "paliperidone",
      "olanzapine"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Three antipsychotics: additive EPS, QT, hyperprolactinemia, metabolic effects, NMS risk, no evidence of benefit."
    },
    {
     "drugs": [
      "benztropine",
      "olanzapine"
     ],
     "category": "anticholinergic burden",
     "severity": "moderate",
     "why": "Additive anticholinergic effects; benztropine can also mask tardive dyskinesia."
    },
    {
     "drugs": [
      "clonazepam",
      "olanzapine"
     ],
     "category": "CNS depression",
     "severity": "moderate",
     "why": "Additive sedation (the major warning is for IM olanzapine with a parenteral benzodiazepine)."
    }
   ],
   "totals": {
    "risperidone moiety": "4 mg risperidone + 6 mg paliperidone"
   },
   "should_not_flag": [
    "atorvastatin"
   ]
  },
  "L39": {
   "theme": "Macrolide on colchicine and simvastatin; diltiazem as a second CYP3A4/P-gp inhibitor; QT",
   "expected": [
    {
     "drugs": [
      "colchicine",
      "erythromycin"
     ],
     "category": "P-gp",
     "severity": "major",
     "why": "Erythromycin (CYP3A4 + P-gp inhibitor) raises colchicine to toxic levels; fatal cases reported. Colcrys label: cut the dose (prophylaxis 0.3 mg/day) and never combine with renal or hepatic impairment."
    },
    {
     "drugs": [
      "simvastatin",
      "erythromycin"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "contraindicated",
     "why": "Zocor label contraindicates erythromycin."
    },
    {
     "drugs": [
      "simvastatin",
      "diltiazem"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "major",
     "why": "Zocor label: max 10 mg simvastatin with diltiazem; 40 mg here."
    },
    {
     "drugs": [
      "colchicine",
      "diltiazem"
     ],
     "category": "P-gp",
     "severity": "moderate",
     "why": "Moderate CYP3A4/P-gp inhibitor; Colcrys label: dose reduction."
    },
    {
     "drugs": [
      "colchicine",
      "simvastatin"
     ],
     "category": "myopathy/rhabdomyolysis",
     "severity": "moderate",
     "why": "Additive myotoxicity, worse with both boosted by erythromycin."
    },
    {
     "drugs": [
      "erythromycin",
      "diltiazem"
     ],
     "category": "QT prolongation",
     "severity": "major",
     "why": "Diltiazem blocks erythromycin clearance; erythromycin + a CYP3A4 inhibitor carried about 5x the sudden cardiac death rate (Ray et al., NEJM 2004)."
    },
    {
     "drugs": [
      "furosemide",
      "erythromycin"
     ],
     "category": "electrolyte",
     "severity": "moderate",
     "why": "Hypokalemia amplifies QT risk."
    }
   ],
   "should_not_flag": [
    "allopurinol"
   ]
  },
  "L40": {
   "theme": "Three bedtime hypnotics plus a benzodiazepine; SSRI at its maximum with trazodone",
   "expected": [
    {
     "drugs": [
      "trazodone",
      "suvorexant",
      "zolpidem",
      "alprazolam"
     ],
     "category": "duplicate therapy",
     "severity": "major",
     "why": "Three sedative-hypnotics at bedtime plus a benzodiazepine: next-day impairment, complex sleep behaviors (zolpidem boxed warning), respiratory depression. Belsomra label: reduce dose with other CNS depressants."
    },
    {
     "drugs": [
      "trazodone",
      "sertraline"
     ],
     "category": "serotonin syndrome",
     "severity": "moderate",
     "why": "Both serotonergic; sertraline at its 200 mg labeled maximum."
    },
    {
     "drugs": [
      "trazodone"
     ],
     "category": "QT prolongation",
     "severity": "minor",
     "why": "Dose-related; 100 mg alone is low risk. Flag only if the app tracks QT burden."
    },
    {
     "drugs": [
      "sertraline"
     ],
     "category": "dose ceiling",
     "severity": "minor",
     "why": "200 mg is the labeled maximum, not over it; a ceiling check should pass."
    }
   ],
   "totals": {
    "alprazolam": "1.5 mg max"
   }
  },
  "L41": {
   "theme": "Data-entry traps: brand and generic of one drug; same dose in different units; one ingredient under two brands",
   "expected": [
    {
     "drugs": [
      "sertraline",
      "sertraline"
     ],
     "category": "duplicate entry",
     "severity": "major",
     "why": "Same drug entered twice, once as Zoloft and once as generic. Either a data-entry duplicate or a real 100 mg/day. The app should ask, not silently sum or silently drop."
    },
    {
     "drugs": [
      "levothyroxine",
      "levothyroxine"
     ],
     "category": "unit normalization",
     "severity": "major",
     "why": "0.1 mg = 100 mcg. Same drug, same dose, twice. Units must be normalized before deduplication."
    },
    {
     "drugs": [
      "ibuprofen",
      "ibuprofen"
     ],
     "category": "dose ceiling",
     "severity": "major",
     "why": "One molecule under two brands: 2,400 + 800 = 3,200 mg/day, exactly the prescription ceiling."
    },
    {
     "drugs": [
      "sertraline",
      "ibuprofen"
     ],
     "category": "bleeding",
     "severity": "moderate",
     "why": "SSRI + NSAID GI bleeding."
    }
   ],
   "totals": {
    "sertraline": "100 mg if both lines are real",
    "levothyroxine": "200 mcg if both lines are real (0.1 mg + 100 mcg)",
    "ibuprofen": "3,200 mg"
   },
   "should_not_flag": [
    "levothyroxine with ibuprofen",
    "levothyroxine with sertraline at moderate or above"
   ]
  }
 }
}
```
