# Phase 7: serve

## What was built

`api/search.py` and `api/check.py`, stateless Python `http.server.BaseHTTPRequestHandler` functions with no framework dependency, so Vercel's file-based `/api` routing applies without a detected preset (verified in Phase 0: a framework dependency would take over routing). `src/rx_label_search/serve/api_search.py` and `api_check.py` hold the pure request/response logic each entry point calls. `public/index.html` is the thin static front end: a search box with PDLA term filter chips, a medication-list box, the alerts and medication-table display, and the notice and build date. `vercel.json`, `.vercelignore`, and `.github/workflows/rebuild.yml` complete the deploy path.

## Function size decision

The full search index (BM25 term frequencies plus every label's full indexed text) serialized to one file at 115 MB. Section 10 anticipated this and asked for per-ingredient sharding if the index did not fit. The index was split:

* `data/build/search_ranking.json` (38 MB): everything BM25 ranking and facet filtering need, with no body text. This is the only large file a cold start reads.
* `data/build/snippets/<set_id>.json` (67 MB total across 2,481 small files, about 27 KB each): each label's indexed text, read only for the handful of results a query actually returns, after ranking and the result limit are applied.

This keeps every request's actual work small: `build-index` plus a sample query ran in well under a second locally (0.51s including Python process startup for a two-term AND query returning 2 results). Both numbers are far inside the verified Python function limits (500 MB uncompressed bundle; 2 GB memory on Hobby). `checker_records.json` (4.6 MB) and `name_dictionary.json` (2.3 MB) needed no sharding.

`vercel.json`'s `functions.excludeFiles` and `.vercelignore` both exclude `data/raw/` and the 232 MB raw `collection.jsonl`, which the serve functions never read at request time.

## Commands run and results

```
PYTHONPATH=src .venv/bin/python -m rx_label_search build-index
PYTHONPATH=src .venv/bin/python -m rx_label_search build-checker-data
.venv/bin/python -m pytest -q
```

Tests: 405 passed, 0 failed, 0 skipped.

## Local verification

`vercel dev` needs a logged-in Vercel account, which this unattended session does not have and must not create (Section 9.5: deploy only through the GitHub Actions workflow, never by hand). Instead, both handler classes were started as real `http.server.HTTPServer` instances in-process and driven with genuine HTTP requests over `urllib`:

* `GET /api/search?terms_only=1` returned all 17 terms and the build date.
* `GET /api/search?q=muscle+spasm&term=T14&term=T15&operator=AND&limit=2` returned 2 ranked hits, cyclobenzaprine first.
* `POST /api/check` with `{"medications": "trazodone 50 mg daily, cyclobenzaprine 10 mg three times daily"}` returned the correct serotonin syndrome and CNS depression group alerts and the exact notice text.

The static page was also opened directly and renders correctly (search box, term filter area, operator toggle, medication box, notice bar) with no console errors; without a live server its `fetch` calls to `/api/*` do not resolve, which is expected for a file-opened static page and is not a gap in the verified handler logic above.

## Weekly workflow

`.github/workflows/rebuild.yml` runs on a Monday 09:00 UTC schedule, on push to `main`, and on manual dispatch. It installs the package, runs `download`, `collect`, `base-ingredients`, `tag`, `build-index`, `build-checker-data`, then `pytest -q`. It deploys only if every prior step, including the tests, succeeds. The deploy step checks for `VERCEL_TOKEN`; if it is unset, it logs that fact and exits 0 without attempting a deploy, per Section 10's requirement. When present, it follows the verified GitHub Actions pattern: `vercel pull --yes --environment=production`, `vercel build --prod`, `vercel deploy --prebuilt --prod`.

## What I should check by hand

* Create the Vercel project `rx-label-search` under your team `aidancolvins-projects` (or update the name in `reports/FINAL_REPORT.md` if you choose a different one), link it locally with `vercel link`, and add `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` as GitHub repo secrets. I did not and must not create the Vercel project or account myself.
* A first live deploy, since I could not run `vercel dev` or `vercel deploy` in this session.
* The front end's visual polish is intentionally minimal per Section 10 Phase 7 ("Clean, Apple-like visual polish waits for the Part 3 rubric").

## Open questions

None new in this phase; the function-size decision above is the only Phase 7 design choice Section 10 asked to be recorded.
