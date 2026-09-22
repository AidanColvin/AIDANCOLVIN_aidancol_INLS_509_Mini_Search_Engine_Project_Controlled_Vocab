# Phase 6: check

## What was built

Heuristic tiers from the label section (`tiers.py`), DailyMed evidence links (`evidence.py`), group alerts for shared T14/T15/T16 (`groups.py`), pair alerts for T17 against another listed drug's name, base ingredient, or pharmacologic class (`pairs.py`), duplication flags for shared base ingredients and cited active-metabolite pairs (`duplicates.py`), the checker orchestration (`checker.py`), the Section 3.5 report formatter (`report.py`), the data-build and run jobs (`run.py`), and the `build-checker-data` and `check` CLI commands.

## Commands run and results

```
PYTHONPATH=src .venv/bin/python -m rx_label_search build-checker-data
PYTHONPATH=src .venv/bin/python -m rx_label_search check "<medication list>" [--no-rxnorm]
.venv/bin/python -m pytest -q
```

Tests: 393 passed, 0 failed, 0 skipped.

## Section 3.6 acceptance test

Built entirely from fixture labels per the section's own instruction, not the live collection (see `OPEN_QUESTIONS.md` items for the amphetamine-salts and desvenlafaxine ambiguity this avoids). All checks pass:

* Seven entries parse with daily totals 10, 60, 10, 50, 50, 30, 300 mg/day.
* "trazdone" resolves to trazodone; "Flexril" resolves through RxNorm to Flexeril, then to cyclobenzaprine, with the full chain shown.
* Adderall rolls up to exactly amphetamine and dextroamphetamine.
* Schedules: amphetamine (Adderall XR fixture) Schedule II, zolpidem Schedule IV, pregabalin Schedule V; the other four entries show no schedule.
* Group alerts fire for T14 (serotonin syndrome, 4 members) and T15 (CNS depression, 4 members).
* No duplication flag on the seven-entry list.
* venlafaxine plus desvenlafaxine gives a cited active-metabolite flag; Adderall plus a dextroamphetamine-only product gives a shared-ingredient flag.
* The notice and "No warning found in the labels checked." wording are verbatim.

## Label-driven differences

* **Amphetamine's DEA schedule.** The build prompt's acceptance value assumes "amphetamine products CII." The label that actually survives the Part 1 newest-per-ingredient-set filter for the four amphetamine salts, as of the 2026-09-18 openFDA export, is an ANDA generic combination product with no `controlled_substance` field at all (fixture `adderall_current_collection_winner`; the brand `Adderall` and `Adderall XR` labels are both older and get dropped by the collection's own dedup rule). A live `check` run against the real full collection therefore reports no schedule for an "adderall"-typed entry, not CII. The Section 3.6 acceptance test, which Section 3.6 itself says to build from fixture labels, uses the `adderall_xr` fixture instead so the test still exercises the CII rule against real label text; both facts are recorded in `tests/fixtures/FIXTURES.md`.
* Two name-matching precision fixes were made while building this phase, both from real ambiguity the full collection exposed: a query that exactly and fully names one product's single ingredient now resolves to that product even when the same ingredient also appears as one component of an unrelated combination product (`OPEN_QUESTIONS.md` was updated in Phase 2's module, fixed here); and pair matching now checks a drug's rolled-up base ingredient name, not only its raw openfda name strings, so a contraindication that names a plain ingredient (a salt-free name) still matches. See `OPEN_QUESTIONS.md` items 18 to 21.

## ONC high-priority floor test

An automated best-effort check (not a hand-curated one): for each of the 15 ONC pairs, one representative drug name was extracted from each side's printed text and resolved against the built collection; when both sides resolved, `check` ran on that two-drug list.

| Result | Count | Pairs |
| :--- | ---: | :--- |
| Fired an alert | 10 | 1, 2, 3, 4, 6, 9, 11, 12, 13, 15 |
| Both sides resolved but no alert fired | 3 | 5 (Irinotecan–ketoconazole), 10 (Rifampin–ritonavir), 14 (Tranylcypromine–procarbazine) |
| At least one side names only a class, no literal drug could be built | 2 | 7 (Tricyclic antidepressants class), 8 (QT-prolonging class vs. itself) |

Two rule gaps found by this floor test were fixed in this phase (the drug-name gazetteer bug and the active-voice contraindication cue), raising the fired count from 8 to 10 of 13. The three still not firing: pairs 5 and 10 are an artifact of this diagnostic's "first resolvable name" heuristic, which can pick a different member of a multi-drug list than the pair's actual intended partner (recorded in `OPEN_QUESTIONS.md` item 21); pair 14's gap is real: tranylcypromine's contraindications text refers to "the products in Table 1" rather than naming procarbazine in running prose, and T17 reads text fields, not embedded tables.

## What I should check by hand

* The three ONC pairs that did not fire, and whether they matter for your use case; see the table above and `OPEN_QUESTIONS.md` item 21.
* T17's pair-matching precision generally, since it is the checker's highest-tier alert type and still carries the residual imprecision recorded in `OPEN_QUESTIONS.md` items 16 and 20 to 21.

## Open questions

`OPEN_QUESTIONS.md` items 18 to 21.
