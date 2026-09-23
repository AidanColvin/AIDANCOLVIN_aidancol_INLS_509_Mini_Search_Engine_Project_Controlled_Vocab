# Interaction checker validation

- Run label: local final, before push
- Base URL: http://127.0.0.1:58211
- Build date reported: 2026-09-21
- Timestamp: 2026-09-23T03:39:29+00:00
- Key: /Users/aidancolvin/AIDANCOLVIN_aidancol_INLS_509_Mini_Search_Engine_Project_Controlled_Vocab/data/reference/drug_interaction_screen_fixture.json (Drug Interaction Screen - blind test fixture)

## Rules

### Category map

| Fixture category | Counts as |
| --- | --- |
| serotonin syndrome | serotonin syndrome risk (T14) |
| CNS depression | CNS depression risk (T15) |
| respiratory depression | CNS depression risk (T15) |
| QT prolongation | QT prolongation risk (T16) |
| duplicate entry | shared ingredient (duplicate entry / duplicate therapy), active metabolite pair (duplicate therapy) |
| duplicate therapy | shared ingredient (duplicate entry / duplicate therapy), active metabolite pair (duplicate therapy) |
| any category at severity contraindicated | also contraindicated combination (T17) |
| every other fixture category | unsupported by this checker's rule set; scored as a miss with cause "category outside the checker's rules" |

### Severity map (alert tier to fixture severity)

| Tier | Severity |
| --- | --- |
| 1 | contraindicated |
| 2 | major |
| 3 | major |
| 4 | moderate |
| null (duplication flags) | minor |

### Scoring rules

- Scoring uses the newline-separated, key-order variant. The other three variants are compared to it for consistency only.
- HIT: one alert's members cover every expected drug (a repeated drug needs a distinct member per repeat) under an equivalent category at the expected severity or higher.
- Drug names match on lowercase generic, base-ingredient, brand, and matched-name-chain names from the medication table. Release-form words (ER, XR, IR, SR, DR, CR, LA, CD, XL, "mixed salts") are dropped, and a name matches when it equals the other or is a leading-word prefix of it, so "lithium" matches "lithium carbonate". A combination "a/b" is satisfied by either component.
- PARTIAL: an alert covers every expected drug but its category or severity differs; the actual risk and severity are shown.
- MISS causes, in order: category outside the checker's rules; drug unresolved (a listed drug has no resolved medication-table row); drugs resolved but no alert.
- FALSE POSITIVE: a moderate-or-higher alert whose two members are exactly a should_not_flag pair, a moderate-or-higher alert that includes a single should_not_flag drug, any moderate-or-higher alert when should_not_flag says "any pair", and any moderate-or-higher alert on a list whose expected list is empty.
- Totals: the checker's daily_total is summed across resolved rows sharing the molecule and compared with the first amount in the key's text, or with the matching amount when the key writes one per component as "a / b" (mcg, mg, and g are interconverted). Weekly, per-episode, moiety, "no single daily number" entries, and a key total with no amount this rule can parse (for example a unit outside mcg/h, mcg, mg, g, mEq, units, such as "about 70 MME") are recorded as not comparable.

## Summary

- Lists run: 41
- Expected items: 196
- Hits: 31
- Partials: 15
- Misses: 150 (unsupported category 127; drug unresolved 0; drugs resolved but no alert 23)
- False positives: 1
- Totals: matched 24, mismatched 8, no checker total 0, not comparable 4
- Lists with variant differences: 0
- Lists with unresolved entries: 18
- Request errors: 0

## L01: Same drug entered twice; sedative stacking; stimulant above labeled maximum

Text sent (newline variant):

