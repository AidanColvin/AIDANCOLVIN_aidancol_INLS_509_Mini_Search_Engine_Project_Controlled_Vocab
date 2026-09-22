# Drug Interaction Screen redesign — final report, 2026-09-22

## Status against Section 13's definition of done

* **Live page.** Confirmed on the live site: the cursor sits in the
  medication field on load, with no click. Pasting a comma-separated list
  adds every entry and runs one check. Sections 3, 4, and 6's behaviors —
  spelling correction, expandable rows, candidate choice, alert cards
  sorted by tier with the boxed-warning box treatment, the label search
  view with grouped hierarchical filters and a mobile bottom sheet, dark
  mode, the phone layout — all verified directly in the browser, first
  locally against a full rebuild of the collection and then again on
  production. **Done.**
* **Safety rules.** Every Section 5 rule holds: `notice` and
  `no_warning_text` render verbatim; no banned wording anywhere; pair
  alerts show only the source label's sentence (Phase 2 fix); nothing is
  built with `innerHTML`; DailyMed links are checked against the DailyMed
  origin before being used as an `href`; nothing is stored in
  `localStorage`/`sessionStorage`/cookies/the URL. An
  `<img src=x onerror=...>` payload was confirmed to render as inert plain
  text. **Done.**
* **Backend fixes.** All seven Section 7 fixes are merged with tests: the
  parser accepts singular "1 time daily", strips trailing directions and
  administration counts; text over 4,000 characters gets HTTP 413; pair
  alerts no longer copy the source's sentence; duplication alerts say
  "Duplicate therapy" and attribute evidence to the correct label; T14–T16
  evidence prefers the concomitant-use sentence within its field;
  heading noise is stripped. Every `results/report.md` example now
  resolves to a label (49 of 49, verified against the real, full
  collection, not just the fixtures). Venlafaxine plus desvenlafaxine
  gives no false Contraindicated alert (verified against the fixtures via
  `test_venlafaxine_and_desvenlafaxine_give_no_false_pair_alert`, and
  independently against the live collection, where venlafaxine now stays
  correctly unresolved-pending-a-candidate-choice rather than firing a
  false alert). **Done.**
* **QA re-run.** 10 of 10 patients pass against the live site. Entries
  resolved: 58 of 60 (was 11 of 60). Interaction alerts fired: 4 (was 0).
  Full comparison table and the two remaining genuine ambiguities in
  `reports/redesign_phase8_ship.md`. **Done.**
* **Tests.** `python -m pytest -q`: 289 passed, 0 failed, 0 skipped.
  `cd web && npm test`: 103 passed, 0 failed, 0 skipped — including a real
  TypeScript-compiler-API style enforcement test, not ESLint. Nothing is
  skipped anywhere; `reports/BLOCKERS.md` has no new entries from this run.
  **Done.**
* **Attribution.** `tests/test_no_attribution.py` scans every tracked and
  untracked, non-ignored file in the repo (already covers `web/` and
  `public/` without needing a change, since it was never scoped to
  specific directories) and passes. Every commit message on this run's
  branches was scrubbed before every push per Section 9.4. **Done.**
* **Final report and merge.** This file, committed and pushed.
  `build/frontend-redesign` is merged into `main` (PRs #4, #5, #6), and
  `main` is the branch Vercel deploys from. **Done.**

## Contrast-ratio table

Computed with the WCAG relative-luminance formula against every color pair
Section 3.2 names. Full table with sourcing in `reports/VERIFIED_FACTS.md`.

| Pair | Light | Dark |
| :--- | ---: | ---: |
| Primary text / page | 15.46:1 | 19.29:1 |
| Secondary text / page | 4.66:1 | 8.16:1 |
| Accent text or button text / surface | 5.39:1 | 5.67:1 |
| Field border / surface | 3.62:1 | 3.36:1 |
| Contraindicated tier color / surface | 6.57:1 | 6.68:1 |
| Warning tier color / surface | 5.46:1 | 7.53:1 |
| Interaction-note/duplication tier color / surface | 11.35:1 | 11.18:1 |

Every pair clears its WCAG target (4.5:1 text, 3:1 the field border, the
one interactive-component boundary the token list names). The decorative
row hairlines sit near 1.3:1, which WCAG 1.4.11 exempts for a boundary not
needed to identify a component or its state — a checked, deliberate choice,
not an overlooked gap.

## Before/after QA numbers

| Metric | Before (`results/report.md`) | After (`results/rerun_2026-09-22/report.md`) |
| :--- | ---: | ---: |
| Entries resolved to a label | 11 of 60 (18%) | 58 of 60 (97%) |
| Interaction alerts fired, any patient | 0 | 4 |
| Patients passing (endpoint returned data) | 10 of 10 | 10 of 10 |

The 2 still-unresolved entries are genuine `needs_confirmation`
ambiguities in the live collection (more than one real product under the
same name), not parsing failures — the app correctly asks which one.

## How to build and test the front end

```bash
python3.11 -m venv .venv && .venv/bin/pip install -e ".[test]"
.venv/bin/python -m pytest -q

cd web
npm ci
npx tsc            # type-check
npm test           # type-check + run the compiled tests
npm run build      # compile web/src/ to public/js/
```

`.github/workflows/rebuild.yml` runs the same sequence (plus the full
openFDA rebuild) on every push to `main` and deploys through Vercel; there
is no manual deploy step.

## The first three things to check when you return

1. **Look at the live site yourself** —
   https://rx-label-search-aidancolvins-projects.vercel.app/ — paste a
   medication list and see the redesign end to end. The Phase 7 and Phase 8
   reports list the specific cases already checked.
2. **Decide whether the two open verification gaps matter to you**: an
   actual VoiceOver pass in Safari, and `prefers-reduced-motion` /
   exactly-320px checked live rather than just written into the CSS
   (`reports/redesign_phase7_local_verification.md`, "Open questions").
3. **Decide whether to keep or drop the "Which one?" pill-labeling rough
   edge**: when two ambiguous candidates share the same name before the
   arrow (the real venlafaxine and paroxetine cases in the QA re-run), the
   pills look identical even though they lead to different drugs. Section
   4.1's own spec anticipates the "still needs confirmation" loop this
   causes, but the pills themselves offer no way to tell them apart — a
   backend follow-up (returning a more specific label per candidate) would
   be the real fix; out of scope for this run
   (`reports/redesign_phase5_interactions_view.md`, "What I should check
   by hand").

## Everything this run touched, in order

`reports/redesign_phase0_audit.md` through
`reports/redesign_phase8_ship.md`, plus the closeouts folded into
`reports/redesign_phase0_audit.md` and `reports/redesign_phase1_parser.md`
(the "405 tests" trace and the "2 puffs"/"2 sprays" fix requested
mid-run). `reports/VERIFIED_FACTS.md`, `reports/OPEN_QUESTIONS.md`, and
`reports/BLOCKERS.md` (no new blockers) all carry a "Redesign run,
2026-09-22" section. `results/rerun_2026-09-22/` holds the live QA re-run.
