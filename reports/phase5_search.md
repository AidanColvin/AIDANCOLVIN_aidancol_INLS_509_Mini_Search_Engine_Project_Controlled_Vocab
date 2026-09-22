# Phase 5: search

## What was built

The tokenizer, the index builder (main text fields plus openfda brand, generic, and substance names), BM25 with `K1 = 1.2` and `B = 0.75` as named module constants, AND/OR facet filtering over stored PDLA tags, snippet extraction, the query orchestrator, the search job and CLI (`build-index`, `query`), and the Part 3 IR evaluation harness (`ir_metrics.py`, reading tab-separated queries and relevance-judgments files) with an `evaluate-search` command.

## Commands run and results

```
PYTHONPATH=src .venv/bin/python -m rx_label_search build-index
PYTHONPATH=src .venv/bin/python -m rx_label_search query "muscle spasm" --term T14 --term T15 --operator AND --limit 3
.venv/bin/python -m pytest -q
```

`build-index` indexed 2,481 documents from the built collection, average length 3,872.4 tokens, in about 3.5 seconds. The sample query above ranks cyclobenzaprine first, matching Appendix C Scenario 3.

Tests: 326 passed, 0 failed, 0 skipped.

## Section 7.6 acceptance scenarios

All three run against the fixture labels and pass:

* Scenario 1 (T06 alone): returns gabapentin, and every hit carries T06.
* Scenario 2 (keyword "hypertension" + T01 AND T02): returns losartan, and every hit carries both T01 and T02. A losartan fixture was added because none of the checker's Section 9.6 fixtures both treat hypertension and carry a boxed warning; see `tests/fixtures/FIXTURES.md`.
* Scenario 3 (keyword "muscle spasm" + T14 AND T15): returns cyclobenzaprine, and every hit carries both T14 and T15.

## Label-driven differences

None; the scenarios pass as specified once the losartan fixture was added.

## What I should check by hand

* No stemming is applied in this version (Section 7 item 3); a query for "spasms" will not match "spasm" unless both literal forms appear in the text. This is documented in the README's search section.
* The IR evaluation harness (`evaluate-search`) is built and tested but has no real queries or relevance judgments file yet; Section 7 item 7 says its report waits for the Part 3 rubric.

## Open questions

None new in this phase; the losartan fixture addition is recorded in `tests/fixtures/FIXTURES.md`.
