# Diff: 2026-09-23_0648 → 2026-09-23_0804

## Metrics

| Metric | 2026-09-23_0648 | 2026-09-23_0804 |
|---|---|---|
| Recall D (hits/expected) | 0/13 | 13/13 |
| Recall C (hits/expected) | 0/103 | 103/103 |
| Recall B (hits/expected) | 0/68 | 68/68 |
| Recall A (hits/expected) | 0/12 | 12/12 |
| False positives on L11, L29 | 0 | 0 |
| False positives, all rules | 0 | 0 |
| Totals correct | 0 | 33 |
| Duplicate/unit/weekly/combination cases resolved | 0 | 22 |
| Grouping statements present | 0 | 43 |
| C/D flags with a working drug-specific link | 0 | 117 |
| C/D flags shown | 0 | 117 |
| Flags shown | 0 | 232 |
| Entries not resolved | 244 | 0 |
| Input focused on load (lists) | 41 | 41 |
| Median seconds to results | 3.243 | 0.407 |
| Worst seconds to results | 4.467 | 1.618 |

## Regressions (P0): 0

None.

## Improvements: 196

| List | Item | Before | After | Site grade now |
|---|---|---|---|---|
| L01 | olanzapine, olanzapine (duplicate entry) | MISS | HIT | C (= B) |
| L01 | alprazolam, zolpidem, olanzapine (CNS depression) | MISS | HIT | D (= C) |
| L01 | amphetamine/dextroamphetamine (dose ceiling) | MISS | HIT | C (= B) |
| L01 | amphetamine/dextroamphetamine, alprazolam, olanzapine (opposing pharmacology) | MISS | HIT | A (= A) |
| L02 | sertraline, tramadol, sumatriptan, cyclobenzaprine, ondansetron (serotonin syndrome) | MISS | HIT | D (= C) |
| L02 | tramadol, sertraline (seizure threshold) | MISS | HIT | C (= B) |
| L02 | ondansetron, tramadol (efficacy loss) | MISS | HIT | A (= A) |
| L03 | citalopram, haloperidol, azithromycin, fluconazole (QT prolongation) | MISS | HIT | D (= C) |
| L03 | citalopram, fluconazole (CYP inhibition) | MISS | HIT | D (= C) |
| L03 | haloperidol, fluconazole (CYP inhibition) | MISS | HIT | C (= B) |
| L03 | furosemide, citalopram, haloperidol, azithromycin, fluconazole (electrolyte) | MISS | HIT | C (= B) |
| L04 | lithium, lisinopril (lithium toxicity) | MISS | HIT | D (= C) |
| L04 | lithium, hydrochlorothiazide (lithium toxicity) | MISS | HIT | D (= C) |
| L04 | lithium, ibuprofen (lithium toxicity) | MISS | HIT | D (= C) |
| L04 | lisinopril, hydrochlorothiazide, ibuprofen (nephrotoxicity) | MISS | HIT | D (= C) |
| L04 | metformin, topiramate (metabolic acidosis) | MISS | HIT | C (= B) |
| L04 | topiramate, hydrochlorothiazide (electrolyte) | MISS | HIT | A (= A) |
| L05 | warfarin, sulfamethoxazole/trimethoprim (bleeding) | MISS | HIT | D (= C) |
| L05 | warfarin, amiodarone (bleeding) | MISS | HIT | D (= C) |
| L05 | warfarin, aspirin, clopidogrel (bleeding) | MISS | HIT | D (= C) |
| L05 | escitalopram, warfarin, aspirin, clopidogrel (bleeding) | MISS | HIT | D (= C) |
| L05 | escitalopram, amiodarone (QT prolongation) | MISS | HIT | D (= C) |
| L06 | oxycodone ER, oxycodone IR (duplicate entry) | MISS | HIT | D (= C) |
| L06 | oxycodone, clonazepam (respiratory depression) | MISS | HIT | D (= C) |
| L06 | oxycodone, gabapentin (respiratory depression) | MISS | HIT | D (= C) |
| L06 | oxycodone, carisoprodol, clonazepam (CNS depression) | MISS | HIT | D (= C) |
| L06 | hydroxyzine, oxycodone, clonazepam (CNS depression) | MISS | HIT | D (= C) |
| L07 | phenelzine, bupropion (hypertensive crisis) | MISS | HIT | E (= D) |
| L07 | phenelzine, meperidine (serotonin syndrome) | MISS | HIT | E (= D) |
| L07 | phenelzine, methylphenidate (hypertensive crisis) | MISS | HIT | E (= D) |
| L07 | phenelzine, amlodipine (hypotension) | MISS | HIT | C (= B) |
| L08 | clozapine, carbamazepine (myelosuppression) | MISS | HIT | D (= C) |
| L08 | clozapine, fluvoxamine (CYP inhibition) | MISS | HIT | D (= C) |
| L08 | clozapine, ciprofloxacin (CYP inhibition) | MISS | HIT | D (= C) |
| L08 | clozapine, lorazepam (respiratory depression) | MISS | HIT | D (= C) |
| L08 | carbamazepine, divalproex (CYP induction) | MISS | HIT | C (= B) |
| L08 | clozapine, ciprofloxacin (QT prolongation) | MISS | HIT | C (= B) |
| L09 | fluoxetine, paroxetine (duplicate therapy) | MISS | HIT | D (= C) |
| L09 | fluoxetine, paroxetine, tamoxifen (efficacy loss) | MISS | HIT | D (= C) |
| L09 | fluoxetine, paroxetine, metoprolol (CYP inhibition) | MISS | HIT | C (= B) |
| L09 | fluoxetine, paroxetine, naproxen (bleeding) | MISS | HIT | C (= B) |
| L10 | simvastatin, clarithromycin (myopathy/rhabdomyolysis) | MISS | HIT | E (= D) |
| L10 | spironolactone, enalapril, potassium chloride (hyperkalemia) | MISS | HIT | D (= C) |
| L10 | methotrexate (dosing frequency) | MISS | HIT | — |
| L12 | olanzapine/fluoxetine, fluoxetine (duplicate therapy) | MISS | HIT | D (= C) |
| L12 | hydrocodone/acetaminophen, acetaminophen (dose ceiling) | MISS | HIT | D (= C) |
| L12 | alprazolam, alprazolam ER (duplicate entry) | MISS | HIT | C (= B) |
| L12 | hydrocodone, alprazolam, olanzapine (respiratory depression) | MISS | HIT | D (= C) |
| L12 | fluoxetine, hydrocodone (CYP inhibition) | MISS | HIT | B (= B) |
| L13 | linezolid, venlafaxine (serotonin syndrome) | MISS | HIT | E (= D) |
| L13 | linezolid, buspirone, fentanyl, metoclopramide (serotonin syndrome) | MISS | HIT | D (= C) |
| L13 | fentanyl, methocarbamol (respiratory depression) | MISS | HIT | D (= C) |
| L13 | metoclopramide, venlafaxine, buspirone (serotonin syndrome) | MISS | HIT | D (= C) |
| L14 | fentanyl, diazepam, temazepam (respiratory depression) | MISS | HIT | D (= C) |
| L14 | diazepam, temazepam (duplicate therapy) | MISS | HIT | D (= C) |
| L14 | fentanyl, pregabalin (respiratory depression) | MISS | HIT | D (= C) |
| L14 | fentanyl, promethazine (respiratory depression) | MISS | HIT | D (= C) |
| L14 | tizanidine, fentanyl, diazepam, temazepam, pregabalin, promethazine (CNS depression) | MISS | HIT | D (= C) |
| L15 | metoprolol, diltiazem (bradycardia/AV block) | MISS | HIT | D (= C) |
| L15 | digoxin, amiodarone (digoxin toxicity) | MISS | HIT | D (= C) |
| L15 | digoxin, diltiazem (digoxin toxicity) | MISS | HIT | C (= B) |
| L15 | digoxin, metoprolol, diltiazem, amiodarone (bradycardia/AV block) | MISS | HIT | D (= C) |
| L15 | donepezil, metoprolol, diltiazem, digoxin (bradycardia/AV block) | MISS | HIT | D (= C) |
| L15 | furosemide, digoxin, amiodarone (electrolyte) | MISS | HIT | C (= B) |
| L15 | amiodarone, metoprolol (CYP inhibition) | MISS | HIT | C (= B) |
| L16 | sildenafil, nitroglycerin (hypotension) | MISS | HIT | E (= D) |
| L16 | sildenafil, isosorbide mononitrate (hypotension) | MISS | HIT | E (= D) |
| L16 | sildenafil, tamsulosin (hypotension) | MISS | HIT | C (= B) |
| L16 | clonidine, carvedilol (bradycardia/AV block) | MISS | HIT | D (= C) |
| L16 | carvedilol, tamsulosin, clonidine, isosorbide mononitrate (hypotension) | MISS | HIT | C (= B) |
| L17 | trimethoprim, spironolactone, losartan, potassium chloride (hyperkalemia) | MISS | HIT | D (= C) |
| L17 | losartan, spironolactone, celecoxib (nephrotoxicity) | MISS | HIT | D (= C) |
| L17 | empagliflozin, spironolactone, celecoxib, losartan (nephrotoxicity) | MISS | HIT | D (= C) |
| L18 | amitriptyline, oxybutynin, hydroxyzine, benztropine, paroxetine (anticholinergic burden) | MISS | HIT | D (= C) |
| L18 | donepezil, amitriptyline, oxybutynin, hydroxyzine, benztropine (therapeutic antagonism) | MISS | HIT | D (= C) |
| L18 | paroxetine, amitriptyline (CYP inhibition) | MISS | HIT | D (= C) |
| L18 | amitriptyline, hydroxyzine (QT prolongation) | MISS | HIT | C (= B) |
| L19 | bupropion, tramadol, theophylline, ciprofloxacin, quetiapine (seizure threshold) | MISS | HIT | D (= C) |
| L19 | theophylline, ciprofloxacin (CYP inhibition) | MISS | HIT | D (= C) |
| L19 | ciprofloxacin, quetiapine (QT prolongation) | MISS | HIT | C (= B) |
| L19 | bupropion, tramadol (CYP inhibition) | MISS | HIT | C (= B) |
| L20 | rifampin, rivaroxaban (efficacy loss) | MISS | HIT | D (= C) |
| L20 | rifampin, norgestimate/ethinyl estradiol (efficacy loss) | MISS | HIT | D (= C) |
| L20 | rifampin, tacrolimus (efficacy loss) | MISS | HIT | D (= C) |
| L20 | rifampin, lurasidone (CYP induction) | MISS | HIT | E (= D) |
| L20 | rifampin, methadone (efficacy loss) | MISS | HIT | D (= C) |
| L21 | ketoconazole, triazolam (CYP inhibition) | MISS | HIT | E (= D) |
| L21 | ketoconazole, alprazolam (CYP inhibition) | MISS | HIT | E (= D) |
| L21 | ketoconazole, apixaban (bleeding) | MISS | HIT | D (= C) |
| L21 | ketoconazole, atorvastatin (myopathy/rhabdomyolysis) | MISS | HIT | D (= C) |
| L21 | ketoconazole, amlodipine (CYP inhibition) | MISS | HIT | B (= B) |
| L22 | tacrolimus, fluconazole (CYP inhibition) | MISS | HIT | D (= C) |
| L22 | tacrolimus, fluconazole, ondansetron (QT prolongation) | MISS | HIT | D (= C) |
| L22 | mycophenolate mofetil, omeprazole (absorption/timing) | MISS | HIT | C (= B) |
| L22 | simvastatin, fluconazole (myopathy/rhabdomyolysis) | MISS | HIT | C (= B) |
| L22 | tacrolimus, omeprazole (CYP inhibition) | MISS | HIT | A (= A) |
| L23 | glipizide, insulin glargine, semaglutide (hypoglycemia) | MISS | HIT | D (= C) |
| L23 | glipizide, sulfamethoxazole/trimethoprim (hypoglycemia) | MISS | HIT | D (= C) |
| L23 | levofloxacin, glipizide, insulin glargine (hypoglycemia) | MISS | HIT | D (= C) |
| L23 | propranolol, glipizide, insulin glargine (hypoglycemia) | MISS | HIT | D (= C) |
| L23 | semaglutide, glipizide (absorption/timing) | MISS | HIT | A (= A) |
| L24 | hydrocodone/acetaminophen, oxycodone/acetaminophen (duplicate therapy) | MISS | HIT | D (= C) |
| L24 | acetaminophen, acetaminophen (duplicate entry) | MISS | HIT | D (= C) |
| L24 | zolpidem, eszopiclone (duplicate therapy) | MISS | HIT | D (= C) |
| L24 | meloxicam, naproxen sodium (duplicate therapy) | MISS | HIT | D (= C) |
| L24 | hydrocodone, oxycodone, zolpidem, eszopiclone (CNS depression) | MISS | HIT | D (= C) |
| L25 | methadone, quetiapine, ondansetron, levofloxacin, fluconazole (QT prolongation) | MISS | HIT | D (= C) |
| L25 | methadone, fluconazole (CYP inhibition) | MISS | HIT | D (= C) |
| L25 | methadone, venlafaxine (serotonin syndrome) | MISS | HIT | D (= C) |
| L25 | methadone, quetiapine (respiratory depression) | MISS | HIT | D (= C) |
| L25 | quetiapine, fluconazole (CYP inhibition) | MISS | HIT | D (= C) |
| L26 | divalproex, lamotrigine (CYP inhibition) | MISS | HIT | D (= C) |
| L26 | carbamazepine, lamotrigine (CYP induction) | MISS | HIT | C (= B) |
| L26 | carbamazepine, divalproex (CYP induction) | MISS | HIT | C (= B) |
| L26 | divalproex, topiramate (hyperammonemia) | MISS | HIT | D (= C) |
| L26 | divalproex, aspirin (bleeding) | MISS | HIT | C (= B) |
| L26 | carbamazepine, clonazepam (CYP induction) | MISS | HIT | A (= A) |
| L26 | divalproex, lamotrigine, topiramate, carbamazepine, clonazepam (CNS depression) | MISS | HIT | D (= C) |
| L27 | carbidopa/levodopa, metoclopramide (therapeutic antagonism) | MISS | HIT | D (= C) |
| L27 | carbidopa/levodopa, haloperidol (therapeutic antagonism) | MISS | HIT | D (= C) |
| L27 | rasagiline, meperidine (serotonin syndrome) | MISS | HIT | E (= D) |
| L27 | rasagiline, escitalopram (serotonin syndrome) | MISS | HIT | D (= C) |
| L27 | metoclopramide, haloperidol (duplicate therapy) | MISS | HIT | D (= C) |
| L27 | haloperidol, escitalopram (QT prolongation) | MISS | HIT | C (= B) |
| L28 | darunavir/cobicistat, atorvastatin (myopathy/rhabdomyolysis) | MISS | HIT | D (= C) |
| L28 | darunavir/cobicistat, alprazolam (CYP inhibition) | MISS | HIT | D (= C) |
| L28 | darunavir/cobicistat, fluticasone propionate (adrenal suppression) | MISS | HIT | D (= C) |
| L28 | darunavir/cobicistat, sildenafil (hypotension) | MISS | HIT | D (= C) |
| L28 | darunavir/cobicistat, tenofovir disoproxil fumarate (nephrotoxicity) | MISS | HIT | C (= B) |
| L30 | levothyroxine, calcium carbonate (absorption/timing) | MISS | HIT | C (= B) |
| L30 | levothyroxine, ferrous sulfate (absorption/timing) | MISS | HIT | C (= B) |
| L30 | ciprofloxacin, calcium carbonate (absorption/timing) | MISS | HIT | D (= C) |
| L30 | ciprofloxacin, ferrous sulfate (absorption/timing) | MISS | HIT | D (= C) |
| L30 | clopidogrel, omeprazole (efficacy loss) | MISS | HIT | D (= C) |
| L30 | ferrous sulfate, omeprazole (absorption/timing) | MISS | HIT | A (= A) |
| L30 | levothyroxine, omeprazole (absorption/timing) | MISS | HIT | A (= A) |
| L31 | vancomycin, gentamicin (nephrotoxicity) | MISS | HIT | D (= C) |
| L31 | vancomycin, piperacillin/tazobactam (nephrotoxicity) | MISS | HIT | D (= C) |
| L31 | gentamicin, furosemide (ototoxicity) | MISS | HIT | D (= C) |
| L31 | ketorolac, lisinopril, furosemide (nephrotoxicity) | MISS | HIT | D (= C) |
| L31 | ketorolac, gentamicin, vancomycin (nephrotoxicity) | MISS | HIT | D (= C) |
| L31 | ketorolac, lisinopril (hyperkalemia) | MISS | HIT | C (= B) |
| L32 | methotrexate, sulfamethoxazole/trimethoprim (myelosuppression) | MISS | HIT | D (= C) |
| L32 | azathioprine, allopurinol (myelosuppression) | MISS | HIT | D (= C) |
| L32 | methotrexate, ibuprofen (nephrotoxicity) | MISS | HIT | C (= B) |
| L32 | methotrexate, azathioprine (myelosuppression) | MISS | HIT | C (= B) |
| L32 | methotrexate (dosing frequency) | MISS | HIT | — |
| L33 | phenytoin, norgestimate/ethinyl estradiol (efficacy loss) | MISS | HIT | D (= C) |
| L33 | phenytoin, fluoxetine (CYP inhibition) | MISS | HIT | D (= C) |
| L33 | phenytoin, fluconazole (CYP inhibition) | MISS | HIT | D (= C) |
| L33 | phenytoin, warfarin (bleeding) | MISS | HIT | D (= C) |
| L33 | warfarin, fluconazole (bleeding) | MISS | HIT | D (= C) |
| L33 | warfarin, fluoxetine (bleeding) | MISS | HIT | C (= B) |
| L33 | phenytoin, atorvastatin (efficacy loss) | MISS | HIT | B (= B) |
| L34 | guanfacine, clonidine (duplicate therapy) | MISS | HIT | D (= C) |
| L34 | paroxetine, atomoxetine (CYP inhibition) | MISS | HIT | D (= C) |
| L34 | lisdexamfetamine, atomoxetine (duplicate therapy) | MISS | HIT | C (= B) |
| L34 | lisdexamfetamine, paroxetine (serotonin syndrome) | MISS | HIT | C (= B) |
| L34 | quetiapine, guanfacine, clonidine (hypotension) | MISS | HIT | C (= B) |
| L34 | lisdexamfetamine, quetiapine (opposing pharmacology) | MISS | HIT | A (= A) |
| L35 | sumatriptan, rizatriptan (duplicate therapy) | MISS | HIT | D (= C) |
| L35 | rizatriptan, propranolol (CYP inhibition) | MISS | HIT | C (= B) |
| L35 | sumatriptan, rizatriptan, amitriptyline (serotonin syndrome) | MISS | HIT | D (= C) |
| L35 | butalbital, amitriptyline, topiramate (CNS depression) | MISS | HIT | C (= B) |
| L35 | butalbital/acetaminophen/caffeine (combination parsing) | MISS | HIT | — |
| L36 | buprenorphine/naloxone, naltrexone (therapeutic antagonism) | MISS | HIT | E (= D) |
| L36 | buprenorphine, clonazepam (respiratory depression) | MISS | HIT | D (= C) |
| L36 | buprenorphine, gabapentin (respiratory depression) | MISS | HIT | D (= C) |
| L36 | buprenorphine, quetiapine, clonazepam, gabapentin (CNS depression) | MISS | HIT | D (= C) |
| L37 | dabigatran, dronedarone (P-gp) | MISS | HIT | D (= C) |
| L37 | dabigatran, verapamil (P-gp) | MISS | HIT | C (= B) |
| L37 | digoxin, dronedarone (digoxin toxicity) | MISS | HIT | D (= C) |
| L37 | digoxin, verapamil (digoxin toxicity) | MISS | HIT | C (= B) |
| L37 | dronedarone, verapamil (bradycardia/AV block) | MISS | HIT | D (= C) |
| L37 | simvastatin, dronedarone (myopathy/rhabdomyolysis) | MISS | HIT | D (= C) |
| L37 | simvastatin, verapamil (myopathy/rhabdomyolysis) | MISS | HIT | D (= C) |
| L37 | furosemide, digoxin, dronedarone (electrolyte) | MISS | HIT | C (= B) |
| L38 | risperidone, paliperidone (duplicate therapy) | MISS | HIT | D (= C) |
| L38 | risperidone, paliperidone, olanzapine (duplicate therapy) | MISS | HIT | D (= C) |
| L38 | benztropine, olanzapine (anticholinergic burden) | MISS | HIT | C (= B) |
| L38 | clonazepam, olanzapine (CNS depression) | MISS | HIT | D (= C) |
| L39 | colchicine, erythromycin (P-gp) | MISS | HIT | D (= C) |
| L39 | simvastatin, erythromycin (myopathy/rhabdomyolysis) | MISS | HIT | E (= D) |
| L39 | simvastatin, diltiazem (myopathy/rhabdomyolysis) | MISS | HIT | D (= C) |
| L39 | colchicine, diltiazem (P-gp) | MISS | HIT | C (= B) |
| L39 | colchicine, simvastatin (myopathy/rhabdomyolysis) | MISS | HIT | C (= B) |
| L39 | erythromycin, diltiazem (QT prolongation) | MISS | HIT | D (= C) |
| L39 | furosemide, erythromycin (electrolyte) | MISS | HIT | C (= B) |
| L40 | trazodone, suvorexant, zolpidem, alprazolam (duplicate therapy) | MISS | HIT | D (= C) |
| L40 | trazodone, sertraline (serotonin syndrome) | MISS | HIT | C (= B) |
| L40 | trazodone (QT prolongation) | MISS | HIT | A (= A) |
| L40 | sertraline (dose ceiling) | MISS | HIT | A (= A) |
| L41 | sertraline, sertraline (duplicate entry) | MISS | HIT | D (= C) |
| L41 | levothyroxine, levothyroxine (unit normalization) | MISS | HIT | D (= C) |
| L41 | ibuprofen, ibuprofen (dose ceiling) | MISS | HIT | D (= C) |
| L41 | sertraline, ibuprofen (bleeding) | MISS | HIT | C (= B) |
