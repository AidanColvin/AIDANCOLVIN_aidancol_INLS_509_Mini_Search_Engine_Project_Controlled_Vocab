# User feedback: one doctor, 41 patients (run 2026-09-23_0804)

Site at main 928b6b8. Chrome at 1440x900, plus 390x844 for L01, L12, L24, and L41. Each patient got a fresh browser. I pasted the whole line and pressed Return.

## Where to type, and Return
- The cursor was in the box on every load (41/41). Pasting the whole line split it into entries at once. Return worked. I never needed a click.
- Every one of the 244 entries was recognized. My own format, `Zyprexa (olanzapine) 10 mg once daily = 10 mg/day`, now works exactly as written. Aspirin, Tums, Feosol, and Sprintec have no single-ingredient label in the collection, but they were still recognized by their ingredients.

## Reading the results
- **The grade is visible without reading.** The A–E strip at the top counts each grade. For L05 it read "D 3" with the caption "Most severe: D, Consider changing therapy." Each card starts with a black grade badge.
- **Each card says the count and the risk in one line:** "4 drugs: risk of serious bleeding, especially stomach and gut bleeding" (L05), "Nolvadex with 2 drugs that block CYP2D6: tamoxifen may not work" (L09), "5 serotonergic drugs: risk of serotonin syndrome" (L02).
- **Every flag tells me what to do.** For example, L05 warfarin: "Choose another drug if possible; otherwise lower the warfarin dose (often 25 to 50%) and check the INR within 3 to 5 days."
- **The language is plain.** Terms like "QT interval" and "CYP2D6" are explained in the same sentence.
- **Wall of text on a phone.** L24 had 10 cards. At 390 px wide, the page ran to about 9,600 px, because every card shows the full label quote, "Why it happens", "What to do", and the sources. On a desktop, the two columns make it manageable (L24 is about 7,100 px). This is the main thing left to fix.

## Links
- Every card links each drug's own label on DailyMed, plus any study it relies on (PubMed). All 158 unique links worked (147 returned 200, and 11 PubMed links returned 203, which is PubMed's normal reply to scripted requests).
- Some label quotes are generic. The bleeding card quotes Coumadin's "Risk factors for bleeding include … certain concomitant drugs". It is correct, but it is not about the specific pair. The card's own "Why it happens" says the specific part.

## Totals and duplicates
- "Totals by ingredient" sits above the medication cards. It showed:
  - L05: warfarin 25 mg/week (5 mg Mon/Wed/Fri plus 2.5 mg on the other days)
  - L06: oxycodone 120 mg/day max, 180 MME
  - L12: acetaminophen 4,300 mg (4.3 g)/day, from 2 entries
  - L41: levothyroxine 200 mcg (0.2 mg)/day, from 0.1 mg plus 100 mcg
  - L10: methotrexate 15 mg/week, with no daily figure
  - L24: total opioid dose 70 MME/day
- Duplicates are named plainly. L41: "Duplicate: Zoloft (sertraline) and sertraline (sertraline) are the same drug under different names: combined sertraline 100 mg/day". L01: "Zyprexa (olanzapine) is entered on two lines: combined olanzapine 12.5 mg/day".

## Speed
The page settled within the runner's 0.4 s poll after Return on nearly every list; the worst was 1.6 s. The check starts on paste, before Return.

## Mobile
The phone layout fits 390 px with no sideways scroll. The strip and the first card are readable. Everything below them is long, as described above.
