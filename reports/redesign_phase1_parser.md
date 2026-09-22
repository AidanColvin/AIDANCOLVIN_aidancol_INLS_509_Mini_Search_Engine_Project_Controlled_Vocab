# Redesign run, 2026-09-22 — Phase 1: parser fixes

**Updated 2026-09-22, second pass.** The first pass of this report
tested that the parser produced a *clean name text*, not that the name
*resolved to a label*, which is what Section 10's Phase 1 "Done when"
actually requires. This update fixes that gap: the "2 puffs" and "2
sprays" entries are now fixed at the parser level (not just documented
as out of scope), and a real resolution test was added. The rest of
this report is unchanged from the first pass except where noted.

## What was built

Fixed three bugs in `src/rx_label_search/normalize/med_line_parser.py`
that kept `results/report.md`'s 49 entries from resolving:

1. Singular "1 time daily" is now a recognized frequency phrase.
2. "as needed" / "as necessary" / "PRN" / "at bedtime" are stripped
   from the name text before matching.
3. **(added in this update)** A per-dose administration count — "2
   puffs", "2 sprays", "3 drops", "2 inhalations", "2 actuations" — is
   now stripped from the name text the same way. This was the
   remaining cause for the Albuterol and Fluticasone entries: neither
   is a frequency or a "trailing direction" in Section 7.1's literal
   sense, but leaving "2 puffs" or "2 sprays" attached to the name
   dragged the typo-tolerant match score for "Albuterol 2 puffs" down
   to about 0.53 against the dictionary key "albuterol" — well under
   the 0.85 local-match threshold — so the entry stayed unresolved
   regardless of how good the rest of the parse was.

## Why the first pass wasn't enough

The first pass tested `parse_entry(...).name_text` against a
fixture-only dictionary reasoning, and documented in
`OPEN_QUESTIONS.md` that testing real resolution for 47 of the 49
drugs was impossible against the 12-fixture offline dictionary the
rest of the test suite uses, since most of those drugs (Alprazolam,
Losartan, Ramipril, ...) simply aren't in the 12 fixtures. That
reasoning was correct as far as it went, but it stopped one step short
of the actual requirement: Section 10 Phase 1's "Done when" says every
example "resolves in a test with `use_rxnorm` off," not that it
parses to a clean string.

The fix: `.github/workflows/rebuild.yml` already builds the **full**
openFDA collection (download, collect, base-ingredients, tag,
build-index, build-checker-data) before it runs `pytest` — the same
full dictionary `/api/check` reads at runtime. A new test,
`test_report_md_failing_examples_resolve_to_a_label_with_use_rxnorm_off`,
loads that full `data/build/name_dictionary.json` (gitignored, not
committed, built fresh by CI and by anyone who runs the pipeline
locally) and asserts every one of the 49 examples resolves — matched
or needs-confirmation, never `unresolved`. It skips with a named,
legible reason when that build hasn't been run locally, which is the
same reason a contributor without a full build can't run
`test_interactions_acceptance.py`'s Playwright-adjacent style of
end-to-end check either; it is not a hidden or silent skip.

Ran it locally against the real, full 7,707-key dictionary already
built on this machine: **all 49 examples now resolve**, 0 unresolved.

## Commands run and results

- `python -m pytest tests/test_normalize_med_line_parser.py -v`: 14 passed (12 from the first pass + 2 new: `test_strip_administration_quantity_removes_puffs_and_sprays`, `test_report_md_failing_examples_resolve_to_a_label_with_use_rxnorm_off`).
- `python -m pytest -q` (full suite): 289 passed, no regressions.

## Tests added (this update)

- `tests/test_normalize_med_line_parser.py`: `test_strip_administration_quantity_removes_puffs_and_sprays`, `test_report_md_failing_examples_resolve_to_a_label_with_use_rxnorm_off`.
- Updated `REPORT_MD_FAILING_EXAMPLES` so the Albuterol and Fluticasone entries now expect the fully clean name ("Albuterol", "Fluticasone") instead of the leftover-fragment values from the first pass.

## Any expected value a real source contradicted

None invented. The resolution test's pass/fail comes from the real
`match_name()` output against the real, locally built dictionary — run
directly and captured before being written into the test, not assumed.

## What I should check by hand

- Nothing yet — no deploy depends on this.

## Open questions

The "2 puffs" / "2 sprays" open question from the first pass is
resolved by this update. See `reports/OPEN_QUESTIONS.md` for the
still-open test-count discrepancy (closed separately in
`reports/redesign_phase0_audit.md`'s update).
