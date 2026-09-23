# Generalization lists G01–G06

Written for TEST_PACK.md Phase 3's generalization check on 2026-09-23. Each patient is built from a rulebook row (TEST_PACK.md Section 3) that lists L01–L41 do not exercise, and uses drugs the pack never pairs. Severities follow the rulebook row's own words. Contraindicated means a labeled contraindication. Major means a boxed warning, or seizures or treatment failure. Moderate means a monitored or dose-adjusted effect. The lists run through the public site exactly like Phase 1 and are graded with the same grader.

## Section 5 — Lists

G01
Depakote (divalproex sodium) 500 mg twice daily = 1000 mg/day, Merrem (meropenem) 1 g IV every 8 hours = 3 g/day, Singulair (montelukast) 10 mg once daily = 10 mg/day

G02
Zanaflex (tizanidine) 4 mg three times daily = 12 mg/day, Cipro (ciprofloxacin) 500 mg twice daily = 1000 mg/day, Singulair (montelukast) 10 mg once daily = 10 mg/day

G03
Tylenol with Codeine (acetaminophen/codeine) 300/30 mg every 6 hours as needed max 4 doses/day = 1200/120 mg/day max, Paxil (paroxetine) 20 mg once daily = 20 mg/day, Singulair (montelukast) 10 mg once daily = 10 mg/day

G04
Levaquin (levofloxacin) 750 mg once daily = 750 mg/day, Deltasone (prednisone) 40 mg once daily = 40 mg/day, Singulair (montelukast) 10 mg once daily = 10 mg/day

G05
Microzide (hydrochlorothiazide) 25 mg once daily = 25 mg/day, Zoloft (sertraline) 100 mg once daily = 100 mg/day, Tegretol (carbamazepine) 200 mg twice daily = 400 mg/day

G06
Adempas (riociguat) 1 mg three times daily = 3 mg/day, Imdur (isosorbide mononitrate ER) 30 mg once daily = 30 mg/day, Singulair (montelukast) 10 mg once daily = 10 mg/day

## Section 6 — Answer key

```json
{"answer_key": {
 "G01": {"theme": "Rulebook row 32", "expected": [{"drugs": ["divalproex", "meropenem"], "category": "efficacy loss", "severity": "major", "why": "Carbapenems block valproate-glucuronide recycling; valproate levels fall 60-100% within 24 h; breakthrough seizures (row 32)."}], "should_not_flag": ["montelukast"]},
 "G02": {"theme": "Rulebook row 4", "expected": [{"drugs": ["tizanidine", "ciprofloxacin"], "category": "CYP inhibition", "severity": "contraindicated", "why": "CYP1A2 inhibition raises tizanidine AUC about 10-fold; label contraindication (row 4)."}], "should_not_flag": ["montelukast"]},
 "G03": {"theme": "Rulebook row 35", "expected": [{"drugs": ["codeine", "paroxetine"], "category": "CYP inhibition", "severity": "moderate", "why": "CYP2D6 inhibition blocks conversion of codeine to morphine: analgesic failure (row 35)."}], "should_not_flag": ["montelukast"]},
 "G04": {"theme": "Rulebook row 36", "expected": [{"drugs": ["levofloxacin", "prednisone"], "category": "tendon rupture", "severity": "major", "why": "Fluoroquinolone with a systemic corticosteroid: tendinopathy and Achilles rupture; boxed warning (row 36)."}], "should_not_flag": ["montelukast"]},
 "G05": {"theme": "Rulebook row 17", "expected": [{"drugs": ["hydrochlorothiazide", "sertraline", "carbamazepine"], "category": "electrolyte", "severity": "moderate", "why": "Thiazide natriuresis plus the SIADH-like effect of an SSRI and carbamazepine: hyponatremia (row 17)."}]},
 "G06": {"theme": "Rulebook row 21", "expected": [{"drugs": ["riociguat", "isosorbide mononitrate"], "category": "hypotension", "severity": "contraindicated", "why": "Nitrate with riociguat: cGMP accumulation and refractory hypotension; contraindicated (row 21)."}], "should_not_flag": ["montelukast"]}
}}
```
