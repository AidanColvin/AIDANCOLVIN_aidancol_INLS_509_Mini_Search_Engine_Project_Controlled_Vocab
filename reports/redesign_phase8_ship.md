# Redesign run, 2026-09-22 — Phase 8: ship

## What was built

Merged `build/frontend-redesign` into `main` (PR #4), fixed two real
production deploy failures that surfaced only on the live pipeline (PRs #5
and #6, detailed below), confirmed the live site runs the new build, and
re-ran the QA script (adapted for the redesigned UI, since the old page's
button and textarea no longer exist) against production.

## Two real deploy failures, found and fixed

**First failure (PR #4's own deploy):** `vercel build` failed with
`Error: ENOENT: no such file or directory, readlink
'/vercel/path0/design/2026-09-22-redesign/canvas.json'`. Vercel's own build
log explained why: `.vercelignore` excluding `design/`, `web/node_modules`,
and `web/out` collided with files its prebuilt-functions file trace had
already queued to include. `web/node_modules` and `web/out` were already
covered by `.gitignore` and never reached the deploy in the first place, so
no `.vercelignore` entry was needed for them; `design/` being included costs
a little deploy size, not a functional problem. Fixed (PR #5) by reverting
`.vercelignore` to its prior content.

**Second failure (PR #5's own deploy):** the exact same error, now on
`web/out/tests/alerts.test.js`. The pre-existing bare `tests` entry in
`.vercelignore` — present before this run, meant for the top-level Python
`tests/` directory — is an unanchored gitignore-style pattern, so it also
matches `web/tests/` and `web/out/tests/` at any depth. This run's own new
`web/tests/` directory is what newly exposed a bug that was always latent in
`.vercelignore`. Fixed (PR #6) by anchoring every entry with a leading `/`,
verified before pushing with a scratch git repo using the identical pattern
file (`git add -A -n`: `web/tests/` and `web/out/tests/` no longer matched,
every originally-intended top-level directory still was).

Both fixes are real, minimal, and specifically targeted at the actual
failure; recorded in full in `reports/VERIFIED_FACTS.md`.

## Live verification

Confirmed directly:

- `https://rx-label-search-aidancolvins-projects.vercel.app/` returns HTTP
  200 and serves the new `<div id="app">` shell.
- `/js/main.js` returns HTTP 200.
- `/api/search?terms_only=1` returns real term data with today's build date
  (`2026-09-22`).
- Opened the live site in the built-in browser: the redesigned Interactions
  view renders correctly, auto-focused, with no console errors.

## QA re-run against the live, redesigned UI

`results/run_patients.py` (read-only, not modified) targets the *old*
page's "Medication list" textarea and "Check interactions" button, neither
of which exist anymore by design (Section 4 removed the button entirely).
Running it unmodified against the new site would fail outright, not because
anything regressed but because the whole interaction model changed. Wrote
`results/rerun_2026-09-22/run_patients_rerun.py`, adapted only in how it
drives the page (one Enter press per drug instead of one textarea fill plus
one button click) and in how it detects the settled result (the new results
heading instead of the old `#check-results` panel), keeping the same
network-interception method, the same 10 patients, and the same report
format as the original script.

**Result: 10 of 10 patients passed** (returned real interaction data, HTTP
200). Compared to the original `results/report.md`:

| Metric | Original (`results/report.md`) | Re-run, 2026-09-22 |
| :--- | ---: | ---: |
| Entries resolved to a label | 11 of 60 (18%) | **58 of 60 (97%)** |
| Interaction alerts fired, any patient | 0 | **4** |

The 2 still-unresolved entries (Venlafaxine ER for Patient 7, Paroxetine for
Patient 10) are both genuine `needs_confirmation` ambiguities — the live
collection now carries more than one real product under each name — not
parsing failures; the app correctly asks which one instead of guessing,
exactly as designed. Full report and screenshots in
`results/rerun_2026-09-22/`.

## Commands run and results

- `python -m pytest -q`: 289 passed (unaffected by the deploy fixes).
- `cd web && npm test`: 103 passed.
- `python3 results/rerun_2026-09-22/run_patients_rerun.py`: 10/10 patients passed against the live production site.

## What I should check by hand

- The live site itself, since you now have it in front of you.
- `results/rerun_2026-09-22/patient_*.png` for the actual rendered screenshots from the live run.

## Open questions

None new for this phase; the two deploy failures are fully closed (see
`reports/VERIFIED_FACTS.md`).
