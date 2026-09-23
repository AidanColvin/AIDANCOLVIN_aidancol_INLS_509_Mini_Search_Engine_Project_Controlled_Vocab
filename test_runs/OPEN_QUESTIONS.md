# Open questions (logged instead of stopping to ask)

1. **Section 6 was empty in the pasted pack.** Grading uses the 2026-09-22 answer key already in the repository (data/reference/drug_interaction_screen_fixture.json). Its L01 matches the pack's L01 and its schema matches Section 4. The owner confirmed this choice in chat on 2026-09-23.
2. **The pack asks for A–D; the site is A–E.** The owner chose to keep A–E and map it (E→D, D→C, C and B→B, A→A). The mapping is printed in every EVALUATION_REPORT.md.
3. **L40 "dose ceiling" for sertraline 200 mg is a minor item that says "a ceiling check should pass."** It is scored as a HIT only if the site states that the dose is at or within the labeled maximum. Staying silent is scored as a MISS.
4. **L41 duplicate sertraline: "the app should ask, not silently sum or silently drop."** It is scored on a duplicate-entry flag that names both lines. The site cannot ask a question, so a flag that says "either a duplicate entry or 100 mg/day" is treated as the intended behavior.
5. **Key categories vs. site wording.** Category equivalence is judged by keyword families (scripts/grade_test_pack.py, CATEGORY_WORDS). A site alert that names the mechanism differently (for example "raises exposure" for "CYP inhibition") counts only if one of those words appears.
