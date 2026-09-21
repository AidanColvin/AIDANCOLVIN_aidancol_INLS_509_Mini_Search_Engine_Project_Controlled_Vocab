# Phase 1: collect

## What was built

The openFDA manifest and bulk download job (`collect/fetch.py`, `collect/manifest.py`, `collect/run.py`), an incremental zip-and-JSON reader that never loads a whole partition, the three scope filters and newest-per-ingredient-set selection, the stats file, the name dictionary built before de-duplication, a collection verifier, the twelve fixture labels plus 34 RxNorm response fixtures with fetch dates, and the `download`, `collect`, and `verify-collection` commands.

## Commands run and results

```
PYTHONPATH=src .venv/bin/python -m rx_label_search download
PYTHONPATH=src .venv/bin/python -m rx_label_search collect --workers 10
PYTHONPATH=src .venv/bin/python -m rx_label_search verify-collection
.venv/bin/python -m pytest -q
```

Collection build on 2026-09-21 against the 2026-09-18 export (14 partitions, 1,774 MB zipped), 15 seconds wall clock with 10 workers:

| Stage | Labels |
| :--- | ---: |
| Total records | 262,883 |
| After filter 1: human prescription | 36,987 |
| After filter 2: has openfda | 36,987 |
| After filter 2b: has substance_name | 36,325 |
| After filter 3: newest per ingredient set | 2,481 |

`verify-collection` reported: 2,481 records, one per ingredient set, all human prescription with openfda. `data/build/collection.jsonl` is 232 MB and is gitignored.

Tests: 49 passed, 0 failed, 0 skipped.

## Commits and push

Phase 0 commit `36e295e` pushed to `origin/build/rx-label-search`. The Phase 1 commit follows this report.

## Label-driven differences

None yet; no expected values were asserted in this phase.

## What to check by hand

* The 662 labels with a non-empty `openfda` but no `substance_name` are dropped and counted under filter 2b. Open question 2 explains why.
* The stats file reports the count after each numbered filter in the prompt's order; filter 2 removes nothing after filter 1 because product type lives inside `openfda`.

## Open questions

`OPEN_QUESTIONS.md` items 1, 2, 6, and 7.
