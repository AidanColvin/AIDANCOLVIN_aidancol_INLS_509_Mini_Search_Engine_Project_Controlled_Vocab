# Data sources

Every clinical statement this tool shows comes from one of the sources below or from label text itself. No source not listed here is used.

## openFDA Drug Label endpoint

* **URL:** https://open.fda.gov/apis/drug/label/
* **License / terms:** https://open.fda.gov/license/ ; https://open.fda.gov/terms/ (public domain FDA data; openFDA's disclaimer applies)
* **Used for:** the entire label collection, all PDLA tagging, all search text, all interaction-checker evidence.
* **Access method:** bulk download files listed at https://api.fda.gov/download.json for full builds; the API (https://api.fda.gov/drug/label.json) for fixtures and spot checks.
* **Access date:** 2026-09-21. Export date of the label data used: 2026-09-18.
* **Update cadence:** weekly, per openFDA's own documentation.

## NLM RxNorm (RxNav REST API)

* **URL:** https://rxnav.nlm.nih.gov/REST/
* **License / terms:** https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html (free of charge; requires the attribution statement below)
* **Used for:** typo-tolerant name matching for names not in the local dictionary, and base-ingredient (salt) rollup for duplication checks.
* **Access date:** 2026-09-21.
* **Update cadence:** monthly, following the RxNorm release.
* **Required attribution (shown in the tool):** "This product uses publicly available data from the U.S. National Library of Medicine (NLM), National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product."
* **Not used:** the RxNav Drug Interaction API, discontinued by NLM on or about January 2, 2024.

## DailyMed

* **URL pattern:** `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={SETID}`
* **Used for:** the evidence link shown on every alert, so a reader can open the full label.
* **Access date:** 2026-09-21 (URL pattern verified with a live request; not stated on DailyMed's own support pages, see `reports/VERIFIED_FACTS.md`).

## FDA "Drug Development and Drug Interactions: Table of Substrates, Inhibitors and Inducers"

* **URL:** https://www.fda.gov/drugs/drug-interactions-labeling/drug-development-and-drug-interactions-table-substrates-inhibitors-and-inducers
* **Used for:** the class-name gazetteer that T17 (Contraindicated Combination) uses to recognize a named enzyme-inhibitor or -inducer class in a contraindication sentence.
* **Access date:** 2026-09-21. Transcribed into `data/reference/fda_enzyme_table.json`, independently re-checked cell by cell against the live page with zero discrepancies.
* **Caveat shown in the tool:** FDA states the tables give examples and are not exhaustive.

## ONC high-priority drug-drug interaction list

* **Citation:** Phansalkar S, Desai AA, Bell D, Yoshida E, Doole J, Czochanski M, Middleton B, Bates DW. "High-priority drug-drug interactions for use in electronic health records." J Am Med Inform Assoc. 2012;19(5):735-743. PMCID: PMC3422823.
* **Used for:** a test floor only, to check that the checker fires on well-established high-priority interactions where both drugs are in the collection. It is never shown to the user as tool output.
* **Access date:** 2026-09-21. Transcribed into `data/reference/onc_high_priority_pairs.json` from the paper's Table 2, independently re-checked against the source.
* **Caveat:** the panel states this is not a complete list of all contraindicated pairs.

## Active-metabolite pairs

* **Source:** FDA drug labels through the openFDA Drug Label endpoint, same as above. Each pair in `data/reference/active_metabolites.json` cites the specific label sentence, field, `set_id`, and `effective_time` that states the relationship. No pair is hand-typed without a cited source.
* **Used for:** duplication flags when two listed drugs are an active-metabolite pair (for example venlafaxine and desvenlafaxine).

## Not used

Lexicomp / UpToDate Lexidrug, Micromedex, First Databank, Medi-Span, Multum, Medscape, Drugs.com, any scraped website, DrugBank data, FAERS or TWOSIDES statistical signals, the discontinued RxNav Drug Interaction API, and this tool's own recall of clinical facts. DDInter 2.0 was not built into this version; it is reserved as a possible future separate, clearly labeled layer, per the build prompt.