```
Ambien 10 mg once daily at bedtime
Xanax 1 mg three times daily
Adderall 20 mg three times daily
Zyprexa 10 mg once daily
Zyprexa 2.5 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| olanzapine, olanzapine | duplicate entry | moderate | PARTIAL (got shared_ingredient at minor) | Zyprexa and Zyprexa share olanzapine | base ingredients: olanzapine | Zyprexa / |
| alprazolam, zolpidem, olanzapine | CNS depression | major | MISS (drugs resolved but no alert) |  |  |  |
| amphetamine/dextroamphetamine | dose ceiling | moderate | MISS (category outside the checker's rules) |  |  |  |
| amphetamine/dextroamphetamine, alprazolam, olanzapine | opposing pharmacology | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Total olanzapine: match (expected 12.5 mg; checker 12.5 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L02: Serotonin syndrome cluster; PRN max dosing

Text sent (newline variant):

```
Zoloft 100 mg once daily
Ultram 50 mg four times daily
Imitrex 50 mg as needed, may repeat once after 2 hours
Flexeril 10 mg three times daily
Zofran 8 mg twice daily
Lipitor 40 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| sertraline, tramadol, sumatriptan, cyclobenzaprine, ondansetron | serotonin syndrome | major | HIT | Serotonin Syndrome Risk shared by 5 drugs | Serotonin Syndrome: Increased risk when co-administered with other serotonergic agents, but also when taken alone. | Zoloft / warnings_and_cautions |
| tramadol, sertraline | seizure threshold | moderate | MISS (category outside the checker's rules) |  |  |  |
| ondansetron, tramadol | efficacy loss | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: may repeat once after 2 hours (unresolved: RxNorm found no close name)
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L03: QT prolongation; CYP2C19 inhibition pushing citalopram past its cap; diuretic electrolyte loss

Text sent (newline variant):

```
Celexa 40 mg once daily
Haldol 5 mg twice daily
Zithromax 500 mg once daily
Diflucan 200 mg once daily
Lasix 40 mg once daily
Protonix 40 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| citalopram, haloperidol, azithromycin, fluconazole | QT prolongation | major | HIT | QT Prolongation Risk shared by 4 drugs | QT-Prolongation and Torsade de Pointes : Dose-dependent QTc prolongation, Torsade de pointes, ventricular tachycardia, and sudden death have occurred. | Celexa / warnings_and_cautions |
| citalopram, fluconazole | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| haloperidol, fluconazole | CYP inhibition | moderate | MISS (category outside the checker's rules) |  |  |  |
| furosemide, citalopram, haloperidol, azithromycin, fluconazole | electrolyte | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L04: Lithium toxicity from three renal-handling interactions; triple whammy; metformin + topiramate

Text sent (newline variant):

```
Lithobid 300 mg three times daily
Zestril 20 mg once daily
Microzide 25 mg once daily
Motrin 800 mg three times daily
Topamax 100 mg twice daily
Glucophage 1,000 mg twice daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| lithium, lisinopril | lithium toxicity | major | MISS (category outside the checker's rules) |  |  |  |
| lithium, hydrochlorothiazide | lithium toxicity | major | MISS (category outside the checker's rules) |  |  |  |
| lithium, ibuprofen | lithium toxicity | major | MISS (category outside the checker's rules) |  |  |  |
| lisinopril, hydrochlorothiazide, ibuprofen | nephrotoxicity | major | MISS (category outside the checker's rules) |  |  |  |
| metformin, topiramate | metabolic acidosis | moderate | MISS (category outside the checker's rules) |  |  |  |
| topiramate, hydrochlorothiazide | electrolyte | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L05: Warfarin potentiation; multi-agent bleeding; alternating-day dosing; combination product

Text sent (newline variant):

```
Coumadin 5 mg once daily on Monday, Wednesday, Friday
Coumadin 2.5 mg once daily on Tuesday, Thursday, Saturday, Sunday
Bactrim DS 800/160 mg twice daily
Cordarone 200 mg once daily
Lexapro 10 mg once daily
Bayer 81 mg once daily
Plavix 75 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| warfarin, sulfamethoxazole/trimethoprim | bleeding | major | MISS (category outside the checker's rules) |  |  |  |
| warfarin, amiodarone | bleeding | major | MISS (category outside the checker's rules) |  |  |  |
| warfarin, aspirin, clopidogrel | bleeding | major | MISS (category outside the checker's rules) |  |  |  |
| escitalopram, warfarin, aspirin, clopidogrel | bleeding | moderate | MISS (category outside the checker's rules) |  |  |  |
| escitalopram, amiodarone | QT prolongation | major | HIT | QT Prolongation Risk shared by 2 drugs | 5.4 Worsened Arrhythmia Amiodarone hydrochloride can exacerbate the presenting arrhythmia in about 2 to 5% of patients or cause new ventricular fibrillation, incessant ventricular… | Cordarone / warnings_and_cautions |

Unresolved entries: Wednesday (unresolved: RxNorm found no close name); Friday (unresolved: RxNorm found no close name); Thursday (unresolved: RxNorm found no close name); Saturday (unresolved: RxNorm found no close name); Sunday (unresolved: RxNorm found no close name); Bayer 81 mg once daily (unresolved: RxNorm found no close name)
False positives: none
Total warfarin: not_comparable (expected 5 mg Mon/Wed/Fri, 2.5 mg other days = 25 mg/week; there is no single daily number; checker 7.5 mg)
Total sulfamethoxazole: match (expected 1,600 mg / 320 mg; checker 1600 mg)
Total trimethoprim: mismatch (expected 1,600 mg / 320 mg; checker 1600 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L06: Opioid + benzodiazepine boxed warning; ER and IR of one opioid; MME; sedative burden

Text sent (newline variant):

```
OxyContin 30 mg twice daily
Roxicodone 10 mg every 4 hours as needed, max 6 doses/day
Klonopin 1 mg twice daily
Neurontin 600 mg three times daily
Soma 350 mg three times daily
Vistaril 25 mg three times daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| oxycodone ER, oxycodone IR | duplicate entry | major | PARTIAL (got shared_ingredient at minor) | OxyContin and Roxicodone share oxycodone | base ingredients: oxycodone | OxyContin / |
| oxycodone, clonazepam | respiratory depression | major | HIT | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | OxyContin / boxed_warning |
| oxycodone, gabapentin | respiratory depression | major | HIT | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | OxyContin / boxed_warning |
| oxycodone, carisoprodol, clonazepam | CNS depression | major | HIT | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | OxyContin / boxed_warning |
| hydroxyzine, oxycodone, clonazepam | CNS depression | moderate | HIT | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | OxyContin / boxed_warning |

Unresolved entries: max 6 doses/day (unresolved: RxNorm found no close name)
False positives: none
Total oxycodone: match (expected 120 mg/day max (60 mg ER + 60 mg IR) = 180 MME; checker 120 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L07: MAOI contraindications; microgram unit; PRN max

Text sent (newline variant):

```
Nardil 15 mg three times daily
Wellbutrin SR 150 mg twice daily
Demerol 50 mg every 6 hours as needed, max 4 doses/day
Ritalin 10 mg twice daily
Norvasc 10 mg once daily
Synthroid 100 mcg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| phenelzine, bupropion | hypertensive crisis | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| phenelzine, meperidine | serotonin syndrome | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| phenelzine, methylphenidate | hypertensive crisis | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| phenelzine, amlodipine | hypotension | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: max 4 doses/day (unresolved: RxNorm found no close name)
False positives: none
Total levothyroxine: match (expected 100 mcg = 0.1 mg; checker 100 mcg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L08: Clozapine with opposing CYP effects; bone marrow suppression; respiratory arrest

Text sent (newline variant):

```
Clozaril 200 mg twice daily
Tegretol 400 mg twice daily
Luvox 100 mg twice daily
Cipro 500 mg twice daily
Ativan 1 mg twice daily
Depakote 500 mg twice daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| clozapine, carbamazepine | myelosuppression | major | MISS (category outside the checker's rules) |  |  |  |
| clozapine, fluvoxamine | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| clozapine, ciprofloxacin | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| clozapine, lorazepam | respiratory depression | major | MISS (drugs resolved but no alert) |  |  |  |
| carbamazepine, divalproex | CYP induction | moderate | MISS (category outside the checker's rules) |  |  |  |
| clozapine, ciprofloxacin | QT prolongation | moderate | HIT | QT Prolongation Risk shared by 2 drugs | Use caution when administering concomitant medications that prolong the QT interval or inhibit the metabolism of VERSACLOZ. | Clozaril / warnings_and_cautions |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L09: Duplicate SSRI; CYP2D6 inhibition of a prodrug and of a substrate; SSRI + NSAID bleeding

Text sent (newline variant):

```
Prozac 40 mg once daily
Paxil 20 mg once daily
Nolvadex 20 mg once daily
Toprol-XL 100 mg once daily
Naprosyn 500 mg twice daily
Nexium 40 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| fluoxetine, paroxetine | duplicate therapy | major | PARTIAL (got T14 at major) | Serotonin Syndrome Risk shared by 2 drugs | When using fluoxetine and olanzapine in combination, also refer to the Warnings and Precautions section of the package insert for Symbyax. • Suicidal Thoughts and Behaviors in Chi… | Prozac / warnings_and_cautions |
| fluoxetine, paroxetine, tamoxifen | efficacy loss | major | MISS (category outside the checker's rules) |  |  |  |
| fluoxetine, paroxetine, metoprolol | CYP inhibition | moderate | MISS (category outside the checker's rules) |  |  |  |
| fluoxetine, paroxetine, naproxen | bleeding | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: QT Prolongation Risk shared by 3 drugs [major, rule: esomeprazole]
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L10: Contraindicated statin-macrolide pair; hyperkalemia triad; mEq unit; weekly dosing

Text sent (newline variant):

```
Zocor 40 mg once daily at bedtime
Biaxin 500 mg twice daily
Aldactone 25 mg once daily
Vasotec 10 mg twice daily
Klor-Con 20 mEq once daily
Trexall 15 mg once weekly
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| simvastatin, clarithromycin | myopathy/rhabdomyolysis | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| spironolactone, enalapril, potassium chloride | hyperkalemia | major | MISS (category outside the checker's rules) |  |  |  |
| methotrexate | dosing frequency | major | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Total methotrexate: not_comparable (expected 15 mg per week (not per day); checker none)
Total potassium chloride: match (expected 20 mEq (about 1.5 g KCl); checker 20 mEq)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L11: Control: no clinically significant interactions

Text sent (newline variant):

```
Synthroid 75 mcg once daily
Lipitor 20 mg once daily
Zestril 10 mg once daily
Lexapro 10 mg once daily
Singulair 10 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| (control list: nothing expected) | | | | | | |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L12: Hidden duplicates inside combination products; acetaminophen ceiling; IR + ER summing

Text sent (newline variant):

```
Symbyax 6/25 mg once daily
Prozac 20 mg once daily
Norco 10/325 mg four times daily
Tylenol 500 mg 2 tablets three times daily
Xanax 0.5 mg three times daily
Xanax XR 1 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| olanzapine/fluoxetine, fluoxetine | duplicate therapy | major | PARTIAL (got shared_ingredient at minor) | Symbyax and Prozac share fluoxetine | base ingredients: fluoxetine, olanzapine | Symbyax / |
| hydrocodone/acetaminophen, acetaminophen | dose ceiling | major | MISS (category outside the checker's rules) |  |  |  |
| alprazolam, alprazolam ER | duplicate entry | moderate | PARTIAL (got shared_ingredient at minor) | Xanax and Xanax XR share alprazolam | base ingredients: alprazolam | Xanax / |
| hydrocodone, alprazolam, olanzapine | respiratory depression | major | MISS (drugs resolved but no alert) |  |  |  |
| fluoxetine, hydrocodone | CYP inhibition | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Total fluoxetine: mismatch (expected 45 mg; checker 26 mg)
Total acetaminophen: mismatch (expected 4,300 mg; checker 3040 mg)
Total alprazolam: match (expected 2.5 mg; checker 2.5 mg)
Total hydrocodone: match (expected 40 mg; checker 40 mg)
Total olanzapine: match (expected 6 mg; checker 6 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L13: Linezolid acting as an MAOI; serotonergic load; fentanyl patch units

Text sent (newline variant):

```
Zyvox 600 mg twice daily
Effexor XR 225 mg once daily
Buspar 15 mg twice daily
Reglan 10 mg four times daily, before meals and at bedtime
Duragesic 25 mcg/h one patch every 72 hours
Robaxin 750 mg four times daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| linezolid, venlafaxine | serotonin syndrome | contraindicated | HIT | Zyvox matches a contraindication named in Effexor XR's label | Venlafaxine hydrochloride extended-release capsules are contraindicated in patients: • with known hypersensitivity to venlafaxine hydrochloride, desvenlafaxine succinate or to any… | Effexor XR / contraindications |
| linezolid, buspirone, fentanyl, metoclopramide | serotonin syndrome | major | HIT | Serotonin Syndrome Risk shared by 5 drugs | 5.3 Serotonin Syndrome Spontaneous reports of serotonin syndrome including fatal cases associated with the co-administration of Linezolid and serotonergic agents, including antide… | Zyvox / warnings_and_cautions |
| fentanyl, methocarbamol | respiratory depression | major | HIT | CNS Depression Risk shared by 2 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | Duragesic / boxed_warning |
| metoclopramide, venlafaxine, buspirone | serotonin syndrome | moderate | HIT | Serotonin Syndrome Risk shared by 5 drugs | 5.3 Serotonin Syndrome Spontaneous reports of serotonin syndrome including fatal cases associated with the co-administration of Linezolid and serotonergic agents, including antide… | Zyvox / warnings_and_cautions |

Unresolved entries: before meals and at bedtime (unresolved: RxNorm found no close name)
False positives: none
Total fentanyl: match (expected 25 mcg/h continuous = 600 mcg/day = about 60 MME; checker 25 mcg/h)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L14: Respiratory depression stacking; duplicate benzodiazepines; fentanyl MME

Text sent (newline variant):

```
Duragesic 50 mcg/h one patch every 72 hours
Valium 10 mg three times daily
Restoril 30 mg once daily at bedtime
Lyrica 150 mg twice daily
Phenergan 25 mg every 6 hours as needed, max 4 doses/day
Zanaflex 4 mg three times daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| fentanyl, diazepam, temazepam | respiratory depression | major | HIT | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | Duragesic / boxed_warning |
| diazepam, temazepam | duplicate therapy | major | PARTIAL (got T15 at major) | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | Duragesic / boxed_warning |
| fentanyl, pregabalin | respiratory depression | major | HIT | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | Duragesic / boxed_warning |
| fentanyl, promethazine | respiratory depression | major | HIT | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | Duragesic / boxed_warning |
| tizanidine, fentanyl, diazepam, temazepam, pregabalin, promethazine | CNS depression | moderate | HIT | CNS Depression Risk shared by 6 drugs | Risks From Concomitant Use With Benzodiazepines Or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | Duragesic / boxed_warning |

Unresolved entries: max 4 doses/day (unresolved: RxNorm found no close name)
False positives: none
Total fentanyl: match (expected 50 mcg/h continuous = 1,200 mcg/day = about 120 MME; checker 50 mcg/h)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L15: Bradycardia and AV block; digoxin level elevation; electrolyte-driven digoxin toxicity

Text sent (newline variant):

```
Toprol-XL 200 mg once daily
Cardizem CD 240 mg once daily
Lanoxin 0.25 mg once daily
Cordarone 200 mg once daily
Aricept 10 mg once daily at bedtime
Lasix 40 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| metoprolol, diltiazem | bradycardia/AV block | major | MISS (category outside the checker's rules) |  |  |  |
| digoxin, amiodarone | digoxin toxicity | major | MISS (category outside the checker's rules) |  |  |  |
| digoxin, diltiazem | digoxin toxicity | moderate | MISS (category outside the checker's rules) |  |  |  |
| digoxin, metoprolol, diltiazem, amiodarone | bradycardia/AV block | major | MISS (category outside the checker's rules) |  |  |  |
| donepezil, metoprolol, diltiazem, digoxin | bradycardia/AV block | moderate | MISS (category outside the checker's rules) |  |  |  |
| furosemide, digoxin, amiodarone | electrolyte | moderate | MISS (category outside the checker's rules) |  |  |  |
| amiodarone, metoprolol | CYP inhibition | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Total digoxin: match (expected 0.25 mg = 250 mcg; checker 0.25 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L16: Nitrate + PDE5 contraindication; additive hypotension; clonidine with a beta-blocker

Text sent (newline variant):

```
Viagra 100 mg as needed, no more than once daily
Nitrostat 0.4 mg as needed for chest pain, up to 3 tablets in 15 minutes
Imdur 60 mg once daily
Flomax 0.4 mg once daily
Catapres 0.1 mg twice daily
Coreg 25 mg twice daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| sildenafil, nitroglycerin | hypotension | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| sildenafil, isosorbide mononitrate | hypotension | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| sildenafil, tamsulosin | hypotension | moderate | MISS (category outside the checker's rules) |  |  |  |
| clonidine, carvedilol | bradycardia/AV block | major | MISS (category outside the checker's rules) |  |  |  |
| carvedilol, tamsulosin, clonidine, isosorbide mononitrate | hypotension | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: no more than once daily (unresolved: RxNorm found no close name); up to 3 tablets in 15 minutes (unresolved: RxNorm found no close name)
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L17: Hyperkalemia from four directions; triple whammy AKI; SGLT2 volume depletion

Text sent (newline variant):

```
Bactrim DS 800/160 mg twice daily
Aldactone 50 mg once daily
Cozaar 100 mg once daily
Klor-Con 40 mEq once daily
Celebrex 200 mg twice daily
Jardiance 10 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| trimethoprim, spironolactone, losartan, potassium chloride | hyperkalemia | major | MISS (category outside the checker's rules) |  |  |  |
| losartan, spironolactone, celecoxib | nephrotoxicity | major | MISS (category outside the checker's rules) |  |  |  |
| empagliflozin, spironolactone, celecoxib, losartan | nephrotoxicity | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Total sulfamethoxazole: match (expected 1,600 mg / 320 mg; checker 1600 mg)
Total trimethoprim: mismatch (expected 1,600 mg / 320 mg; checker 1600 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L18: Anticholinergic burden; cholinesterase inhibitor opposed by anticholinergics; CYP2D6 raising a TCA

Text sent (newline variant):

```
Elavil 75 mg once daily at bedtime
Ditropan 5 mg three times daily
Vistaril 50 mg three times daily
Cogentin 1 mg twice daily
Aricept 10 mg once daily
Paxil 40 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| amitriptyline, oxybutynin, hydroxyzine, benztropine, paroxetine | anticholinergic burden | major | MISS (category outside the checker's rules) |  |  |  |
| donepezil, amitriptyline, oxybutynin, hydroxyzine, benztropine | therapeutic antagonism | major | MISS (category outside the checker's rules) |  |  |  |
| paroxetine, amitriptyline | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| amitriptyline, hydroxyzine | QT prolongation | moderate | PARTIAL (got T15 at major) | CNS Depression Risk shared by 2 drugs | Amitriptyline hydrochloride may enhance the response to alcohol and the effects of barbiturates and other CNS depressants. | Elavil / warnings |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L19: Seizure threshold at labeled maximums; CYP1A2 inhibition of theophylline; QT

Text sent (newline variant):

```
Wellbutrin XL 450 mg once daily
Ultram 100 mg four times daily
Theo-24 400 mg once daily
Cipro 500 mg twice daily
Seroquel 400 mg once daily at bedtime
Lipitor 10 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| bupropion, tramadol, theophylline, ciprofloxacin, quetiapine | seizure threshold | major | MISS (category outside the checker's rules) |  |  |  |
| theophylline, ciprofloxacin | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| ciprofloxacin, quetiapine | QT prolongation | moderate | HIT | QT Prolongation Risk shared by 2 drugs | QT Prolongation: Prolongation of the QT interval and isolated cases of torsade de pointes have been reported. | Cipro / warnings_and_cautions |
| bupropion, tramadol | CYP inhibition | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L20: Strong CYP3A4/P-gp inducer undermining five drugs

Text sent (newline variant):

```
Rifadin 600 mg once daily
Xarelto 20 mg once daily with the evening meal
Sprintec 0.25 mg/35 mcg once daily
Prograf 2 mg twice daily
Latuda 80 mg once daily with food
Dolophine 60 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| rifampin, rivaroxaban | efficacy loss | major | MISS (category outside the checker's rules) |  |  |  |
| rifampin, norgestimate/ethinyl estradiol | efficacy loss | major | MISS (category outside the checker's rules) |  |  |  |
| rifampin, tacrolimus | efficacy loss | major | MISS (category outside the checker's rules) |  |  |  |
| rifampin, lurasidone | CYP induction | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| rifampin, methadone | efficacy loss | major | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: Sprintec 0.25 mg/35 mcg once daily (unresolved: RxNorm found no close name)
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L21: Strong CYP3A4 inhibitor against benzodiazepines, a DOAC, and a statin

Text sent (newline variant):

```
Nizoral 200 mg once daily
Halcion 0.25 mg once daily at bedtime
Xanax 1 mg three times daily
Eliquis 5 mg twice daily
Lipitor 80 mg once daily
Norvasc 10 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| ketoconazole, triazolam | CYP inhibition | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| ketoconazole, alprazolam | CYP inhibition | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| ketoconazole, apixaban | bleeding | major | MISS (category outside the checker's rules) |  |  |  |
| ketoconazole, atorvastatin | myopathy/rhabdomyolysis | major | MISS (category outside the checker's rules) |  |  |  |
| ketoconazole, amlodipine | CYP inhibition | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L22: Transplant regimen: azole raising tacrolimus; QT; PPI reducing mycophenolate

Text sent (newline variant):

```
Prograf 3 mg twice daily
CellCept 1,000 mg twice daily
Diflucan 400 mg once daily
Zocor 40 mg once daily at bedtime
Prilosec 20 mg once daily
Zofran 8 mg twice daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| tacrolimus, fluconazole | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| tacrolimus, fluconazole, ondansetron | QT prolongation | major | HIT | QT Prolongation Risk shared by 4 drugs | When co-administering tacrolimus with other substrates and/or inhibitors of CYP3A4 that also have the potential to prolong the QT interval, a reduction in tacrolimus dose, frequen… | Prograf / warnings_and_cautions |
| mycophenolate mofetil, omeprazole | absorption/timing | moderate | MISS (category outside the checker's rules) |  |  |  |
| simvastatin, fluconazole | myopathy/rhabdomyolysis | moderate | MISS (category outside the checker's rules) |  |  |  |
| tacrolimus, omeprazole | CYP inhibition | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L23: Hypoglycemia; CYP2C9 on a sulfonylurea; beta-blocker masking; weekly injectable and unit-based dosing

Text sent (newline variant):

```
Glucotrol 10 mg twice daily
Lantus 40 units once daily at bedtime
Inderal 40 mg twice daily
Bactrim DS 800/160 mg twice daily
Levaquin 750 mg once daily
Ozempic 1 mg once weekly
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| glipizide, insulin glargine, semaglutide | hypoglycemia | major | MISS (category outside the checker's rules) |  |  |  |
| glipizide, sulfamethoxazole/trimethoprim | hypoglycemia | major | MISS (category outside the checker's rules) |  |  |  |
| levofloxacin, glipizide, insulin glargine | hypoglycemia | major | MISS (category outside the checker's rules) |  |  |  |
| propranolol, glipizide, insulin glargine | hypoglycemia | moderate | MISS (category outside the checker's rules) |  |  |  |
| semaglutide, glipizide | absorption/timing | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Total insulin glargine: match (expected 40 units (units, not mg); checker 40 units)
Total semaglutide: not_comparable (expected 1 mg per week (not per day); checker none)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L24: Duplicate therapy across three classes; hidden acetaminophen total; MME

Text sent (newline variant):

```
Norco 10/325 mg every 6 hours
Percocet 5/325 mg every 6 hours as needed, max 4 doses/day
Ambien 10 mg once daily at bedtime
Lunesta 3 mg once daily at bedtime
Mobic 15 mg once daily
Aleve 220 mg twice daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| hydrocodone/acetaminophen, oxycodone/acetaminophen | duplicate therapy | major | PARTIAL (got shared_ingredient at minor) | Norco and PERCOCET share acetaminophen | base ingredients: acetaminophen, hydrocodone | Norco / |
| acetaminophen, acetaminophen | duplicate entry | moderate | PARTIAL (got shared_ingredient at minor) | Norco and PERCOCET share acetaminophen | base ingredients: acetaminophen, hydrocodone | Norco / |
| zolpidem, eszopiclone | duplicate therapy | major | PARTIAL (got T15 at major) | CNS Depression Risk shared by 4 drugs | Risks from Concomitant Use with Benzodiazepines or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | Norco / boxed_warning |
| meloxicam, naproxen sodium | duplicate therapy | major | MISS (drugs resolved but no alert) |  |  |  |
| hydrocodone, oxycodone, zolpidem, eszopiclone | CNS depression | major | HIT | CNS Depression Risk shared by 4 drugs | Risks from Concomitant Use with Benzodiazepines or Other CNS Depressants Concomitant use of opioids with benzodiazepines or other central nervous system (CNS) depressants, includi… | Norco / boxed_warning |

Unresolved entries: max 4 doses/day (unresolved: RxNorm found no close name)
False positives: none
Total acetaminophen: mismatch (expected 2,600 mg; checker 60 mg)
Total hydrocodone: match (expected 40 mg; checker 40 mg)
Total oxycodone: match (expected 20 mg max; checker 20 mg)
Total combined opioid: not_comparable (expected about 70 MME; checker none)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L25: Methadone QT stacking; azole raising methadone; serotonin

Text sent (newline variant):

```
Dolophine 40 mg twice daily
Seroquel 300 mg once daily at bedtime
Zofran 8 mg twice daily
Levaquin 500 mg once daily
Effexor XR 150 mg once daily
Diflucan 200 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| methadone, quetiapine, ondansetron, levofloxacin, fluconazole | QT prolongation | major | HIT | QT Prolongation Risk shared by 5 drugs | Life-Threatening QT Prolongation QT interval prolongation and serious arrhythmia (torsades de pointes) have occurred during treatment with methadone. | Dolophine / boxed_warning |
| methadone, fluconazole | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| methadone, venlafaxine | serotonin syndrome | moderate | HIT | Serotonin Syndrome Risk shared by 3 drugs | Serotonin Syndrome : Potentially life-threatening condition could result from concomitant serotonergic drug administration. | Dolophine / warnings_and_cautions |
| methadone, quetiapine | respiratory depression | major | PARTIAL (got T16 at major) | QT Prolongation Risk shared by 5 drugs | Life-Threatening QT Prolongation QT interval prolongation and serious arrhythmia (torsades de pointes) have occurred during treatment with methadone. | Dolophine / boxed_warning |
| quetiapine, fluconazole | CYP inhibition | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L26: Valproate-lamotrigine; enzyme induction; hyperammonemia; salicylate displacement

Text sent (newline variant):

```
Depakote 750 mg twice daily
Lamictal 200 mg once daily
Topamax 100 mg twice daily
Bayer 325 mg once daily
Tegretol 400 mg twice daily
Klonopin 0.5 mg twice daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| divalproex, lamotrigine | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| carbamazepine, lamotrigine | CYP induction | moderate | MISS (category outside the checker's rules) |  |  |  |
| carbamazepine, divalproex | CYP induction | moderate | MISS (category outside the checker's rules) |  |  |  |
| divalproex, topiramate | hyperammonemia | major | MISS (category outside the checker's rules) |  |  |  |
| divalproex, aspirin | bleeding | moderate | MISS (category outside the checker's rules) |  |  |  |
| carbamazepine, clonazepam | CYP induction | minor | MISS (category outside the checker's rules) |  |  |  |
| divalproex, lamotrigine, topiramate, carbamazepine, clonazepam | CNS depression | moderate | MISS (drugs resolved but no alert) |  |  |  |

Unresolved entries: Bayer 325 mg once daily (unresolved: RxNorm found no close name)
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L27: Dopamine antagonists opposing levodopa; MAO-B inhibitor with meperidine; serotonergic caution

Text sent (newline variant):

```
Sinemet 25/100 mg three times daily
Azilect 1 mg once daily
Reglan 10 mg four times daily, before meals and at bedtime
Haldol 2 mg once daily at bedtime
Demerol 50 mg every 6 hours as needed, max 4 doses/day
Lexapro 10 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| carbidopa/levodopa, metoclopramide | therapeutic antagonism | major | MISS (category outside the checker's rules) |  |  |  |
| carbidopa/levodopa, haloperidol | therapeutic antagonism | major | MISS (category outside the checker's rules) |  |  |  |
| rasagiline, meperidine | serotonin syndrome | contraindicated | HIT | DEMEROL matches a contraindication named in Azilect's label | Rasagiline is contraindicated for use with meperidine, tramadol, methadone, propoxyphene and MAO inhibitors (MAOIs), including other selective MAO-B inhibitors, because of risk of… | Azilect / contraindications |
| rasagiline, escitalopram | serotonin syndrome | moderate | HIT | Serotonin Syndrome Risk shared by 4 drugs | 5.2 Serotonin Syndrome Serotonin syndrome has been reported with concomitant use of an antidepressant (e.g., selective serotonin reuptake inhibitors-SSRIs, serotonin-norepinephrin… | Azilect / warnings_and_cautions |
| metoclopramide, haloperidol | duplicate therapy | major | MISS (drugs resolved but no alert) |  |  |  |
| haloperidol, escitalopram | QT prolongation | moderate | HIT | QT Prolongation Risk shared by 2 drugs | Sudden Death, Torsades de Pointes (TdP), and QTc Interval Prolongation: Avoid use of haloperidol decanoate in patients who are at risk of developing TdP. | Haldol Decanoate / warnings_and_cautions |

Unresolved entries: before meals and at bedtime (unresolved: RxNorm found no close name); max 4 doses/day (unresolved: RxNorm found no close name)
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L28: Cobicistat boosting: statin, benzodiazepine, inhaled steroid, PDE5 inhibitor, tenofovir

Text sent (newline variant):

```
Prezcobix 800/150 mg once daily with food
Truvada 200/300 mg once daily
Lipitor 80 mg once daily
Xanax 0.5 mg three times daily
Flonase 50 mcg per spray 2 sprays each nostril once daily
Viagra 50 mg as needed, no more than once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| darunavir/cobicistat, atorvastatin | myopathy/rhabdomyolysis | major | MISS (category outside the checker's rules) |  |  |  |
| darunavir/cobicistat, alprazolam | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| darunavir/cobicistat, fluticasone propionate | adrenal suppression | major | MISS (category outside the checker's rules) |  |  |  |
| darunavir/cobicistat, sildenafil | hypotension | major | MISS (category outside the checker's rules) |  |  |  |
| darunavir/cobicistat, tenofovir disoproxil fumarate | nephrotoxicity | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: no more than once daily (unresolved: RxNorm found no close name)
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L29: Control: no clinically significant interactions

Text sent (newline variant):

```
Amoxil 500 mg three times daily
Claritin 10 mg once daily
Singulair 10 mg once daily
Norvasc 5 mg once daily
Zoloft 50 mg once daily
Glucophage 500 mg twice daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| (control list: nothing expected) | | | | | | |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L30: Absorption and timing interactions versus one true CYP problem

Text sent (newline variant):

```
Synthroid 100 mcg once daily
Tums Ultra 1,000 mg twice daily
Cipro 500 mg twice daily
Feosol 325 mg twice daily
Prilosec 20 mg once daily
Plavix 75 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| levothyroxine, calcium carbonate | absorption/timing | moderate | MISS (category outside the checker's rules) |  |  |  |
| levothyroxine, ferrous sulfate | absorption/timing | moderate | MISS (category outside the checker's rules) |  |  |  |
| ciprofloxacin, calcium carbonate | absorption/timing | major | MISS (category outside the checker's rules) |  |  |  |
| ciprofloxacin, ferrous sulfate | absorption/timing | major | MISS (category outside the checker's rules) |  |  |  |
| clopidogrel, omeprazole | efficacy loss | major | MISS (category outside the checker's rules) |  |  |  |
| ferrous sulfate, omeprazole | absorption/timing | minor | MISS (category outside the checker's rules) |  |  |  |
| levothyroxine, omeprazole | absorption/timing | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: Tums Ultra 1000 mg twice daily (unresolved: RxNorm found no close name); Feosol 325 mg twice daily (unresolved: no collection label has exactly these ingredients)
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L31: Additive nephrotoxicity and ototoxicity; IV routes; gram unit

Text sent (newline variant):

```
Vancocin 1,000 mg every 12 hours
Garamycin 80 mg every 8 hours
Lasix 40 mg twice daily
Toradol 30 mg every 6 hours, not to exceed 5 days
Zestril 10 mg once daily
Zosyn 3.375 g every 6 hours
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| vancomycin, gentamicin | nephrotoxicity | major | MISS (category outside the checker's rules) |  |  |  |
| vancomycin, piperacillin/tazobactam | nephrotoxicity | moderate | MISS (category outside the checker's rules) |  |  |  |
| gentamicin, furosemide | ototoxicity | major | MISS (category outside the checker's rules) |  |  |  |
| ketorolac, lisinopril, furosemide | nephrotoxicity | major | MISS (category outside the checker's rules) |  |  |  |
| ketorolac, gentamicin, vancomycin | nephrotoxicity | major | MISS (category outside the checker's rules) |  |  |  |
| ketorolac, lisinopril | hyperkalemia | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: not to exceed 5 days (unresolved: RxNorm found no close name)
False positives: none
Total piperacillin: match (expected 13.5 g per day (3.375 g x 4); checker 13.5 g)
Total tazobactam: match (expected 13.5 g per day (3.375 g x 4); checker 13.5 g)
Total vancomycin: match (expected 2 g per day; checker 2000 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L32: Antifolate stacking; xanthine oxidase inhibition on azathioprine; NSAID on methotrexate; weekly dosing

Text sent (newline variant):

```
Trexall 20 mg once weekly
Bactrim DS 800/160 mg twice daily
Imuran 100 mg once daily
Zyloprim 300 mg once daily
Motrin 600 mg three times daily
folic acid 1 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| methotrexate, sulfamethoxazole/trimethoprim | myelosuppression | major | MISS (category outside the checker's rules) |  |  |  |
| azathioprine, allopurinol | myelosuppression | major | MISS (category outside the checker's rules) |  |  |  |
| methotrexate, ibuprofen | nephrotoxicity | moderate | MISS (category outside the checker's rules) |  |  |  |
| methotrexate, azathioprine | myelosuppression | moderate | MISS (category outside the checker's rules) |  |  |  |
| methotrexate | dosing frequency | major | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L33: Phenytoin: induction of contraceptive and statin; CYP2C9 inhibitors raising phenytoin; warfarin

Text sent (newline variant):

```
Dilantin 300 mg once daily at bedtime
Coumadin 5 mg once daily
Sprintec 0.25 mg/35 mcg once daily
Prozac 20 mg once daily
Diflucan 100 mg once daily
Lipitor 20 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| phenytoin, norgestimate/ethinyl estradiol | efficacy loss | major | MISS (category outside the checker's rules) |  |  |  |
| phenytoin, fluoxetine | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| phenytoin, fluconazole | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| phenytoin, warfarin | bleeding | major | MISS (category outside the checker's rules) |  |  |  |
| warfarin, fluconazole | bleeding | major | MISS (category outside the checker's rules) |  |  |  |
| warfarin, fluoxetine | bleeding | moderate | MISS (category outside the checker's rules) |  |  |  |
| phenytoin, atorvastatin | efficacy loss | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: Sprintec 0.25 mg/35 mcg once daily (unresolved: RxNorm found no close name)
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L34: Duplicate alpha-2 agonists; CYP2D6 inhibition of atomoxetine; stimulant + SSRI; sedation and hypotension

Text sent (newline variant):

```
Vyvanse 70 mg once daily in the morning
Strattera 80 mg once daily
Intuniv 3 mg once daily at bedtime
Kapvay 0.1 mg twice daily
Paxil 20 mg once daily
Seroquel 100 mg once daily at bedtime
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| guanfacine, clonidine | duplicate therapy | major | MISS (drugs resolved but no alert) |  |  |  |
| paroxetine, atomoxetine | CYP inhibition | major | MISS (category outside the checker's rules) |  |  |  |
| lisdexamfetamine, atomoxetine | duplicate therapy | moderate | MISS (drugs resolved but no alert) |  |  |  |
| lisdexamfetamine, paroxetine | serotonin syndrome | moderate | HIT | Serotonin Syndrome Risk shared by 2 drugs | Serotonin Syndrome: Increased risk when co-administered with serotonergic agents (e.g., SSRIs, SNRIs, triptans), but also during overdosage situations. | Vyvanse / warnings_and_cautions |
| quetiapine, guanfacine, clonidine | hypotension | moderate | MISS (category outside the checker's rules) |  |  |  |
| lisdexamfetamine, quetiapine | opposing pharmacology | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L35: Two triptans; propranolol on rizatriptan; TCA + triptan; three-component barbiturate product; overuse

Text sent (newline variant):

```
Imitrex 100 mg as needed, may repeat once after 2 hours, max 200 mg/day
Maxalt 10 mg as needed, may repeat after 2 hours, max 30 mg/day
Inderal LA 80 mg once daily
Elavil 50 mg once daily at bedtime
Topamax 50 mg twice daily
Fioricet 50/325/40 mg 2 tablets every 4 hours as needed, max 6 tablets/day
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| sumatriptan, rizatriptan | duplicate therapy | major | PARTIAL (got T14 at major) | Serotonin Syndrome Risk shared by 3 drugs | Serotonin syndrome: Discontinue sumatriptan if occurs. | IMITREX / warnings_and_cautions |
| rizatriptan, propranolol | CYP inhibition | moderate | MISS (category outside the checker's rules) |  |  |  |
| sumatriptan, rizatriptan, amitriptyline | serotonin syndrome | moderate | HIT | Serotonin Syndrome Risk shared by 3 drugs | Serotonin syndrome: Discontinue sumatriptan if occurs. | IMITREX / warnings_and_cautions |
| butalbital, amitriptyline, topiramate | CNS depression | moderate | HIT | CNS Depression Risk shared by 4 drugs | Neonates whose mothers are receiving propranolol at parturition have exhibited bradycardia, hypoglycemia and/or respiratory depression. | INDERAL LA / precautions |
| butalbital/acetaminophen/caffeine | combination parsing | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: may repeat once after 2 hours (unresolved: RxNorm found no close name); max 200 mg/day (unresolved: RxNorm found no close name); may repeat after 2 hours (unresolved: RxNorm found no close name); max 30 mg/day (unresolved: RxNorm found no close name); max 6 tablets/day (unresolved: RxNorm found no close name)
False positives: none
Total acetaminophen: mismatch (expected 1,950 mg max; checker 600 mg)
Total butalbital: mismatch (expected 300 mg max; checker 600 mg)
Total caffeine: mismatch (expected 240 mg max; checker 600 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L36: Opioid antagonist against a partial agonist; buprenorphine + benzodiazepine; a drug that should not flag

Text sent (newline variant):

```
Suboxone 8/2 mg twice daily
Revia 50 mg once daily
Campral 666 mg three times daily
Klonopin 0.5 mg twice daily
Neurontin 300 mg three times daily
Seroquel 50 mg once daily at bedtime
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| buprenorphine/naloxone, naltrexone | therapeutic antagonism | contraindicated | PARTIAL (got T15 at major) | CNS Depression Risk shared by 4 drugs | Warn patients of the potential danger of self-administration of benzodiazepine or other CNS depressants while under treatment with Buprenorphine and Naloxone Sublingual Tablets. | Suboxone / warnings_and_cautions |
| buprenorphine, clonazepam | respiratory depression | major | HIT | CNS Depression Risk shared by 4 drugs | Warn patients of the potential danger of self-administration of benzodiazepine or other CNS depressants while under treatment with Buprenorphine and Naloxone Sublingual Tablets. | Suboxone / warnings_and_cautions |
| buprenorphine, gabapentin | respiratory depression | major | HIT | CNS Depression Risk shared by 4 drugs | Warn patients of the potential danger of self-administration of benzodiazepine or other CNS depressants while under treatment with Buprenorphine and Naloxone Sublingual Tablets. | Suboxone / warnings_and_cautions |
| buprenorphine, quetiapine, clonazepam, gabapentin | CNS depression | moderate | MISS (drugs resolved but no alert) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L37: P-gp inhibitors on dabigatran; dronedarone on digoxin, verapamil, simvastatin; rate-control stacking

Text sent (newline variant):

```
Pradaxa 150 mg twice daily
Multaq 400 mg twice daily with meals
Calan SR 240 mg once daily
Lanoxin 0.125 mg once daily
Zocor 20 mg once daily at bedtime
Lasix 20 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| dabigatran, dronedarone | P-gp | major | MISS (category outside the checker's rules) |  |  |  |
| dabigatran, verapamil | P-gp | moderate | MISS (category outside the checker's rules) |  |  |  |
| digoxin, dronedarone | digoxin toxicity | major | MISS (category outside the checker's rules) |  |  |  |
| digoxin, verapamil | digoxin toxicity | moderate | MISS (category outside the checker's rules) |  |  |  |
| dronedarone, verapamil | bradycardia/AV block | major | MISS (category outside the checker's rules) |  |  |  |
| simvastatin, dronedarone | myopathy/rhabdomyolysis | moderate | MISS (category outside the checker's rules) |  |  |  |
| simvastatin, verapamil | myopathy/rhabdomyolysis | moderate | MISS (category outside the checker's rules) |  |  |  |
| furosemide, digoxin, dronedarone | electrolyte | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: Calan SR 240 mg once daily (unresolved: RxNorm found no close name)
False positives: none
Total digoxin: match (expected 0.125 mg = 125 mcg; checker 0.125 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L38: Hidden duplicate: active metabolite prescribed alongside its parent; three antipsychotics

Text sent (newline variant):

```
Risperdal 2 mg twice daily
Invega 6 mg once daily
Zyprexa 10 mg once daily at bedtime
Cogentin 1 mg twice daily
Klonopin 1 mg twice daily
Lipitor 20 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| risperidone, paliperidone | duplicate therapy | major | MISS (drugs resolved but no alert) |  |  |  |
| risperidone, paliperidone, olanzapine | duplicate therapy | major | MISS (drugs resolved but no alert) |  |  |  |
| benztropine, olanzapine | anticholinergic burden | moderate | MISS (category outside the checker's rules) |  |  |  |
| clonazepam, olanzapine | CNS depression | moderate | MISS (drugs resolved but no alert) |  |  |  |

Unresolved entries: none
False positives: none
Total risperidone moiety: match (expected 4 mg risperidone + 6 mg paliperidone; checker 4 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L39: Macrolide on colchicine and simvastatin; diltiazem as a second CYP3A4/P-gp inhibitor; QT

Text sent (newline variant):

```
Colcrys 0.6 mg twice daily
Ery-Tab 500 mg four times daily
Zocor 40 mg once daily at bedtime
Zyloprim 300 mg once daily
Cardizem CD 240 mg once daily
Lasix 40 mg once daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| colchicine, erythromycin | P-gp | major | MISS (category outside the checker's rules) |  |  |  |
| simvastatin, erythromycin | myopathy/rhabdomyolysis | contraindicated | MISS (drugs resolved but no alert) |  |  |  |
| simvastatin, diltiazem | myopathy/rhabdomyolysis | major | MISS (category outside the checker's rules) |  |  |  |
| colchicine, diltiazem | P-gp | moderate | MISS (category outside the checker's rules) |  |  |  |
| colchicine, simvastatin | myopathy/rhabdomyolysis | moderate | MISS (category outside the checker's rules) |  |  |  |
| erythromycin, diltiazem | QT prolongation | major | MISS (drugs resolved but no alert) |  |  |  |
| furosemide, erythromycin | electrolyte | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L40: Three bedtime hypnotics plus a benzodiazepine; SSRI at its maximum with trazodone

Text sent (newline variant):

```
Desyrel 100 mg once daily at bedtime
Zoloft 200 mg once daily
Belsomra 20 mg once daily at bedtime
Ambien 10 mg once daily at bedtime
Xanax 0.5 mg three times daily as needed, max 3 doses/day
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| trazodone, suvorexant, zolpidem, alprazolam | duplicate therapy | major | PARTIAL (got T15 at major) | CNS Depression Risk shared by 4 drugs | CNS Depressants: Trazodone hydrochloride tablets may enhance effects of alcohol, barbiturates, or other CNS depressants ( 7 ). | Desyrel / drug_interactions |
| trazodone, sertraline | serotonin syndrome | moderate | HIT | Serotonin Syndrome Risk shared by 2 drugs | Serotonin Syndrome: Increased risk when co-administered with other serotonergic agents (e.g., SSRI, SNRI, triptans), but also when taken alone. | Desyrel / warnings_and_cautions |
| trazodone | QT prolongation | minor | HIT | QT Prolongation Risk shared by 2 drugs | The use of trazodone hydrochloride tablets should be avoided in patients with known QT prolongation or in combination with other drugs that are inhibitors of CYP3A4 (e.g., itracon… | Desyrel / warnings_and_cautions |
| sertraline | dose ceiling | minor | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: max 3 doses/day (unresolved: RxNorm found no close name)
False positives: none
Total alprazolam: match (expected 1.5 mg max; checker 1.5 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order

## L41: Data-entry traps: brand and generic of one drug; same dose in different units; one ingredient under two brands

Text sent (newline variant):

```
Zoloft 50 mg once daily
sertraline 50 mg once daily
Synthroid 0.1 mg once daily
levothyroxine 100 mcg once daily
Motrin 800 mg three times daily
Advil 200 mg 2 tablets twice daily
```

| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |
| --- | --- | --- | --- | --- | --- | --- |
| sertraline, sertraline | duplicate entry | major | PARTIAL (got shared_ingredient at minor) | Zoloft and Sertraline share sertraline | base ingredients: sertraline | Zoloft / |
| levothyroxine, levothyroxine | unit normalization | major | MISS (category outside the checker's rules) |  |  |  |
| ibuprofen, ibuprofen | dose ceiling | major | MISS (category outside the checker's rules) |  |  |  |
| sertraline, ibuprofen | bleeding | moderate | MISS (category outside the checker's rules) |  |  |  |

Unresolved entries: none
False positives: none
Total sertraline: match (expected 100 mg if both lines are real; checker 100 mg)
Total levothyroxine: match (expected 200 mcg if both lines are real (0.1 mg + 100 mcg); checker 0.2 mg)
Total ibuprofen: match (expected 3,200 mg; checker 3200 mg)
Variants: identical alert sets across newline, comma, semicolon, and reversed order
