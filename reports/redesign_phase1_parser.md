# Redesign run, 2026-09-22 — Phase 1: parser fixes

## What was built

Fixed the two bugs `results/report.md` isolated in
`src/rx_label_search/normalize/med_line_parser.py`: singular "1 time
daily" is now a recognized frequency phrase, and "as needed" / "as
necessary" / "PRN" / "at bedtime" are stripped from the name text
before matching. Both fixes are three small, additive changes: one
regex alternative, one new stripping function, one call site.

## Commands run and results

- `python -m pytest tests/test_normalize_med_line_parser.py -q`: 12 passed (8 pre-existing + 4 new).
- `python -m pytest -q` (full suite): 273 passed, no regressions.

## What changed

- `FREQUENCY_PATTERNS`: `(?:times|x)` → `(?:times|time|x)` so "1 time
  daily" matches the same pattern as "3 times daily".
- New `TRAILING_DIRECTIONS` regex and `strip_trailing_directions()`,
  called in `parse_entry()` between frequency parsing and
  `clean_name_text()`.
- The RxNorm dose-leak example from Section 7.1 ("Lisinopril 1 time →
  lisinopril 1 MG/ML") is fixed as a side effect of the frequency fix:
  once "1 time daily" is recognized and removed, no dose fragment is
  left to leak into the RxNorm query.

## Tests added

`tests/test_normalize_med_line_parser.py`:
- `test_singular_one_time_daily_is_recognized`
- `test_strip_trailing_directions_removes_as_needed_prn_and_bedtime`
- `test_report_md_failing_examples_now_parse_to_a_clean_name` — all 49
  previously unresolved `results/report.md` entries, asserting the
  real `parse_entry(...).name_text` for each.
- `test_dose_text_no_longer_leaks_into_the_matched_name`

## Any expected value a real source contradicted

None for this phase's committed tests — every asserted value is the
real output of the fixed code, not an invented one. Two of the 49
examples (Albuterol "2 puffs", Fluticasone "2 sprays") still carry a
leftover fragment after the two named fixes; the test asserts that
real, current value rather than a hoped-for clean one. See
`reports/OPEN_QUESTIONS.md`.

## What I should check by hand

- Nothing yet — this only changes offline parsing; no deploy.

## Open questions

See `reports/OPEN_QUESTIONS.md`, heading "Redesign run, 2026-09-22".
