# Drug Interaction Screen — redesign live QA re-run, 2026-09-22

Target: https://rx-label-search-aidancolvins-projects.vercel.app/
Driven with a script adapted from `results/run_patients.py` (read-only, not modified) for the redesigned UI: no "Check interactions" button and no "Medication list" textarea exist anymore, so each drug is added with one Enter press instead of one textarea fill plus one button click. See `results/rerun_2026-09-22/README.md`.
Result: 10 / 10 patients returned interaction data successfully.
Entries resolved to a label across all 10 patients: 58 of 60 (compare to 11 of 60 in the original `results/report.md`).
Interaction alerts fired, any patient: 4 (compare to 0 in the original report).

| Patient | Drugs | Alerts | Unresolved | Result |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 6 | 2 | 0 | PASS |
| 2 | 6 | 0 | 0 | PASS |
| 3 | 6 | 0 | 0 | PASS |
| 4 | 6 | 0 | 0 | PASS |
| 5 | 6 | 0 | 0 | PASS |
| 6 | 6 | 2 | 0 | PASS |
| 7 | 6 | 0 | 1 | PASS |
| 8 | 6 | 0 | 0 | PASS |
| 9 | 6 | 0 | 0 | PASS |
| 10 | 6 | 0 | 1 | PASS |


## Patient 1 — PASS

**Medications submitted:** Alprazolam 1 mg 3 times daily, Zolpidem 10 mg 1 time daily, Lisinopril 10 mg 1 time daily, Atorvastatin 20 mg 1 time daily, Sertraline 50 mg 1 time daily, Omeprazole 20 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
- [group/T15] CNS Depression Risk shared by 2 drugs — tier: Boxed warning (heuristic)
- [group/T16] QT Prolongation Risk shared by 2 drugs — tier: Warning (heuristic)
```

**Unresolved entries:** (none)

**Screenshot:** `results/rerun_2026-09-22/patient_01.png`

**Results panel text (verbatim):**
```
2 alerts

6 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.

Boxed warning (heuristic)
CNS Depression Risk shared by 2 drugs

Alprazolam, Zolpidem

WARNING: RISKS FROM CONCOMITANT USE WITH OPIOIDS; ABUSE, MISUSE, AND ADDICTION; and DEPENDENCE AND WITHDRAWAL REACTIONS Concomitant use of benzodiazepines and opioids may result in profound sedation, respiratory depression, coma, and death.
Alprazolam, Boxed Warning section
DailyMed
Show 1 more label sentences
Warning (heuristic)
QT Prolongation Risk shared by 2 drugs

Sertraline, Omeprazole

QTc Prolongation: Sertraline hydrochloride should be used with caution in patients with risk factors for QTc prolongation.
Sertraline, Warnings and Precautions section
DailyMed
Show 1 more label sentences
```

## Patient 2 — PASS

**Medications submitted:** Metformin 500 mg 2 times daily, Amlodipine 5 mg 1 time daily, Simvastatin 20 mg 1 time daily, Losartan 50 mg 1 time daily, Gabapentin 300 mg 3 times daily, Levothyroxine 50 mcg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** (none)

**Screenshot:** `results/rerun_2026-09-22/patient_02.png`

**Results panel text (verbatim):**
```
No warning found in the labels checked.

6 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.
```

## Patient 3 — PASS

**Medications submitted:** Hydrochlorothiazide 25 mg 1 time daily, Metoprolol Succinate 50 mg 1 time daily, Escitalopram 10 mg 1 time daily, Pantoprazole 40 mg 1 time daily, Montelukast 10 mg 1 time daily, Rosuvastatin 10 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** (none)

**Screenshot:** `results/rerun_2026-09-22/patient_03.png`

**Results panel text (verbatim):**
```
No warning found in the labels checked.

6 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.
```

## Patient 4 — PASS

**Medications submitted:** Glipizide 5 mg 2 times daily, Valsartan 80 mg 1 time daily, Pravastatin 20 mg 1 time daily, Duloxetine 30 mg 1 time daily, Famotidine 20 mg 2 times daily, Albuterol 90 mcg 2 puffs as needed

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** (none)

**Screenshot:** `results/rerun_2026-09-22/patient_04.png`

**Results panel text (verbatim):**
```
No warning found in the labels checked.

