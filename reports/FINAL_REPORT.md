# Final report

State of the project against Section 13's definition of done, how to run every command, and what to do first.

## Definition of done, checked against Section 13

| Criterion | Status |
| :--- | :--- |
| All 17 PDLA terms tagged with evidence; consistency tests pass | Met. 0 consistency violations across all 2,481 built labels. |
| Per-term precision/recall/F1 harness runs; README explains recording the real gold set | Met. See `reports/phase4_evaluate.md` and the README's "Evaluating the tagger" section. |
| ONC high-priority floor passes for every collection pair | Partially met: 10 of 13 automatically testable pairs fire. See `reports/BLOCKERS.md`. |
| Section 3.6 acceptance test passes | Met, built from fixtures per that section's own instruction. |
| Search Scenarios 1 to 3 pass | Met. |
| Page runs locally against the Python functions; weekly workflow deploys when tests pass and the secret is present | Built and verified over real HTTP requests; not yet deployed live, no Vercel project exists yet. See `reports/phase7_serve.md`. |
| README.md and DATA_SOURCES.md complete | Met. |
| Style, attribution, and all other tests pass; skipped tests listed | Met. 405 passed, 0 failed, 0 skipped. |
| The two forbidden names appear nowhere in the repo, including commit messages | Met, checked before every push. |
| This file committed and pushed; `main` has the merge or `MERGE_READY.md` says how | This file is that report. See the end of this document for the merge outcome. |

## The built collection

262,883 total labels as of the 2026-09-18 openFDA export, narrowed to 2,481 human prescription labels, one per active-ingredient set, after the Part 1 scope filters. Full counts in `data/build/collection_stats.json` after a rebuild.

## How to run every command

See the README's "Tool" section for the full command list with examples. In short, from the repo root:

```bash
.venv/bin/pip install -e ".[test]"
PYTHONPATH=src .venv/bin/python -m rx_label_search download
PYTHONPATH=src .venv/bin/python -m rx_label_search collect
PYTHONPATH=src .venv/bin/python -m rx_label_search base-ingredients
PYTHONPATH=src .venv/bin/python -m rx_label_search tag
PYTHONPATH=src .venv/bin/python -m rx_label_search build-index
PYTHONPATH=src .venv/bin/python -m rx_label_search build-checker-data
.venv/bin/python -m pytest -q
```

Then `query`, `check`, `gold-template`, `gold-label`, `evaluate-tags`, and `evaluate-search` for day-to-day use.

## The first three things to do

1. **Read `reports/BLOCKERS.md`.** It records the one done-criterion not fully met (the ONC floor test) and exactly why, plus what I recommend as a follow-up.
2. **Create the Vercel project and its secrets.** Create `rx-label-search` under your team, run `vercel link` locally once to generate `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID`, and add those two plus a `VERCEL_TOKEN` as GitHub repository secrets. Until then the weekly workflow will rebuild and test every week but skip the deploy step and say so in its log.
3. **Spot-check T17 (Contraindicated Combination).** It drives the checker's highest-tier pair alerts and had the most iteration in this build; `reports/phase6_check.md` and `reports/OPEN_QUESTIONS.md` items 16 and 18 to 21 record its known residual imprecision. A hand review of a sample of T17-tagged labels before relying on pair alerts clinically is worth the time.

## Everything the reports cover, in order

`reports/phase0_audit.md` through `reports/phase7_serve.md`, `reports/VERIFIED_FACTS.md`, `reports/OPEN_QUESTIONS.md`, and `reports/BLOCKERS.md`.

## Reminders that apply to every use of this tool

* This tool is not validated for clinical use. Before any real clinical launch, a regulatory review is the owner's own step, not something this build performed.
* Medication lists are never logged, stored, cached, or sent to any third party; the check function is stateless.
* Every alert and tag carries the label sentence and section behind it, and every tier is labeled a heuristic.
