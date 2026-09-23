# User feedback: one doctor, 41 patients

Site: https://rx-label-search-aidancolvins-projects.vercel.app/ (main 6d02dc3), Chrome at 1440x900, then 390x844 for L01, L12, L24, L41. Each patient got a fresh browser. For each one I pasted the whole medication line and pressed Return.

## The short version

I pasted 41 medication lists and got no interaction screen back for any of them. Every one of the 244 entries came back as "not found" or "Not a medication name we know." The site had the answers: under almost every entry it offered the correct drug ("Did you mean: warfarin sodium 5 mg [coumadin]"). But it would not use them until I clicked each suggestion, one at a time. For a six-drug list that is six extra clicks, and at the end of it I still would have lost the doses and schedules I typed.

## Where to type, and Return

- **Where to type: good.** The cursor was already in the box on all 41 loads (`INPUT#add-med`, placeholder "warfarin 5 mg daily"). I never had to click to start typing. The page was usable within about 1 second.
- **Return: works, but it doesn't matter.** The site splits a pasted line on commas as soon as it lands, so all 5–7 entries appeared before I pressed Return. Return did not change the outcome.
- **The line format failed.** I pasted the format every prescriber writes: `Brand (generic) dose frequency = daily total`, for example `Zyprexa (olanzapine) 10 mg once daily = 10 mg/day`. The site treated each whole entry as one drug name and could not find it. This is the defect behind everything else in this file.

## Reading the results

- **Nothing to read at a glance.** The top of the Interactions column said "0 of 5 medications checked" and "Not checked". It listed every entry as ": not found. Edit it in the list, or remove it." Below that it said "No warning found in the labels checked."
- **"No warning found" is dangerous here.** Under the list of "not found" entries, the page still printed the big "No warning found in the labels checked." L05 contains warfarin, amiodarone, Bactrim, aspirin, and clopidogrel. A tired reader could take that line as reassurance. When nothing was checked, the page should say so instead: "Nothing was checked".
- **The A–E strip is clear but empty.** The row of five boxes (E Avoid combination … A Minor) is readable without reading any prose. With nothing checked it showed "–" in every box, which looks exactly like "all clear".
- **A wall of unrelated label text.** Under each entry, the right column showed "What the labels say about …" with four label snippets and a "Show 8 more" button. They were mostly unrelated to the drug:
  - Coumadin (L05): "Campath / alemtuzumab" first, then desloratadine.
  - Ambien (L01): "GOCOVRI / amantadine" and "ADDYI".
  - Zoloft (L41): "MARPLAN / isocarboxazid" before sertraline itself.
  - Inderal (L23): "Ergomar Sublingual / ergotamine tartrate".

  The L01 page is about 7,000 px tall, and the L41 phone page is about 9,800 px. Almost all of that is these snippets.
- **The suggestions misread the dose.** L01 Xanax 1 mg three times daily was suggested as "alprazolam 3 mg [xanax]", which is the daily total, not the strength. L23 Glucotrol 10 mg twice daily was offered "glipizide 5 mg" first, and Inderal 40 mg twice daily was offered "propranolol hydrochloride 80 mg". A doctor who clicks the first suggestion gets a wrong strength on the card.

## Language

The wording is plain: "Not found in the FDA labels. Did you mean:", "Edit it in the list, or remove it." It is not intimidating. But it asks the doctor to do the parsing work the tool should do.

## What to do next

No flag was shown, so no flag told me what to do. The only instruction on the page was to edit or remove my own entries.

## Links

Every "Open on DailyMed" link I checked returned HTTP 200 (466 unique links, all 200). They are drug-specific (DailyMed setid pages). But none was attached to an interaction, because there were none. The links sat under the unrelated snippets, so a Campath label link under Coumadin was working and specific, and useless.

## Totals and duplicates

- No totals: no card showed a daily total, because no entry was resolved.
- No merging: the site did not merge the two Zyprexa lines (L01), the two Coumadin lines (L05), OxyContin + Roxicodone (L06), Xanax + Xanax XR (L12), Zoloft + generic sertraline (L41), or Synthroid 0.1 mg + levothyroxine 100 mcg (L41). It showed each as its own "not found" card.
- The Coumadin schedule (Mon/Wed/Fri vs other days), weekly methotrexate, weekly Ozempic, units of insulin, and the fentanyl mcg/h patch never reached any dose logic.

## Speed

Fast for what it did. The page settled 2.4–4.5 s after Return (median 3.2 s), with no errors in the console and no 4xx/5xx responses.

## Mobile (390x844)

- The layout stacks correctly: title, input, the Interactions column, then the medication cards.
- The input is focused on load there too.
- The same failure makes the phone page about 9,800 px tall (L41). I had to scroll through 24 unrelated label snippets to reach the footer.
- The A–E strip fits on one row and is readable.

## What I would tell the developer, in order

1. Accept `Brand (generic) dose frequency = total`. Take the generic in parentheses as the drug and the text before "=" as the dose and schedule. Treat the "= total" as the prescriber's own arithmetic, useful as a cross-check.
2. When an entry can't be resolved but there is exactly one confident suggestion, use it automatically and say so. Don't wait for a click.
3. Never print "No warning found" when nothing was checked.
4. Hide the "What the labels say about …" snippets for entries that are medication lines. They are noise.
5. Then the clinical content: merged totals, duplicates, class rules, and grouping statements.
