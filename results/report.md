# Drug Interaction Screen — live QA report

**Target:** https://rx-label-search-aidancolvins-projects.vercel.app/
**Method:** headless Chromium (Playwright), driving the real page controls by accessible role and name, with network interception attached before any interaction.
**Discovered endpoint:** `POST /api/check`, JSON body `{"medications": <text>, "use_rxnorm": true}`, found by intercepting the network request fired when the "Check interactions" button was clicked for Patient 1. Used directly (via `page.expect_response`) for all 10 patients so the reported alert and resolution data comes from the parsed JSON response, not scraped page text; a full-page screenshot and the rendered results-panel text were still captured for every patient from the live browser session.

## Pass/fail definition used

Per the task's own definition — **did the endpoint return any interaction data, versus erroring or returning nothing** — all 10 of 10 patients PASS: every submission returned HTTP 200 with a well-formed JSON response containing a medication table, an alerts list, and an unresolved-entries list.

## Critical finding: the checker could not evaluate most of these patients for interactions

Read past the 10/10 in the table above. **Zero interaction alerts fired for any of the 10 patients, on any drug pair.** That is not because these medication lists are interaction-free — several are textbook polypharmacy risks (Patient 1: alprazolam + zolpidem + sertraline, three CNS/serotonergic drugs; Patient 5: warfarin + digoxin + spironolactone + potassium chloride, a classic high-risk cardiac-renal combination; Patient 6: bupropion + trazodone + cyclobenzaprine, serotonergic and CNS-depressant risk). It is because **82% of the drug entries across all 10 patients never resolved to a label in the first place**, so the checker had nothing to compare.

| Metric | Value |
| :--- | ---: |
| Total drug entries submitted (10 patients × 6 drugs) | 60 |
| Entries resolved to a label | 11 (18%) |
| Entries unresolved | 49 (82%) |
| Interaction alerts fired, any patient | 0 |

### Root cause: two reproducible parsing bugs in the medication-list entry, isolated with direct API calls (`use_rxnorm: false` to remove RxNorm network variability)

**Bug 1 — "N time daily" (singular "time", used for a count of 1) is not recognized as a frequency phrase at all.** The parser recognizes "N times daily" (plural), "once/twice/three times/four times daily" (word forms), and "daily" alone, but not the numeral form "1 time daily" that all 10 of these synthetic patients use for every once-daily drug. When it fails to match, the leftover "1 time" text stays attached to the drug name, and name resolution fails:

```
POST /api/check {"medications":"Alprazolam","use_rxnorm":false}
  → resolves cleanly to ALPRAZOLAM

POST /api/check {"medications":"Alprazolam 1 mg 3 times daily","use_rxnorm":false}
  → resolves cleanly to ALPRAZOLAM (plural "times" is recognized)

POST /api/check {"medications":"Zolpidem 10 mg 1 time daily","use_rxnorm":false}
  → "Zolpidem 10 mg 1 time daily" → Not resolved, reason: "no dictionary name is close enough"
  (Zolpidem alone resolves without issue; "1 time daily" is what breaks it)
```

**Bug 2 — a common trailing qualifier after a correctly recognized frequency ("as needed", "at bedtime") is not stripped, and breaks resolution even when the frequency phrase itself matched.** Six of the sixty entries across these ten patients use "as needed" or "at bedtime" (Patients 4, 6, 8, 10):

```
POST /api/check {"medications":"Ibuprofen 600 mg 3 times daily as needed","use_rxnorm":false}
  → Not resolved, reason: "no dictionary name is close enough"
  (the plural "3 times daily" phrase matches fine on its own — see Bug 1's Alprazolam
  example above — so "as needed" trailing it is what breaks this one)

POST /api/check {"medications":"Dicyclomine","use_rxnorm":false}
  → resolves cleanly to DICYCLOMINE HYDROCHLORIDE

POST /api/check {"medications":"Dicyclomine 20 mg 4 times daily as needed","use_rxnorm":false}
  → Not resolved (same "as needed" pattern)
```

