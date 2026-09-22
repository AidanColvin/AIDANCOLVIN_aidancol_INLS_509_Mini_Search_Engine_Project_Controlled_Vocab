# Phase 3: tag

## What was built

All 17 rule functions in the seven files Section 6 names (`safety.py`, `route.py`, `population.py`, `patient_info.py`, `dosing.py`, `dea.py`, `product.py`, `interaction.py`), the indexing-time hierarchy expansion (`hierarchy.py`), a class-name gazetteer built only from the collection's own `pharm_class_epc`/`pharm_class_moa` values and the FDA enzyme table (`gazetteer.py`), the orchestrator (`tagger.py`), and the parallel, cached tagging job (`run.py`) with a `tag` CLI command.

## Commands run and results

```
PYTHONPATH=src .venv/bin/python -m rx_label_search tag --workers 8
.venv/bin/python -m pytest -q
```

Tagging the full 2,481-label collection took 5 seconds with 8 worker processes. Cache keys are hashed from label id, set id, effective time, and the rule version, so an unchanged label is skipped on the next run.

Term frequencies across the collection:

| Term | Labels | Share |
| :--- | ---: | ---: |
| T01 | 747 | 30.1% |
| T02 | 1,338 | 53.9% |
| T03 | 463 | 18.7% |
| T04 | 1,393 | 56.1% |
| T05 | 561 | 22.6% |
| T06 | 547 | 22.0% |
| T07 | 75 | 3.0% |
| T08 | 1,938 | 78.1% |
| T09 | 1,295 | 52.2% |
| T10 | 28 | 1.1% |
| T11 | 722 | 29.1% |
| T12 | 384 | 15.5% |
| T13 | 614 | 24.7% |
| T14 | 121 | 4.9% |
| T15 | 234 | 9.4% |
| T16 | 217 | 8.7% |
| T17 | 282 | 11.4% |

Tests: 229 passed, 0 failed, 0 skipped.

## Commits and push

This report's commit follows the Phase 2 commit `2aaf7f1`, pushed to `origin/build/rx-label-search`.

## Label-driven differences

* All four Phase 3 done-criteria checks pass against the real fixture labels: OxyContin carries T01, T02, T05, T07, T08, T09, T10, T13, and T15; cyclobenzaprine carries T14 and T15; gabapentin carries T06 but not T01; Entresto carries T09 but not T08.
* OxyContin's label also carries T03 (`pediatric_use` states "The safety and efficacy of OXYCONTIN have been established in pediatric patients ages 11 to 16 years") and T12 (a hepatic dose reduction in `dosage_and_administration`), neither of which the prompt's "at least" list required or excluded.
* Every one of the 2,481 tagged labels passes the three consistency rules with zero violations.

## What I should check by hand

* T17's residual imprecision, recorded in `OPEN_QUESTIONS.md` item 16: after two rounds of fixing false positives (a gazetteer footnote-transcription bug, and self-referential and own-name mentions), a random sample of matched sentences was overwhelmingly correct, with a small remainder that names a drug's own pharmacologic class in words (for example an ACE inhibitor's own contraindication) rather than a true combination partner. This term drives the checker's pair alerts, so I recommend spot-checking a sample of T17-tagged labels before relying on pair alerts clinically.
* T04's table-column reader (item 14) and T03's cue patterns (item 15) are heuristics over real but varied SPL text; they were checked against the fixture labels only.
* T06/T12's dose-change cue (item 17) accepts a bare "dosage adjustment ... is necessary" statement, matching Entresto's and gabapentin's actual wording, without requiring a specific number.

## Open questions

`OPEN_QUESTIONS.md` items 14 to 17.
