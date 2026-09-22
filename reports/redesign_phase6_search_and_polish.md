# Redesign run, 2026-09-22 — Phase 6: Label search view, dark mode, phone layout

## What was built

- `web/src/search.ts`: the pure logic Section 9.3 assigns it — snippet
  segmenting with the query's words marked bold, the vocabulary hierarchy
  constant (T10 under T07; T06 and T12 under T11; T14–T17 under T13, cited
  to `MiniVocab_Aidan_Colvin_aidancol.md` Section 1, since `/api/search` does
  not return it), grouping terms by `property_group` in first-appearance
  order with each group's narrower terms reordered to sit after the term
  they narrow, active-filter tag splitting, and the brand/generic title rule.
- `web/src/render_search.ts`: the search field, the filters panel (rendered
  twice — once inline in an `<aside>` for the sidebar, once inside a
  `<dialog>` for the mobile bottom sheet — from the same pure builder
  function, so the two never drift out of sync), the operator toggle, and
  the results list with bolded snippets, tag pills, and DailyMed links.
- `public/styles.css` additions: the full responsive layout (`<768px`
  breakpoint: header stacks, filters move to the dialog, the search body
  goes single-column) and the complete dark-mode custom-property set from
  Section 3.2.

## Two real layout bugs this phase's local verification caught

1. **The home logo overlapped the header title.** `.app-header__bar` had
   only 16px of left padding, but the absolutely-positioned home link
   (`left: 12px`, 44px wide) needed 60px of clearance; on anything narrower
   than the 1280px-wide design mockup, "Drug" rendered directly under the
   logo icon. Fixed by giving the bar 60px of left padding at every width
   (matches the position exactly at any viewport, since the home link's
   position is fixed regardless of viewport width).
2. **The mobile header wrapped to three lines instead of stacking.** The
   `<768px` media query changed the header's own `flex-direction` to
   `column` but left `.app-header__bar` as a single row still holding both
   the name and the full segmented control, so at 390px both compressed and
   wrapped badly. Fixed by making the bar wrap (`flex-wrap: wrap`), giving
   the name an ellipsis instead of a wrap, and putting the nav on its own
   full-width row — now matches image 03's stacked mobile header exactly.

Both found by loading the real compiled site in the browser at narrow
widths, not by reading the CSS — screenshots in
`reports/redesign_screenshots/` (Phase 7) show the before and after.

## Contrast ratios

Computed with the WCAG relative-luminance formula against every token pair
Section 3.2 names; full table in `reports/VERIFIED_FACTS.md`. Every text
pair clears 4.5:1 and the field border (the one interactive-component
boundary the token list names) clears 3:1 in both themes. The decorative
row hairlines sit near 1.3:1, which WCAG 1.4.11 exempts for a boundary that
is not needed to identify a component or its state — recorded as a
deliberate, checked choice, not an overlooked gap.

## Commands run and results

- `npm test`: 103 passed (unchanged from Phase 5; this phase's `search.ts` tests were already written and counted then).
- `npx tsc -p tsconfig.site.json`: clean.
- Manual verification in the built-in browser at 1024px/desktop and 390px/dark, light and dark `prefers-color-scheme`: see Phase 7's report for the full case list and screenshots.

## What I should check by hand

- The filters dialog on mobile is a native `<dialog>` opened with
  `showModal()`; it was verified to open, select a filter, and close with
  the "Done" button in the built-in browser, but a native iOS/Android Safari
  or Chrome pass would be worth a quick look given `<dialog>` styling can
  vary slightly across engines.

## Open questions

None new for this phase beyond the two layout fixes above, which are closed.
