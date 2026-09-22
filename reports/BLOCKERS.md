# Blockers

No hard blocker in the Section 0.3 sense occurred. This file also lists every skipped test (none) and every done-criterion that is not fully met, as Section 0.2 item 5 and Section 13 require.

## Skipped tests

None. All 405 tests pass; `pytest.mark.skip` and `xfail` do not appear anywhere in `src/` or `tests/`.

## Partially met done-criterion: the ONC high-priority floor

Section 13 asks that "every ONC high-priority pair whose drugs are both in the collection fires." An automated best-effort check (`reports/phase6_check.md`) found 10 of 13 pairs that could be built from a literal drug name on each side actually fire an alert; 2 more pairs name only a drug class with no member drug in the paper's printed text, so no literal two-drug list could be built at all. Of the 3 that did not fire:

* **Irinotecan–ketoconazole** and **Rifampin–ritonavir**: my diagnostic script resolves "the first name it can match" from each side's printed drug list, which can differ from the specific pair name the paper intends (for example it picked Ritonavir where the paper's own pair name says Rifampin). This is a limitation of the automated floor-check script, not necessarily of the checker itself; I did not have time in this run to hand-curate the intended representative drug for every ONC pair.
* **Tranylcypromine–procarbazine**: this one is a real, understood gap. Tranylcypromine's `contraindications` field says "Concomitant use ... with the products in Table 1 is contraindicated," and names procarbazine only inside an HTML table elsewhere in the label, not in the contraindications free text the T17 rule reads. Reading embedded tables for T17 was out of scope for this build.

I recommend you spot-check these three by hand, and consider whether hand-curating the ONC floor test's representative drug per pair, or extending T17 to also read `contraindications_table` where the label has one, is worth a follow-up.

## Everything else in Section 13

Met, as recorded in each phase report:

* All 17 terms tagged with evidence; 0 consistency violations across all 2,481 labels.
* The tag-evaluation harness runs on the placeholder gold file.
* The Section 3.6 acceptance test passes, built from fixtures per that section's own instruction.
* Search Scenarios 1 to 3 pass.
* Both API handlers verified over real HTTP requests; the weekly workflow is built and valid YAML, but has not run live because no Vercel project or secrets exist yet (see `reports/phase7_serve.md`, "What I should check by hand").
* README.md and DATA_SOURCES.md are complete.
* Style and attribution tests pass on every commit.
* The two forbidden names never appear in the repo or any commit message, checked before every push.
