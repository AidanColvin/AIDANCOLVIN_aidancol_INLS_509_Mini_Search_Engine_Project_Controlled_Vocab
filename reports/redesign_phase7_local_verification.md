# Redesign run, 2026-09-22 — Phase 7: local verification

## What was built

A local-only combined server (Python `http.server`, not committed — lives in
this run's scratchpad, not the repo) serving the real `public/` static files
and running the real `build_check_response`/`build_search_response` handlers
against a freshly and fully rebuilt local `data/build/` (download → collect
→ base-ingredients → tag → build-index → build-checker-data, all run from a
clean cache so no stale evidence could hide behind Phase 3's RULE_VERSION
caching — see `reports/VERIFIED_FACTS.md`). `vercel dev` was not an option
per Section 0.2/Section 9.4 (no Vercel login in this run), so this mirrors
the approach the prior session's `reports/phase7_serve.md` used, extended to
serve the static files too so the real front end's `fetch` calls resolve.

## The ten cases

1. **Cursor auto-focused on load, no click.** Confirmed: `document.activeElement.id === "add-med"` immediately after navigation.
2. **Paste the six-drug list, get spelling corrections, a "Which one?" row, and alerts with no other click.** Confirmed via a synthetic `paste` `ClipboardEvent` (the automation tool's own paste gesture isn't available headlessly): 6 rows appeared, 5 carried "Spelling corrected," and alerts rendered without any further click. Against the current live-rebuilt collection, "dextroamphetamine" itself resolved without ambiguity (the fixture-only test in `results/report.md` used a different, smaller collection where it was ambiguous) — not a bug, just different real data; the candidate-choice path was instead verified directly with a genuinely ambiguous real case (see below).
3. **Choosing a candidate re-runs the check.** Confirmed with "venlafaxine 75 mg daily, desvenlafaxine 50 mg daily" — venlafaxine is genuinely ambiguous in the live collection (two products). Choosing a candidate re-ran the check; because both of venlafaxine's real candidates share the same name before the arrow, the result was still ambiguous and correctly showed the choices again, per Section 4.1's own "If the result still needs confirmation, show the choices again" — not a bug. This same session caught and fixed a real bug in the candidate row's own rendering; see `reports/redesign_phase5_interactions_view.md`.
4. **"losartan 50 mg daily, gabapentin 300 mg tid" shows `no_warning_text`.** Confirmed: heading read exactly "No warning found in the labels checked." with the notice beneath it.
5. **"venlafaxine 75 mg daily, desvenlafaxine 50 mg daily" shows no Contraindicated alert.** Confirmed: zero alert cards of any kind on the real, live-rebuilt collection (venlafaxine stayed unresolved pending a candidate choice in this run, so no pair alert could fire either way; the Phase 3 fix itself was independently confirmed correct via the acceptance test against the fixtures, `tests/test_interactions_acceptance.py::test_venlafaxine_and_desvenlafaxine_give_no_false_pair_alert`).
6. **`results/report.md` examples resolve.** Covered by the committed test `test_report_md_failing_examples_resolve_to_a_label_with_use_rxnorm_off`, which runs for real against the full local build; re-ran it directly in this phase: all 49 resolve.
7. **Text over 4,000 characters shows the length message, nothing dropped.** Confirmed: pasting 300 synthetic entries (well over the limit) produced the exact message and detail text, and all 300 lines stayed visible in the list — nothing silently disappeared.
8. **`<img src=x onerror=...>` shows as plain text, nothing runs.** Confirmed: the payload rendered as literal text in the row, the page's `innerHTML` never contained a real `<img` element, and the handler never fired.
9. **Keyboard only, start to finish.** The medication field is focused on load with no click; Tab reaches the add button, remove buttons (which also appear on keyboard focus, not just hover), candidate pills, and the header nav links, each with a visible focus ring from the browser's own default styling (none suppressed in `styles.css`). Enter-to-add was confirmed by dispatching a real `keydown` `Enter` event (the automation tool's own synthesized Return keystroke did not reliably reach the input in this headless setup — a tooling quirk, not an app bug, confirmed by dispatching the equivalent DOM event directly and watching it work). VoiceOver itself was not run (no macOS accessibility inspector in this environment); the semantic building blocks it depends on — labeled fields, `aria-live` regions, `aria-pressed`/`aria-expanded`/`aria-current` on the right elements, and real `<button>`/`<a>` elements throughout — are in place and were checked in the accessibility tree via `read_page`, but an actual screen-reader pass is unverified. Recorded as an open item below.
10. **320px width, dark mode, reduced motion.** 390px dark mode was tested directly (found and fixed two real layout bugs — see `reports/redesign_phase6_search_and_polish.md`) and 1024px light mode was tested directly. 320px specifically was not separately tested (390px is the narrower of the two named breakpoints actually exercised); the layout has no fixed-width elements below 720px, so it should scale, but this is not independently confirmed. `prefers-reduced-motion: reduce` is written in `styles.css` (disables the spinner's animation and the row/card fade-in) but was not tested by actually emulating that media feature in the browser — recorded as an open item below.

## Screenshots

Compared the running site against all six reference images interactively in
the built-in browser pane first, at both breakpoints and both color schemes,
and found the two genuine layout defects Phase 6 documents this way (the
logo/title overlap and the mobile header wrap) before any file was saved.

Also captured real screenshot files with the system's own Chrome
(`--headless=old`, no new dependency — `--headless=new` produced a blank
black capture in this environment, a headless-Chrome/macOS GPU quirk, not an
app bug; confirmed the page's DOM was fully correct under `--headless=new`
too via `--dump-dom`, so this was purely a screenshot-capture issue, worked
around by switching headless modes), committed to
`reports/redesign_screenshots/`: `interactions_desktop.png` (1280×720),
`interactions_mobile.png` (390×844), and `search_desktop.png`
(1280×900), all dark mode — `--force-color-scheme=light` did not
actually change the rendered scheme in this Chrome build (verified by
inspecting the pixels: identical output with and without the flag), so no
light-mode file was captured; light mode was confirmed correct visually in
the interactive browser pane earlier in this phase (see Phase 6) but not
saved as a file. Recorded as an open item below rather than silently
skipped.

## Commands run and results

- `python -m rx_label_search download / collect / base-ingredients / tag / build-index / build-checker-data` (PYTHONPATH=src): full clean local rebuild, 2,481 labels.
- `python -m pytest -q`: 289 passed.
- `cd web && npm test`: 106 passed.
- `npx tsc -p tsconfig.site.json`: clean build.
- Local combined server + built-in browser: all ten cases above.

## What I should check by hand

- An actual VoiceOver pass in Safari (case 9's screen-reader half).
- `prefers-reduced-motion: reduce` and exactly 320px width (case 10's two unverified pieces).
- A light-mode screenshot file, if you want one committed — the three saved files are all dark mode (see "Screenshots" above).

## Open questions

1. **Only dark-mode screenshot files committed.** See "Screenshots" above. Light mode was confirmed correct interactively but a Chrome flag limitation in this environment kept it out of the saved files.
2. **VoiceOver and exact 320px/reduced-motion not independently verified.** See case 9 and case 10 above. The building blocks are in place (semantic HTML, ARIA attributes, the `prefers-reduced-motion` media query in CSS) but the live behaviors are unconfirmed in this run.
