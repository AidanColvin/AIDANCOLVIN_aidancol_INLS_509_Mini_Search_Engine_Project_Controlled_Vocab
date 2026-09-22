# QA re-run, 2026-09-22 — after the front-end redesign and backend fixes

Re-runs the same 10 synthetic patients from `results/report.md` (read-only,
not modified) against the live, redesigned site, to compare against the
original 11-of-60-resolved, 0-alerts baseline.

`results/run_patients.py` (read-only, not modified) drives the *old* page:
it looks for a "Medication list" textarea and clicks a "Check interactions"
button. Neither exists on the redesigned page — Section 4 of the redesign
removed the button entirely; the field adds one entry per Enter press and
the check runs automatically, debounced, after the list changes. Running
the original script unmodified against the new site would fail outright,
not because anything regressed but because the whole interaction model
changed by design.

`run_patients_rerun.py` is the same script adapted only where the UI itself
changed: it adds each drug with one Enter press instead of one textarea
fill plus one button click, and it waits for the new results heading
instead of the old `#check-results` panel. Everything else — the 10
patients, the network-interception method, the report format — is
unchanged from the original.

Outputs: `report.md`, `raw_responses.json`, and `patient_NN.png` for each
patient, in this directory. See `reports/redesign_phase8_ship.md` for the
headline comparison against the original run.
