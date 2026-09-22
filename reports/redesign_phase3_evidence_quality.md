# Redesign run, 2026-09-22 — Phase 3: evidence quality

## What was built

- **7.3 False Contraindicated alerts:** `sentence_mentions_drug` in
  `interactions/pairs.py` now matches drug and pharm-class names as
  whole words (`\bname\b`), not a plain substring, and splits a T17
  evidence sentence on its bullet markers first, dropping any clause
  that is hypersensitivity-only (reusing
  `vocabulary.interaction.is_self_reference_only`) before searching
  the rest for a name match.
- **7.6 Evidence choice for T14/T15/T16:** `matching_sentence` now
  collects every candidate sentence in the first matching field and
  prefers the first one that also names combined/concomitant use
  (`_COMBINED_USE_SIGNAL`), instead of always taking the first
  candidate in the field. The field search order is unchanged.
- **7.7 Heading noise:** new `strip_evidence_heading()` removes a
  leading numbered section heading ("5 WARNINGS AND PRECAUTIONS", "7
  DRUG INTERACTIONS", "WARNINGS", "CONTRAINDICATIONS", ...) or a
  leading reference mark with a bullet ("( 5.4 ) •") from the chosen
  evidence sentence, applied at both places a final sentence is
  returned (`matching_sentence` for T14-T16, and
  `contraindicated_combination_sentence` for T17).

## Why both fixes were needed for Bug 3 (not just one)

Ran the actual venlafaxine and desvenlafaxine fixtures through the
unpatched tagger to confirm both root causes are real, not just the
one BUILD_PROMPT.md names first:

- Venlafaxine's T17 sentence is a single bullet-joined string covering
  both its hypersensitivity clause ("...hypersensitivity to
  venlafaxine hydrochloride, **desvenlafaxine** succinate...") and its
  MAOI clause. Without clause-splitting, the hypersensitivity clause
  alone caused a false pair alert toward desvenlafaxine.
- Desvenlafaxine's T17 sentence never mentions "venlafaxine" as a
  drug name at all — it only says "**desvenlafaxine**" repeatedly.
  The old plain substring check (`"venlafaxine" in lowered`) still
  matched, because "venlafaxine" is literally a substring of
  "desvenlafaxine". Without word-boundary matching, this alone caused
  a false pair alert in the other direction, with no hypersensitivity
  clause involved.

Both are fixed; recorded in `reports/VERIFIED_FACTS.md`.

## Term assignment is unchanged — proved by diff, not asserted

Wrote a one-off script that runs `tag_record` over every committed
fixture label and dumps the sorted term_id list per label, ran it once
on this branch and once with the Phase 3 changes stashed
(`git stash` / `git stash pop`), and diffed the two outputs: **no
difference.** This is the only phase where a behavior change to a
tagging rule risked changing which labels carry a term, so it's the
one phase report with a real regression check attached, not just a
claim.

## Commands run and results

- `python -m pytest -q` (full suite): 287 passed, no regressions.
- Term-assignment diff (see above): identical before and after.

## Tests added

- `tests/test_interactions_pairs.py`: `test_name_appears_matches_whole_words_only`, `test_combination_clauses_drops_hypersensitivity_only_bullets`, `test_combination_clauses_drops_a_lone_hypersensitivity_sentence`, `test_sentence_mentions_drug_ignores_a_hypersensitivity_bullet_naming_the_other_drug`, `test_sentence_mentions_drug_does_not_match_a_shorter_name_inside_a_longer_one`.
- `tests/test_interactions_acceptance.py`: `test_venlafaxine_and_desvenlafaxine_give_no_false_pair_alert`, run against the real fixtures through the full checker.
- `tests/test_vocabulary_interaction.py`: `test_oxycontin_t15_evidence_is_the_concomitant_use_sentence_not_the_general_one`, `test_preferred_sentence_picks_the_combined_use_candidate`, `test_strip_evidence_heading_removes_named_forms`, `test_trazodone_venlafaxine_and_lyrica_evidence_has_no_heading_noise`.

## Any expected value a real source contradicted

None invented — every asserted sentence fragment is the real output of
`tag_t14/t15/t16/t17_...` run against the committed fixture labels,
captured by directly running the code (see the transcripts in this
phase's work).

## What I should check by hand

- Nothing yet — no deploy.

## Open questions

None new for this phase.
