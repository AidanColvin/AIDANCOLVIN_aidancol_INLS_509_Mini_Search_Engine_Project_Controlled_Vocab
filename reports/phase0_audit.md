# Phase 0: audit and plan

## What was built

Work branch `build/rx-label-search` from `main`; `pyproject.toml`, `.gitignore`, the commit-msg hook, the style and attribution tests, the record dataclasses, the JSON storage helpers, and the first collect modules with tests. Facts were verified with web fetches and live requests and recorded in `reports/VERIFIED_FACTS.md`.

## Repository before the build

| Path | Read-only under Section 9.2 |
| :--- | :--- |
| `LICENSE` | Yes |
| `README.md` | No (extend only) |
| `MiniVocab_Aidan_Colvin_aidancol.md` | Yes (write-up) |
| `document_collection_part_1/document_collection_part_1_v1_submitted.md` | Yes (write-up) |
| `document_collection_part_1/document_collection_part_1_v2_updated.md` | Yes (write-up) |
| `notes/chatfield-2015-lexicomp-micromedex.md` | Yes |
| `notes/pinkoh-2023-psychotropic-ddi-databases.md` | Yes |
| `notes/interview-2026-09-21-hospitalist-inpatient-ddi.md` | Yes |
| `rubrics/rubric_INLS_509_Mini_Search_Engine_Project_Controlled_Vocab.pdf` | Yes |
| `rubrics/rubric_mini_search_engine_project_part_1_document_collection_foraging.md` | Yes |
| `rubrics/rubric_mini_search_engine_project_part_2_mini_controlled_vocabulary.md` | Yes |

No git tags exist. The Part 1 and Part II write-ups stay where they are.

## Toolchain

Python 3.11.15 in `.venv` (gitignored) with pytest 9.1.1. No other dependency.

## Layout

The Section 9.4 layout is kept. Additions, with reasons:

* `collect/manifest.py` (pure): reads partition URLs and the export date out of the manifest dict, so `fetch.py` stays I/O only.
* `collect/stream_decode.py` (pure) and `collect/partition_reader.py` (I/O): a partition is 120 MB zipped and about 1 GB of JSON; decoding it incrementally keeps memory flat.
* `<package>/run.py`: job functions that compose the package's pure and I/O functions. `cli.py` only parses arguments and dispatches to them.
* `tests/conftest.py` and `tests/fixtures/FIXTURES.md`: fixture loading and the fixture provenance table.

## Verified and unverifiable

See `reports/VERIFIED_FACTS.md`. Unverifiable: a documented DailyMed rate limit (none stated); the exact wording of the retired RxNav Interaction API page (returns 403; the RxNav home page carries the discontinuation notice instead).

## Commands and tests

```
.venv/bin/python -m pytest -q
```

Result at the end of Phase 0: 46 passed, 0 failed, 0 skipped.

## What to check by hand

* The fixture choices in `tests/fixtures/FIXTURES.md`, especially Adderall IR (an ANDA product) and the generic labels chosen for trazodone, desvenlafaxine, venlafaxine, cyclobenzaprine, gabapentin, and dextroamphetamine.
* Open question 4 (`self` exemption in the style test) and 5 (attribution scan exemptions).

## Open questions

See `reports/OPEN_QUESTIONS.md`, items 1 to 10.