6 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.
```

## Patient 5 — PASS

**Medications submitted:** Carvedilol 6.25 mg 2 times daily, Furosemide 20 mg 1 time daily, Spironolactone 25 mg 1 time daily, Warfarin 5 mg 1 time daily, Digoxin 125 mcg 1 time daily, Potassium Chloride 20 mEq 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** (none)

**Screenshot:** `results/rerun_2026-09-22/patient_05.png`

**Results panel text (verbatim):**
```
No warning found in the labels checked.

6 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.
```

## Patient 6 — PASS

**Medications submitted:** Bupropion XL 150 mg 1 time daily, Trazodone 50 mg 1 time daily at bedtime, Amoxicillin 500 mg 3 times daily, Ibuprofen 600 mg 3 times daily as needed, Cyclobenzaprine 10 mg 3 times daily as needed, Fluticasone 50 mcg 2 sprays daily

**HTTP status:** 200

**Alerts returned:**
```
- [group/T14] Serotonin Syndrome Risk shared by 2 drugs — tier: Warning (heuristic)
- [group/T15] CNS Depression Risk shared by 2 drugs — tier: Warning (heuristic)
```

**Unresolved entries:** (none)

**Screenshot:** `results/rerun_2026-09-22/patient_06.png`

**Results panel text (verbatim):**
```
2 alerts

6 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.

Warning (heuristic)
Serotonin Syndrome Risk shared by 2 drugs

Trazodone HCL, CYCLOBENZAPRINE

Serotonin Syndrome: Increased risk when co-administered with other serotonergic agents (e.g., SSRI, SNRI, triptans), but also when taken alone.
Trazodone HCL, Warnings and Precautions section
DailyMed
Show 1 more label sentences
Warning (heuristic)
CNS Depression Risk shared by 2 drugs

Trazodone HCL, CYCLOBENZAPRINE

Cyclobenzaprine may enhance the effects of alcohol, barbiturates, and other CNS depressants.
CYCLOBENZAPRINE, Warnings section
DailyMed
Show 1 more label sentences
```

## Patient 7 — PASS

**Medications submitted:** Empagliflozin 10 mg 1 time daily, Telmisartan 40 mg 1 time daily, Ezetimibe 10 mg 1 time daily, Venlafaxine ER 75 mg 1 time daily, Esomeprazole 40 mg 1 time daily, Meloxicam 15 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Venlafaxine ER 75 mg 1 time daily" (two or more names are equally close)

**Screenshot:** `results/rerun_2026-09-22/patient_07.png`

**Results panel text (verbatim):**
```
No warning found in the labels checked.

5 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.
```

## Patient 8 — PASS

**Medications submitted:** Diltiazem ER 180 mg 1 time daily, Apixaban 5 mg 2 times daily, Allopurinol 100 mg 1 time daily, Tamsulosin 0.4 mg 1 time daily, Finasteride 5 mg 1 time daily, Acetaminophen 500 mg 4 times daily as needed

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** (none)

**Screenshot:** `results/rerun_2026-09-22/patient_08.png`

**Results panel text (verbatim):**
```
No warning found in the labels checked.

6 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.
```

## Patient 9 — PASS

**Medications submitted:** Sitagliptin 100 mg 1 time daily, Nifedipine ER 30 mg 1 time daily, Lovastatin 20 mg 1 time daily, Fluoxetine 20 mg 1 time daily, Famotidine 40 mg 1 time daily, Cetirizine 10 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** (none)

**Screenshot:** `results/rerun_2026-09-22/patient_09.png`

**Results panel text (verbatim):**
```
No warning found in the labels checked.

6 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.
```

## Patient 10 — PASS

**Medications submitted:** Ramipril 5 mg 1 time daily, Chlorthalidone 25 mg 1 time daily, Pitavastatin 2 mg 1 time daily, Paroxetine 20 mg 1 time daily, Dicyclomine 20 mg 4 times daily as needed, Loratadine 10 mg 1 time daily

**HTTP status:** 200

**Alerts returned:**
```
No warning found in the labels checked.
```

**Unresolved entries:** "Paroxetine 20 mg 1 time daily" (the name is used by more than one ingredient set)

**Screenshot:** `results/rerun_2026-09-22/patient_10.png`

**Results panel text (verbatim):**
```
No warning found in the labels checked.

5 of 6 medications checked

Results reflect FDA label text as of 2026-09-22. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.
```
