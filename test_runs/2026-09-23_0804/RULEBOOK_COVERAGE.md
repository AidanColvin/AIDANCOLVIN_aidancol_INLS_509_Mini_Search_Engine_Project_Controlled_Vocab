# Rulebook coverage

Rows are Section 3 of TEST_PACK.md. A row applies to a list when the list holds drugs from each side of the row (different entries, different drugs).
"Flagged" means the site showed an alert holding at least two of the row's drugs. "Named" means that alert's text also names the row's syndrome.
In the list column, a bare ID means named, ~ means flagged but syndrome not named, ✗ means not flagged.

| Row | Combination | Lists it applies to | Flagged | Named | Lists |
|---|---|---|---|---|---|
| 1 | Opioid + benzodiazepine | 4 | 4 | 4 | L06 L12 L14 L36 |
| 2 | Opioid + gabapentinoid | 3 | 3 | 3 | L06 L14 L36 |
| 3 | Oxycodone/fentanyl/methadone + strong CYP3A4 inhibitor | 0 | 0 | 0 | — |
| 4 | Tizanidine + ciprofloxacin or fluvoxamine | 0 | 0 | 0 | — |
| 5 | Clozapine + fluvoxamine or ciprofloxacin | 1 | 1 | 1 | L08 |
| 6 | Anticholinergic burden | 1 | 1 | 1 | L18 |
| 7 | SSRI/SNRI or MAOI + serotonergic drug | 7 | 7 | 7 | L02 L07 L09 L13 L25 L27 L40 |
| 8 | Tramadol/bupropion + threshold-lowering drug or CYP2D6 inhibitor | 2 | 2 | 2 | L07 L19 |
| 9 | Warfarin + NSAID | 1 | 1 | 1 | L05 |
| 10 | Warfarin + CYP2C9 inhibitor (or rifampin) | 2 | 2 | 2 | L05 L33 |
| 11 | DOAC + strong CYP3A4/P-gp inhibitor | 2 | 2 | 2 | L21 L37 |
| 12 | Anticoagulant + DAPT or antiplatelet + NSAID | 1 | 1 | 1 | L05 |
| 13 | SSRI + NSAID or anticoagulant | 4 | 4 | 4 | L05 L09 L33 L41 |
| 14 | Triple whammy: ACEi/ARB + diuretic + NSAID | 3 | 3 | 3 | L04 L17 L31 |
| 15 | ACEi/ARB or TMP-SMX + MRA (hyperkalemia) | 2 | 2 | 2 | L10 L17 |
| 16 | Lithium + NSAID, ACEi/ARB, or thiazide | 1 | 1 | 1 | L04 |
| 17 | Thiazide + SSRI (hyponatremia) | 0 | 0 | 0 | — |
| 18 | Digoxin + P-gp inhibitor or loop/thiazide | 2 | 2 | 2 | L15 L37 |
| 19 | Metformin + AKI cause | 1 | 0 | 0 | L04✗ |
| 20 | Beta-blocker + verapamil or diltiazem | 1 | 1 | 1 | L15 |
| 21 | Nitrate + PDE5 inhibitor or riociguat | 1 | 1 | 1 | L16 |
| 22 | Alpha-1 blocker + PDE5 inhibitor or antihypertensive | 1 | 1 | 1 | L16 |
| 23 | Stacked QT prolongers | 6 | 6 | 6 | L03 L05 L19 L22 L25 L27 |
| 24 | MAOI + sympathomimetic | 1 | 1 | 1 | L07 |
| 25 | Clonidine + beta-blocker | 1 | 1 | 1 | L16 |
| 26 | Sulfonylurea + CYP2C9 inhibitor or beta-blocker | 1 | 1 | 1 | L23 |
| 27 | Statin + CYP3A4 inhibitor, gemfibrozil, or amiodarone/verapamil/diltiazem | 5 | 5 | 2 | L10 L21~ L28~ L37~ L39 |
| 28 | Colchicine + CYP3A4/P-gp inhibitor | 1 | 1 | 1 | L39 |
| 29 | Xanthine oxidase inhibitor + thiopurine | 1 | 1 | 1 | L32 |
| 30 | Methotrexate + TMP-SMX, NSAID, PPI, or penicillin | 1 | 1 | 1 | L32 |
| 31 | Clopidogrel + omeprazole or esomeprazole | 1 | 1 | 1 | L30 |
| 32 | Valproate + carbapenem | 0 | 0 | 0 | — |
| 33 | Inducer + DOAC, calcineurin inhibitor, PI, OC, or methadone | 2 | 2 | 2 | L20 L33 |
| 34 | Calcineurin inhibitor + azole, clarithromycin, diltiazem, or verapamil | 1 | 1 | 1 | L22 |
| 35 | Codeine/tramadol + CYP2D6 inhibitor | 1 | 1 | 1 | L19 |
| 36 | Fluoroquinolone + systemic corticosteroid | 0 | 0 | 0 | — |

Rows no list in L01–L41 exercises: 3, 4, 17, 32, 36.
