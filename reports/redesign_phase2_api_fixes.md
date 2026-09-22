# Redesign run, 2026-09-22 — Phase 2: API fixes

## What was built

- **7.2 Silent truncation:** `parse_check_body` now raises
  `MedicationTextTooLong` instead of silently truncating at 4,000
  characters. `api/check.py` catches it and returns HTTP 413 with
  `{"error": "..."}`.
- **7.4 Copied evidence:** `build_pair_alert` in `interactions/pairs.py`
  no longer copies the source drug's sentence onto the other drug. The
  other member now gets an empty `section`/`sentence` and its own
  DailyMed link.
- **7.5 Duplication alerts:** both duplication builders in
  `interactions/duplicates.py` now use `tier_name = "Duplicate
  therapy"` instead of `"heuristic"`. The metabolite flag's two
  members previously mixed one drug's display name/effective_time with
  the *other* drug's cited set_id and sentence; `cited_member()` now
  attributes the citation only to whichever drug's own resolved label
  actually is the cited label (matched by set_id), and falls back to
  the existing base-ingredient evidence for both members when neither
  matches, rather than ever showing a sentence next to a mismatched
  DailyMed link. The base-ingredient flag's members already had an
  empty `section` (verified, not changed).

## Commands run and results

- `python -m pytest tests/test_serve_api_check.py tests/test_interactions_duplicates.py tests/test_interactions_pairs.py tests/test_style.py -q`: 21 passed.
- `python -m pytest -q` (full suite): 277 passed, no regressions.

## Tests added

- `tests/test_serve_api_check.py`: `test_parse_check_body_raises_instead_of_silently_truncating` (replaces the old truncation assertion).
- `tests/test_interactions_pairs.py`: `test_build_pair_alert_never_attributes_the_source_sentence_to_the_other_drug`.
- `tests/test_interactions_duplicates.py`: tier_name assertions on the existing tests, plus `test_build_metabolite_flag_attributes_the_sentence_to_the_cited_label_only` and `test_build_metabolite_flag_falls_back_when_neither_label_matches_the_citation`.

## Any expected value a real source contradicted

None — the metabolite reference file (`data/reference/active_metabolites.json`) confirms `set_id` is the *metabolite's own* label (desvenlafaxine's set_id, not venlafaxine's), which is what made the original bug visible: the code paired venlafaxine's own display name with a DailyMed link and sentence that actually belonged to desvenlafaxine.

## What I should check by hand

- Nothing yet — no deploy.

## Open questions

None new for this phase.
