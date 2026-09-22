# Redesign run, 2026-09-22 — Phase 0 audit

Work branch: `build/frontend-redesign`, created from `main` at commit `555d3ec`.

## What was built

Audited the repo against BUILD_PROMPT.md Section 2, verified the API
contract, the deploy pipeline, and the toolchain, and started Phase 1
(parser fixes) since the two bugs were fast to isolate and fix once the
audit located the parser.

## Repo state

- Remote: `AidanColvin/AIDANCOLVIN_aidancol_INLS_509_Mini_Search_Engine_Project_Controlled_Vocab`, already cloned at the working directory, `main` clean at `555d3ec`.
- `public/index.html` exists and is the current live page (to be replaced in Phase 5-6).
- `.github/workflows/rebuild.yml` exists, runs on push to `main`, weekly cron, and `workflow_dispatch`.
- Read-only paths from Section 9.2 all present: `MiniVocab_Aidan_Colvin_aidancol.md`, `rubrics/`, `notes/`, `document_collection_part_1/`, `LICENSE`, every file under `results/` and `reports/`. None touched.
- `tests/` has 54 test files. Full suite: **273 passed** (not "405+" as BUILD_PROMPT.md Section 2 assumed — the prompt's own rule says code wins over the prompt; recorded in OPEN_QUESTIONS.md).
- `data/build/` exists locally (gitignored) from a prior full build — used to sanity-check parser fixes against the real production-scale name dictionary (7,707 keys) before committing. CI rebuilds this itself before running pytest, per `rebuild.yml`.

## Section 2.1 API contract — verified against source

- `api/check.py` calls `rx_label_search.serve.api_check.build_check_response`, wraps `FileNotFoundError` into HTTP 503 with `{"error": "checker data not built yet: ..."}`. Matches the prompt.
- `api/search.py` calls `rx_label_search.serve.api_search`, supports `terms_only=1` returning `{"build_date", "available_terms"}`, and otherwise `build_search_response`. Matches the prompt.
- Full alert/table field shapes verified against `interactions/report.py`, `interactions/pairs.py`, `interactions/groups.py`, `interactions/duplicates.py`, `interactions/evidence.py`, `interactions/tiers.py` in Phase 1-3 work (see those phase reports).

## Deploy pipeline — verified against `.github/workflows/rebuild.yml`

- Runs on `ubuntu-latest`, Python 3.12.
- Order: checkout, install package, download openFDA data, collect, base-ingredients, tag, build-index, build-checker-data, `pytest -q`, install Vercel CLI + `uv`, `vercel build --prod` (prebuilt) then `vercel deploy --prebuilt --prod`.
- Only `public/` is served as static files; `vercel.json` excludes `data/raw`, `data/build/collection.jsonl`, `.venv`, `tests`, `notes`, `rubrics`, `document_collection_part_1`, `.github`, `reports` from the Python function bundle via `excludeFiles`. `.vercelignore` mirrors the same list for the static/build step.
- A CI step for `web/` (npm ci, tsc, web tests) must run **before** `vercel build` so the compiled `public/js/` exists when Vercel builds. Added in Phase 4.
- `package.json` must live in `web/`, not the repo root, so Vercel's Python-function auto-detection at the root is unaffected — confirmed by reading `vercel.json`, which only configures `api/*.py`; Vercel's zero-config static handling serves `public/` regardless of a root `package.json`, but keeping it out of the root avoids Vercel guessing a Node build step for the whole repo.

## Toolchain versions — verified locally, 2026-09-22

- Python: 3.14.3 (local dev venv); CI pins 3.12 in `rebuild.yml` — unchanged, not in scope.
- Node: v25.8.2 (local). No Node version is pinned anywhere in the repo yet; Phase 4 adds a CI step and will pin one there (`actions/setup-node`).
- npm: 11.11.1 (local).
- TypeScript: `npm view typescript version` → **7.0.2** (current stable on the npm registry, checked 2026-09-22). Pinned as the only `web/` dev dependency.
- ES modules and `backdrop-filter` (with `-webkit-` prefix) are supported in current Safari, Chrome, and Firefox releases; this is long-standing, uncontroversial browser support and was not re-verified with a live fetch. If this changes materially before shipping, Phase 7's local verification (real browser via the built-in Browser pane) will catch it.

## Commands run and results

- `python -m pytest -q` (before any change): 273 passed.
- `python -m pytest tests/test_normalize_med_line_parser.py -q` (after the Phase 1 fix): 12 passed (8 existing + 4 new).
- `python -m pytest -q` (after the Phase 1 fix): 273 passed — no regressions.
- `npm view typescript version`: 7.0.2.

## What I should check by hand

- Nothing yet — no deploy has happened.

## Open questions

See `reports/OPEN_QUESTIONS.md`, heading "Redesign run, 2026-09-22".
