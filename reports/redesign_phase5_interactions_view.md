# Redesign run, 2026-09-22 — Phase 5: Interactions view

## What was built

- `web/src/records.ts`: readonly record types for the full `/api/check` and `/api/search` contract, plus the app's own `AppState` and a `createInitialState`/`withState` factory pair.
- `web/src/api.ts`: `fetchCheck`/`fetchSearch`/`fetchTermsOnly`, each validating the decoded JSON at the boundary against the real shape (`ApiShapeError` on a bad shape, `ApiHttpError` carrying the status and the API's own `error` text on a non-2xx response) — no `any`, nothing trusted unchecked.
- `web/src/meds.ts`, `web/src/format.ts`, `web/src/alerts.ts`: the pure logic Section 9.3 assigns them — splitting pasted text, the "Spelling corrected" check, candidate labels, dose/section/count formatting, alert sorting and evidence selection (strongest section first, "Duplicate therapy" override, skip-empty-section).
- `web/src/render_icons.ts`, `web/src/render_header.ts`, `web/src/render_interactions.ts`: DOM building only, wired by `web/src/main.ts`, which owns the one `AppState` object, debounces `/api/check` by 300ms with `AbortController`, and wires every callback (add, remove, clear all, choose a candidate, edit an unresolved entry, expand a row or an alert, retry).
- `public/index.html` (now a thin shell: `<div id="app">` plus the module script) and `public/styles.css` (the full design-token system from Section 3.2: light and dark custom properties, the header, the medication field and list, alert cards per tier including the boxed-warning box treatment, the error card).

## A real bug this phase's own local verification caught

`statusForLine` (moved to `meds.ts` once found to be pure, not render, logic)
originally checked `medication_table` before `unresolved_entries`. That was
backwards: `medication_table` carries **one row per line regardless of
whether it resolved**, with `matched_name: null` for an unresolved one, so
the row branch always matched first and the unresolved branch — the
"Which one?" candidate UI — was never reached. Found by pasting
"venlafaxine 75 mg daily, desvenlafaxine 50 mg daily" against the real,
live-rebuilt collection (where "venlafaxine" is genuinely ambiguous, unlike
the 12-drug fixture set) and watching the row render as a bare pending line
instead of the candidate picker. Fixed by checking `unresolved_entries`
first, and only falling back to the row when `matched_name` is not null.
Regression test added: `statusForLine prefers the unresolved entry over a
null-matched_name row for the same line`.

## Section 4 behaviors verified against a real local server

Ran the real Python API handlers plus the compiled front end together (see
`reports/redesign_phase7_local_verification.md` for the full case list).
Confirmed directly in the browser: cursor auto-focused on load with no
click; pasting a comma-separated list adds every entry and runs one check;
"Spelling corrected" tags appear correctly; the DEA badge, dose, and chevron
render; expanding a row shows FDA class/route/base ingredients/matched
chain/label terms; remove appears on hover and on keyboard focus and clears
back to the field; Clear all empties the list and results; the "Which one?"
candidate flow re-runs the check and, when the choice is still ambiguous
(the real venlafaxine case — its candidates share the same name before the
arrow, so re-entering it cannot disambiguate), correctly shows the choices
again rather than looping forever or crashing, matching Section 4.1's own
"If the result still needs confirmation, show the choices again"; the
length-limit message shows without dropping any entry; and an
`<img src=x onerror=...>` payload renders as inert plain text with no script
execution, confirmed by checking the handler never fired.

## Commands run and results

- `npm test`: 103 passed (101 from Phase 4 plus the two new `statusForLine` tests).
- `npx tsc -p tsconfig.site.json`: clean build.
- Full case list run against a local Python+static server: see Phase 7's report.

## What I should check by hand

- The "Which one?" pill labeling is exactly what Section 4.1 specifies (the
  part before the arrow, lowercased), but for the real venlafaxine ambiguity
  both candidates show as identical-looking "venlafaxine" pills, because the
  API's own candidate strings for this ambiguity type share the same name
  before the arrow. This is a real, if narrow, usability rough edge in the
  data the API sends, not a front-end bug — Section 4.1 anticipates it
  ("show the choices again") but a user facing it has no way to actually
  tell the two pills apart. Worth a look if it comes up in practice.

## Open questions

None new for this phase beyond the `statusForLine` fix above, which is
closed.
