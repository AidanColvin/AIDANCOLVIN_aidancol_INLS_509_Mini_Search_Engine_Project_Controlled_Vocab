# Rulebook coverage

Rows are Section 3 of TEST_PACK.md. A row applies to a list when the list holds drugs from each side of the row (different entries, different drugs).
"Flagged" means the site showed an alert holding at least two of the row's drugs. "Named" means that alert's text also names the row's syndrome.
In the list column, a bare ID means named, ~ means flagged but syndrome not named, ✗ means not flagged.

| Row | Combination | Lists it applies to | Flagged | Named | Lists |
|---|---|---|---|---|---|
| 1 | Opioid + benzodiazepine | 0 | 0 | 0 | — |
| 2 | Opioid + gabapentinoid | 0 | 0 | 0 | — |
| 3 | Oxycodone/fentanyl/methadone + strong CYP3A4 inhibitor | 0 | 0 | 0 | — |
| 4 | Tizanidine + ciprofloxacin or fluvoxamine | 1 | 1 | 1 | G02 |
| 5 | Clozapine + fluvoxamine or ciprofloxacin | 0 | 0 | 0 | — |
| 6 | Anticholinergic burden | 0 | 0 | 0 | — |
| 7 | SSRI/SNRI or MAOI + serotonergic drug | 0 | 0 | 0 | — |
| 8 | Tramadol/bupropion + threshold-lowering drug or CYP2D6 inhibitor | 0 | 0 | 0 | — |
| 9 | Warfarin + NSAID | 0 | 0 | 0 | — |
| 10 | Warfarin + CYP2C9 inhibitor (or rifampin) | 0 | 0 | 0 | — |
| 11 | DOAC + strong CYP3A4/P-gp inhibitor | 0 | 0 | 0 | — |
| 12 | Anticoagulant + DAPT or antiplatelet + NSAID | 0 | 0 | 0 | — |
| 13 | SSRI + NSAID or anticoagulant | 0 | 0 | 0 | — |
| 14 | Triple whammy: ACEi/ARB + diuretic + NSAID | 0 | 0 | 0 | — |
| 15 | ACEi/ARB or TMP-SMX + MRA (hyperkalemia) | 0 | 0 | 0 | — |
| 16 | Lithium + NSAID, ACEi/ARB, or thiazide | 0 | 0 | 0 | — |
| 17 | Thiazide + SSRI (hyponatremia) | 1 | 1 | 1 | G05 |
| 18 | Digoxin + P-gp inhibitor or loop/thiazide | 0 | 0 | 0 | — |
| 19 | Metformin + AKI cause | 0 | 0 | 0 | — |
| 20 | Beta-blocker + verapamil or diltiazem | 0 | 0 | 0 | — |
| 21 | Nitrate + PDE5 inhibitor or riociguat | 1 | 1 | 1 | G06 |
| 22 | Alpha-1 blocker + PDE5 inhibitor or antihypertensive | 0 | 0 | 0 | — |
| 23 | Stacked QT prolongers | 0 | 0 | 0 | — |
| 24 | MAOI + sympathomimetic | 0 | 0 | 0 | — |
| 25 | Clonidine + beta-blocker | 0 | 0 | 0 | — |
| 26 | Sulfonylurea + CYP2C9 inhibitor or beta-blocker | 0 | 0 | 0 | — |
| 27 | Statin + CYP3A4 inhibitor, gemfibrozil, or amiodarone/verapamil/diltiazem | 0 | 0 | 0 | — |
| 28 | Colchicine + CYP3A4/P-gp inhibitor | 0 | 0 | 0 | — |
| 29 | Xanthine oxidase inhibitor + thiopurine | 0 | 0 | 0 | — |
| 30 | Methotrexate + TMP-SMX, NSAID, PPI, or penicillin | 0 | 0 | 0 | — |
| 31 | Clopidogrel + omeprazole or esomeprazole | 0 | 0 | 0 | — |
| 32 | Valproate + carbapenem | 1 | 1 | 1 | G01 |
| 33 | Inducer + DOAC, calcineurin inhibitor, PI, OC, or methadone | 0 | 0 | 0 | — |
| 34 | Calcineurin inhibitor + azole, clarithromycin, diltiazem, or verapamil | 0 | 0 | 0 | — |
| 35 | Codeine/tramadol + CYP2D6 inhibitor | 1 | 1 | 1 | G03 |
| 36 | Fluoroquinolone + systemic corticosteroid | 1 | 1 | 1 | G04 |

Rows no list in L01–L41 exercises: 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 33, 34.