**In live production** (`use_rxnorm: true`, the page's actual default), RxNorm's approximate-match fallback occasionally recovers a "1 time daily" entry anyway — Patient 1's "Lisinopril 10 mg 1 time daily" resolved live via the chain "Lisinopril 1 time → lisinopril 1 MG/ML → lisinopril → LISINOPRIL" (see `patient_01.png`), while "Zolpidem 10 mg 1 time daily" in the same request did not. This makes the failure inconsistent and drug-dependent rather than a clean, predictable behavior: whether a given "1 time daily" or "as needed" entry survives depends on whether RxNorm's fuzzy search happens to find the base name underneath the leftover noise, not on anything about the entry itself.

**What this means for the question asked:** the live checker's alert logic (group alerts, pair alerts, duplication flags) was not exercised by this test, because the entries it needed to compare almost never made it into the medication table. This QA run cannot confirm the checker "actually detects drug-drug interactions" one way or the other for these patients — it can only confirm that, for medication lists phrased the way these ten were, it mostly fails before reaching that step. A retest with "3 times daily"-style plural phrasing (or bare "daily") and without trailing qualifiers would be needed to separately test the interaction-detection logic itself.

## Summary table

| Patient | Drugs | Alerts | Unresolved | Result |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 6 | 0 | 4 | PASS |
| 2 | 6 | 0 | 4 | PASS |
| 3 | 6 | 0 | 6 | PASS |
| 4 | 6 | 0 | 4 | PASS |
| 5 | 6 | 0 | 4 | PASS |
| 6 | 6 | 0 | 5 | PASS |
| 7 | 6 | 0 | 6 | PASS |
| 8 | 6 | 0 | 4 | PASS |
| 9 | 6 | 0 | 6 | PASS |
| 10 | 6 | 0 | 6 | PASS |

## Patient 1 — PASS

**Medications submitted:** Alprazolam 1 mg 3 times daily, Zolpidem 10 mg 1 time daily, Lisinopril 10 mg 1 time daily, Atorvastatin 20 mg 1 time daily, Sertraline 50 mg 1 time daily, Omeprazole 20 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Zolpidem 10 mg 1 time daily" (RxNorm found no close name); "Atorvastatin 20 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Sertraline 50 mg 1 time daily" (RxNorm found no close name); "Omeprazole 20 mg 1 time daily" (RxNorm found no close name)

**Screenshot:** `results/patient_01.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Alprazolam 1 mg 3 times daily	Alprazolam → ALPRAZOLAM	ALPRAZOLAM	alprazolam	Alprazolam	Benzodiazepine [EPC]	ORAL	IV	3 mg	T01T02T04T05T07T08T11T12T13T15
Zolpidem 10 mg 1 time daily	Not resolved				Not listed on label.			10 mg	
Lisinopril 10 mg 1 time daily	Lisinopril 1 time → lisinopril 1 MG/ML → lisinopril → LISINOPRIL	LISINOPRIL	lisinopril	Lisinopril	Not listed on label.	ORAL		10 mg	T01T02T03T04T06T08T11T13T17
Atorvastatin 20 mg 1 time daily	Not resolved				Not listed on label.			20 mg	
Sertraline 50 mg 1 time daily	Not resolved				Not listed on label.			50 mg	
Omeprazole 20 mg 1 time daily	Not resolved				Not listed on label.			20 mg	

No warning found in the labels checked.

Unresolved entries
"Zolpidem 10 mg 1 time daily" — RxNorm found no close name (candidates: ZOLPIDEM)
"Atorvastatin 20 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Sertraline 50 mg 1 time daily" — RxNorm found no close name (candidates: sertraline)
"Omeprazole 20 mg 1 time daily" — RxNorm found no close name (candidates: Omeprazole; (-)-omeprazole)
```

## Patient 2 — PASS

**Medications submitted:** Metformin 500 mg 2 times daily, Amlodipine 5 mg 1 time daily, Simvastatin 20 mg 1 time daily, Losartan 50 mg 1 time daily, Gabapentin 300 mg 3 times daily, Levothyroxine 50 mcg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Amlodipine 5 mg 1 time daily" (RxNorm found no close name); "Simvastatin 20 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Losartan 50 mg 1 time daily" (RxNorm found no close name); "Levothyroxine 50 mcg 1 time daily" (RxNorm found no close name)

**Screenshot:** `results/patient_02.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Metformin 500 mg 2 times daily	Metformin → METFORMIN HYDROCHLORIDE	METFORMIN ER 500 MG	metformin	Metformin	Not listed on label.	ORAL		1000 mg	T01T02T04T06T08T11
Amlodipine 5 mg 1 time daily	Not resolved				Not listed on label.			5 mg	
Simvastatin 20 mg 1 time daily	Not resolved				Not listed on label.			20 mg	
Losartan 50 mg 1 time daily	Not resolved				Not listed on label.			50 mg	
Gabapentin 300 mg 3 times daily	Gabapentin → GABAPENTIN	GABAPENTIN	gabapentin	gabapentin	Not listed on label.	ORAL		900 mg	T02T04T05T06T08T11T13T15
Levothyroxine 50 mcg 1 time daily	Not resolved				Not listed on label.			50 mcg	

No warning found in the labels checked.

Unresolved entries
"Amlodipine 5 mg 1 time daily" — RxNorm found no close name
"Simvastatin 20 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Losartan 50 mg 1 time daily" — RxNorm found no close name (candidates: losartan)
"Levothyroxine 50 mcg 1 time daily" — RxNorm found no close name
```

## Patient 3 — PASS

**Medications submitted:** Hydrochlorothiazide 25 mg 1 time daily, Metoprolol Succinate 50 mg 1 time daily, Escitalopram 10 mg 1 time daily, Pantoprazole 40 mg 1 time daily, Montelukast 10 mg 1 time daily, Rosuvastatin 10 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Hydrochlorothiazide 25 mg 1 time daily" (RxNorm found no close name); "Metoprolol Succinate 50 mg 1 time daily" (two or more names are equally close); "Escitalopram 10 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Pantoprazole 40 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Montelukast 10 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Rosuvastatin 10 mg 1 time daily" (RxNorm lists no ingredient for the matched concept)

**Screenshot:** `results/patient_03.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Hydrochlorothiazide 25 mg 1 time daily	Not resolved				Not listed on label.			25 mg	
Metoprolol Succinate 50 mg 1 time daily	Not resolved				Not listed on label.			50 mg	
Escitalopram 10 mg 1 time daily	Not resolved				Not listed on label.			10 mg	
Pantoprazole 40 mg 1 time daily	Not resolved				Not listed on label.			40 mg	
Montelukast 10 mg 1 time daily	Not resolved				Not listed on label.			10 mg	
Rosuvastatin 10 mg 1 time daily	Not resolved				Not listed on label.			10 mg	

No warning found in the labels checked.

Unresolved entries
"Hydrochlorothiazide 25 mg 1 time daily" — RxNorm found no close name
"Metoprolol Succinate 50 mg 1 time daily" — two or more names are equally close (candidates: Metoprolol Succinate ER → METOPROLOL SUCCINATE; Metoprolol succinate → METOPROLOL SUCCINATE | METOPROLOL TARTRATE)
"Escitalopram 10 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Pantoprazole 40 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Montelukast 10 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Rosuvastatin 10 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
```

## Patient 4 — PASS

**Medications submitted:** Glipizide 5 mg 2 times daily, Valsartan 80 mg 1 time daily, Pravastatin 20 mg 1 time daily, Duloxetine 30 mg 1 time daily, Famotidine 20 mg 2 times daily, Albuterol 90 mcg 2 puffs as needed

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Valsartan 80 mg 1 time daily" (RxNorm found no close name); "Pravastatin 20 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Duloxetine 30 mg 1 time daily" (RxNorm found no close name); "Albuterol 90 mcg 2 puffs as needed" (RxNorm found no close name)

**Screenshot:** `results/patient_04.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Glipizide 5 mg 2 times daily	Glipizide → GLIPIZIDE	GLIPIZIDE	glipizide	Glipizide	Sulfonylurea [EPC]	ORAL		10 mg	T02T04T08
Valsartan 80 mg 1 time daily	Not resolved				Not listed on label.			80 mg	
Pravastatin 20 mg 1 time daily	Not resolved				Not listed on label.			20 mg	
Duloxetine 30 mg 1 time daily	Not resolved				Not listed on label.			30 mg	
Famotidine 20 mg 2 times daily	Famotidine → FAMOTIDINE	FAMOTIDINE	famotidine	Famotidine	Histamine-2 Receptor Antagonist [EPC]	ORAL		40 mg	T02T03T06T08T11T13T17
Albuterol 90 mcg 2 puffs as needed	Not resolved				Not listed on label.				

No warning found in the labels checked.

Unresolved entries
"Valsartan 80 mg 1 time daily" — RxNorm found no close name (candidates: Valsartan)
"Pravastatin 20 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Duloxetine 30 mg 1 time daily" — RxNorm found no close name (candidates: duloxetine)
"Albuterol 90 mcg 2 puffs as needed" — RxNorm found no close name (candidates: albuterol 2 MG)
```

## Patient 5 — PASS

**Medications submitted:** Carvedilol 6.25 mg 2 times daily, Furosemide 20 mg 1 time daily, Spironolactone 25 mg 1 time daily, Warfarin 5 mg 1 time daily, Digoxin 125 mcg 1 time daily, Potassium Chloride 20 mEq 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Furosemide 20 mg 1 time daily" (RxNorm returned more than one equally ranked concept); "Spironolactone 25 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Warfarin 5 mg 1 time daily" (RxNorm found no close name); "Digoxin 125 mcg 1 time daily" (RxNorm found no close name)

**Screenshot:** `results/patient_05.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Carvedilol 6.25 mg 2 times daily	Carvedilol → CARVEDILOL	CARVEDILOL	carvedilol	Carvedilol	alpha-Adrenergic Blocker [EPC], beta-Adrenergic Blocker [EPC]	ORAL		12.5 mg	T02T04T08
Furosemide 20 mg 1 time daily	Not resolved				Not listed on label.			20 mg	
Spironolactone 25 mg 1 time daily	Not resolved				Not listed on label.			25 mg	
Warfarin 5 mg 1 time daily	Not resolved				Not listed on label.			5 mg	
Digoxin 125 mcg 1 time daily	Not resolved				Not listed on label.			125 mcg	
Potassium Chloride 20 mEq 1 time daily	Potassium Chloride 20 mEq 1 time → potassium chloride 20 MEQ → potassium chloride → POTASSIUM CHLORIDE	POTASSIUM CHLORIDE EXTENDED-RELEASE	potassium chloride	Potassium Chloride Extended-release	Not listed on label.	ORAL			T02T08T13T17

No warning found in the labels checked.

Unresolved entries
"Furosemide 20 mg 1 time daily" — RxNorm returned more than one equally ranked concept (candidates: furosemide 1.8 MG; furosemide 1 MG/ML)
"Spironolactone 25 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Warfarin 5 mg 1 time daily" — RxNorm found no close name (candidates: (-)-Warfarin; warfarin)
"Digoxin 125 mcg 1 time daily" — RxNorm found no close name (candidates: Digoxin)
```

## Patient 6 — PASS

**Medications submitted:** Bupropion XL 150 mg 1 time daily, Trazodone 50 mg 1 time daily at bedtime, Amoxicillin 500 mg 3 times daily, Ibuprofen 600 mg 3 times daily as needed, Cyclobenzaprine 10 mg 3 times daily as needed, Fluticasone 50 mcg 2 sprays daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Bupropion XL 150 mg 1 time daily" (RxNorm found no close name); "Trazodone 50 mg 1 time daily at bedtime" (RxNorm found no close name); "Ibuprofen 600 mg 3 times daily as needed" (RxNorm found no close name); "Cyclobenzaprine 10 mg 3 times daily as needed" (RxNorm lists no ingredient for the matched concept); "Fluticasone 50 mcg 2 sprays daily" (RxNorm found no close name)

**Screenshot:** `results/patient_06.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Bupropion XL 150 mg 1 time daily	Not resolved				Not listed on label.			150 mg	
Trazodone 50 mg 1 time daily at bedtime	Not resolved				Not listed on label.			50 mg	
Amoxicillin 500 mg 3 times daily	Amoxicillin → AMOXICILLIN	AMOXICILLIN	amoxicillin	AMOXICILLIN	Not listed on label.	ORAL		1500 mg	T02T06T08T11
Ibuprofen 600 mg 3 times daily as needed	Not resolved				Not listed on label.			1800 mg	
Cyclobenzaprine 10 mg 3 times daily as needed	Not resolved				Not listed on label.			30 mg	
Fluticasone 50 mcg 2 sprays daily	Not resolved				Not listed on label.			50 mcg	

No warning found in the labels checked.

Unresolved entries
"Bupropion XL 150 mg 1 time daily" — RxNorm found no close name
"Trazodone 50 mg 1 time daily at bedtime" — RxNorm found no close name
"Ibuprofen 600 mg 3 times daily as needed" — RxNorm found no close name
"Cyclobenzaprine 10 mg 3 times daily as needed" — RxNorm lists no ingredient for the matched concept
"Fluticasone 50 mcg 2 sprays daily" — RxNorm found no close name (candidates: fluticasone Metered Dose Nasal Spray)
```

## Patient 7 — PASS

**Medications submitted:** Empagliflozin 10 mg 1 time daily, Telmisartan 40 mg 1 time daily, Ezetimibe 10 mg 1 time daily, Venlafaxine ER 75 mg 1 time daily, Esomeprazole 40 mg 1 time daily, Meloxicam 15 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Empagliflozin 10 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Telmisartan 40 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Ezetimibe 10 mg 1 time daily" (RxNorm found no close name); "Venlafaxine ER 75 mg 1 time daily" (RxNorm found no close name); "Esomeprazole 40 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Meloxicam 15 mg 1 time daily" (RxNorm found no close name)

**Screenshot:** `results/patient_07.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Empagliflozin 10 mg 1 time daily	Not resolved				Not listed on label.			10 mg	
Telmisartan 40 mg 1 time daily	Not resolved				Not listed on label.			40 mg	
Ezetimibe 10 mg 1 time daily	Not resolved				Not listed on label.			10 mg	
Venlafaxine ER 75 mg 1 time daily	Not resolved				Not listed on label.			75 mg	
Esomeprazole 40 mg 1 time daily	Not resolved				Not listed on label.			40 mg	
Meloxicam 15 mg 1 time daily	Not resolved				Not listed on label.			15 mg	

No warning found in the labels checked.

Unresolved entries
"Empagliflozin 10 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Telmisartan 40 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Ezetimibe 10 mg 1 time daily" — RxNorm found no close name (candidates: Ezetimibe)
"Venlafaxine ER 75 mg 1 time daily" — RxNorm found no close name
"Esomeprazole 40 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Meloxicam 15 mg 1 time daily" — RxNorm found no close name (candidates: Meloxicam)
```

## Patient 8 — PASS

**Medications submitted:** Diltiazem ER 180 mg 1 time daily, Apixaban 5 mg 2 times daily, Allopurinol 100 mg 1 time daily, Tamsulosin 0.4 mg 1 time daily, Finasteride 5 mg 1 time daily, Acetaminophen 500 mg 4 times daily as needed

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Diltiazem ER 180 mg 1 time daily" (RxNorm found no close name); "Allopurinol 100 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Tamsulosin 0.4 mg 1 time daily" (RxNorm found no close name); "Acetaminophen 500 mg 4 times daily as needed" (RxNorm found no close name)

**Screenshot:** `results/patient_08.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Diltiazem ER 180 mg 1 time daily	Not resolved				Not listed on label.			180 mg	
Apixaban 5 mg 2 times daily	Apixaban → APIXABAN	APIXABAN	apixaban	ELIQUIS	Factor Xa Inhibitor [EPC]	ORAL		10 mg	T01T02T03T04T05T06T08T09T11T12
Allopurinol 100 mg 1 time daily	Not resolved				Not listed on label.			100 mg	
Tamsulosin 0.4 mg 1 time daily	Not resolved				Not listed on label.			0.4 mg	
Finasteride 5 mg 1 time daily	Finasteride 1 time → finasteride 1 MG → finasteride → FINASTERIDE	FINASTERIDE	finasteride	Finasteride	5-alpha Reductase Inhibitor [EPC]	ORAL		5 mg	T02T03T08
Acetaminophen 500 mg 4 times daily as needed	Not resolved				Not listed on label.			2000 mg	

No warning found in the labels checked.

Unresolved entries
"Diltiazem ER 180 mg 1 time daily" — RxNorm found no close name
"Allopurinol 100 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Tamsulosin 0.4 mg 1 time daily" — RxNorm found no close name (candidates: (-)-tamsulosin)
"Acetaminophen 500 mg 4 times daily as needed" — RxNorm found no close name (candidates: Acetaminophen)
```

## Patient 9 — PASS

**Medications submitted:** Sitagliptin 100 mg 1 time daily, Nifedipine ER 30 mg 1 time daily, Lovastatin 20 mg 1 time daily, Fluoxetine 20 mg 1 time daily, Famotidine 40 mg 1 time daily, Cetirizine 10 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Sitagliptin 100 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Nifedipine ER 30 mg 1 time daily" (RxNorm found no close name); "Lovastatin 20 mg 1 time daily" (RxNorm found no close name); "Fluoxetine 20 mg 1 time daily" (RxNorm found no close name); "Famotidine 40 mg 1 time daily" (RxNorm found no close name); "Cetirizine 10 mg 1 time daily" (more than one collection ingredient set matches)

**Screenshot:** `results/patient_09.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Sitagliptin 100 mg 1 time daily	Not resolved				Not listed on label.			100 mg	
Nifedipine ER 30 mg 1 time daily	Not resolved				Not listed on label.			30 mg	
Lovastatin 20 mg 1 time daily	Not resolved				Not listed on label.			20 mg	
Fluoxetine 20 mg 1 time daily	Not resolved				Not listed on label.			20 mg	
Famotidine 40 mg 1 time daily	Not resolved				Not listed on label.			40 mg	
Cetirizine 10 mg 1 time daily	Not resolved				Not listed on label.			10 mg	

No warning found in the labels checked.

Unresolved entries
"Sitagliptin 100 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Nifedipine ER 30 mg 1 time daily" — RxNorm found no close name
"Lovastatin 20 mg 1 time daily" — RxNorm found no close name (candidates: Lovastatin)
"Fluoxetine 20 mg 1 time daily" — RxNorm found no close name (candidates: fluoxetine)
"Famotidine 40 mg 1 time daily" — RxNorm found no close name (candidates: Famotidine)
"Cetirizine 10 mg 1 time daily" — more than one collection ingredient set matches (candidates: CETIRIZINE HYDROCHLORIDE; CETIRIZINE)
```

## Patient 10 — PASS

**Medications submitted:** Ramipril 5 mg 1 time daily, Chlorthalidone 25 mg 1 time daily, Pitavastatin 2 mg 1 time daily, Paroxetine 20 mg 1 time daily, Dicyclomine 20 mg 4 times daily as needed, Loratadine 10 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Ramipril 5 mg 1 time daily" (RxNorm found no close name); "Chlorthalidone 25 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Pitavastatin 2 mg 1 time daily" (RxNorm lists no ingredient for the matched concept); "Paroxetine 20 mg 1 time daily" (RxNorm found no close name); "Dicyclomine 20 mg 4 times daily as needed" (RxNorm found no close name); "Loratadine 10 mg 1 time daily" (RxNorm found no close name)

**Screenshot:** `results/patient_10.png`

**Results panel text (verbatim):**
```
As entered	Matched name	Generic	Base ingredients	Brand	FDA class	Route	DEA schedule	Daily total	PDLA tags
Ramipril 5 mg 1 time daily	Not resolved				Not listed on label.			5 mg	
Chlorthalidone 25 mg 1 time daily	Not resolved				Not listed on label.			25 mg	
Pitavastatin 2 mg 1 time daily	Not resolved				Not listed on label.			2 mg	
Paroxetine 20 mg 1 time daily	Not resolved				Not listed on label.			20 mg	
Dicyclomine 20 mg 4 times daily as needed	Not resolved				Not listed on label.			80 mg	
Loratadine 10 mg 1 time daily	Not resolved				Not listed on label.			10 mg	

No warning found in the labels checked.

Unresolved entries
"Ramipril 5 mg 1 time daily" — RxNorm found no close name (candidates: Ramipril)
"Chlorthalidone 25 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Pitavastatin 2 mg 1 time daily" — RxNorm lists no ingredient for the matched concept
"Paroxetine 20 mg 1 time daily" — RxNorm found no close name (candidates: paroxetine)
"Dicyclomine 20 mg 4 times daily as needed" — RxNorm found no close name (candidates: dicyclomine)
"Loratadine 10 mg 1 time daily" — RxNorm found no close name
```
