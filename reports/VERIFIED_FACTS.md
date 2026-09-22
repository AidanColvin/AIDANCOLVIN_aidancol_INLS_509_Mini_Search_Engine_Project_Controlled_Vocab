# Verified facts

Every fact below was checked against the named official page or a live request on the date shown. Quotes are verbatim from the fetched page. Anything that could not be confirmed is in `OPEN_QUESTIONS.md`.

## openFDA bulk download (checked 2026-09-21)

| Fact | Status | Source |
| :--- | :--- | :--- |
| Download manifest URL is `https://api.fda.gov/download.json` | Verified. Page: "A json containing links to all downloadable files is available at here" where "here" links to that URL. Live GET returned 200. | https://open.fda.gov/apis/downloads/ |
| Label partitions sit under `results.drug.label.partitions`; each has `file`, `size_mb` (a JSON string), `records` (int), `display_name`; the label section has `export_date` and `total_records` | Verified live. 14 partitions, 1773.84 MB, records sum to 262,883. | https://api.fda.gov/download.json |
| Each partition is a `.json.zip` holding one JSON file with top-level `meta` and `results` (array) | Verified. Page: "Each file is a zipped JSON file." Live: part 14 zip has one member `drug-label-0014-of-0014.json`, 2,883 records. | https://open.fda.gov/apis/downloads/ |
| Label endpoint updates weekly | Verified. Page: "Frequency of API updates: Weekly". | https://open.fda.gov/apis/drug/label/ |
| Rate limits: no key 240/min and 1,000/day per IP; with key 240/min and 120,000/day per key | Verified. Page: "With no API key: 240 requests per minute, per IP address. 1,000 requests per day, per IP address." | https://open.fda.gov/apis/authentication/ |
| An API key is optional for API calls and for bulk downloads | Verified live: key-less API and download calls returned 200. The Authentication page says a key "is required" but also lists no-key limits; the live behavior wins. | https://open.fda.gov/apis/authentication/ |
| `limit` max is 1000; `skip` max is 25000; larger sets need `search_after` | Verified. Page: "Currently, the largest allowed value for the limit parameter is 1000." Live: limit=1001 gives HTTP 400. | https://open.fda.gov/apis/query-parameters/ , https://open.fda.gov/apis/paging/ |
| Bulk data must be re-downloaded in full after every update | Verified. Page: "You need to download all available data files for the endpoint of interest." | https://open.fda.gov/apis/downloads/ |
| Label endpoint held 262,883 labels as of 2026-09-18 | Verified. Manifest: `"export_date": "2026-09-18"`, `"total_records": 262883`. | https://api.fda.gov/download.json |

## openFDA label record layout (live probe of part 14, 2,883 records, 2026-09-21)

| Fact | Status |
| :--- | :--- |
| `id`, `set_id`, `version`, `effective_time` present in every record as strings; `effective_time` matches `^\d{8}$`; `version` matches `^\d+$` | Verified live. |
| `openfda` is present in every record but is an empty dict in 380 of 2,883 | Verified live. Filter 2 therefore tests for a non-empty `openfda` object. |
| Label text fields (`boxed_warning`, `warnings`, `warnings_and_cautions`, `precautions`, `drug_interactions`, `contraindications`, `adverse_reactions`, `adverse_reactions_table`, `spl_medguide`, `pediatric_use`, `controlled_substance`, `dosage_forms_and_strengths`) are lists of strings whenever present | Verified live. |
| There is no `dosage_form` field | Verified live: 0 of 2,883 records. |
| OxyContin record (set_id bfdfe235-d717-4855-a3c8-a13d26dadede) has no `openfda.pharm_class_epc`; `controlled_substance` reads "OXYCONTIN contains oxycodone, a Schedule II controlled substance." | Verified live via the API on 2026-09-21. |
| Zyprexa Relprevv (set_id 11544cba-64a9-49cb-8d74-da228053b252) has a non-empty `openfda` with no `substance_name` | Verified live via the API. Such labels cannot form an ingredient set and are counted separately (see `OPEN_QUESTIONS.md`). |
| openFDA has no label whose `openfda.brand_name` is FLEXERIL | Verified live: the API returned HTTP 404 (no matches) on 2026-09-21. |

## RxNorm (RxNav) API (checked 2026-09-21)

| Fact | Status | Source |
| :--- | :--- | :--- |
| Base is `https://rxnav.nlm.nih.gov/REST/`; `.json` suffix selects JSON | Verified. Page: "Service domain https://rxnav.nlm.nih.gov". | https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getApproximateMatch.html |
| getApproximateMatch: `GET /REST/approximateTerm.json?term=...&maxEntries=...&option=...`; maxEntries 1 to 100, default 20; response `approximateGroup.candidate[]` with `rxcui`, `rxaui`, `score`, `rank`, `name` (omitted for restricted sources), `source` | Verified. Live call for "Flexeril" and "Flexril" both returned rxcui 224954 "Flexeril" at rank 1. | same page |
| findRxcuiByString: `GET /REST/rxcui.json?name=...&search=0|1|2` (0 exact, 1 normalized, 2 exact then normalized); response `idGroup.rxnormId[]` | Verified. Live: `name=CYCLOBENZAPRINE HYDROCHLORIDE&search=2` gives 52101. | https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.findRxcuiByString.html |
| getRelatedByType: `GET /REST/rxcui/{rxcui}/related.json?tty=IN` (space-separated TTYs, sent as `+`, never `%2B`); response `relatedGroup.conceptGroup[].conceptProperties[]`; Active scope only | Verified. Live: 52101 gives IN 21949 cyclobenzaprine; `%2B` gives HTTP 400. | https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getRelatedByType.html |
| TTY codes: IN ingredient, PIN precise ingredient (salt or isomer), MIN multiple ingredients, BN brand name | Verified. | https://www.nlm.nih.gov/research/umls/rxnorm/docs/appendix5.html |
| getRxNormName: `GET /REST/rxcui/{rxcui}.json`; response `idGroup.name`; empty `idGroup` for non-active concepts | Verified live: 21949 gives "cyclobenzaprine"; 224954 gives `{"idGroup":{}}`. | https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getRxNormName.html |
| getRxcuiHistoryStatus: `GET /REST/rxcui/{rxcui}/historystatus.json`; scope current and historical; `rxcuiStatusHistory.derivedConcepts.ingredientConcept[]` gives `ingredientRxcui` and `ingredientName` | Verified live: 224954 (Flexeril, status Obsolete, BN) gives ingredient 21949 cyclobenzaprine. This is the only RxNorm route from an obsolete brand to its ingredient, because related.json is Active-scope and returns nothing for it. | https://rxnav.nlm.nih.gov/REST/rxcui/224954/historystatus.json |
| Rate limit: no more than 20 requests per second per IP; NLM recommends caching results 12 to 24 hours; no API key needed | Verified. Page: "send no more than 20 requests per second per IP address". | https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html |
| Attribution: "This product uses publicly available data from the U.S. National Library of Medicine (NLM), National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product." | Verified; must appear in the tool. | same page |
| Drug-Drug Interaction API discontinued: "The Drug-Drug Interaction API will be discontinued on or about January 2, 2024." (dated July 3, 2023); `/REST/interaction/` returns 404 live | Verified. The old InteractionAPIs.html page itself returns 403. | https://lhncbc.nlm.nih.gov/RxNav/ |
| Data updates monthly following the RxNorm release; live version 08-Sep-2026 | Verified. | https://lhncbc.nlm.nih.gov/RxNav/ , https://rxnav.nlm.nih.gov/REST/version.json |

## DailyMed (checked 2026-09-21)

| Fact | Status | Source |
| :--- | :--- | :--- |
| Label page by set id: `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={SETID}` | Verified live: HEAD and GET return 200 with no redirect; title "DailyMed - OXYCONTIN- oxycodone hydrochloride tablet, film coated, extended release". The pattern is not written on the three official support pages; DailyMed's own pages link to it. | https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=bfdfe235-d717-4855-a3c8-a13d26dadede |
| Web service: base `https://dailymed.nlm.nih.gov/dailymed/services/`, version `v2`, `/spls/{SETID}` returns the SPL (XML only; `.json` returns 415); `/spls.json?setid=...` returns JSON metadata | Verified. Page: "/spls/{SETID} Returns an SPL document for specific SET ID." | https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm |
| No rate limit or usage terms are stated for the web service | Unverifiable (none found on the three official pages). | same page |

## FDA clinical decision support guidance (checked 2026-09-21)

| Fact | Status | Source |
| :--- | :--- | :--- |
| Guidance page shows "January 2026", Final; the PDF cover says "Document issued on January 29, 2026. This document supersedes 'Clinical Decision Support Software' issued on January 6, 2026." | Verified. FDA's own word is "supersedes", not "re-issued". | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software , https://www.fda.gov/media/109618/download |
| Criterion (4): "Intended for the purpose of enabling an HCP to independently review the basis for the recommendations that such software presents so that it is not the intent that the HCP rely primarily on any of such recommendations to make a clinical diagnosis or treatment decision regarding an individual patient" | Verified from the PDF. | https://www.fda.gov/media/109618/download |
| "FDA's existing digital health policies continue to apply to software functions that meet the definition of a device, including those that are intended for use by patients or caregivers." | Verified from the landing page. | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software |

## openFDA drug label field layout (checked 2026-09-21, from the official field YAML)

| Fact | Status | Source |
| :--- | :--- | :--- |
| The label endpoint's YAML schema has 178 top-level properties; `openfda` has 21 sub-properties; no field or sub-field is named `dosage_form` anywhere in the label schema | Verified. Live search for `_exists_:dosage_form` and `_exists_:openfda.dosage_form` both return `NOT_FOUND`. | https://open.fda.gov/fields/druglabel.yaml |
| `openfda.pharm_class_cs` is "chemical structure classification of the drug product's pharmacologic class" | Verified. Live values end in the suffix `[CS]` (for example "Anti-Inflammatory Agents, Non-Steroidal [CS]"), not `[Chemical/Ingredient]` as the YAML's example text shows; the doc/live mismatch is noted for later spot checks. | https://open.fda.gov/fields/druglabel.yaml |
| `openfda.brand_name` is described only as "Brand or trade name of the drug product." | Unverifiable: no official page states that it is copied from the NDC Directory proprietary name, or the word "proprietary". | https://open.fda.gov/fields/druglabel.yaml |
| `effective_time` is `YYYYMMDD`; `version` is a string; `is_original_packager` is the one `openfda` field typed as a plain string rather than an array | Verified live. | https://open.fda.gov/fields/druglabel.yaml |
| Fields ending in `_table` hold SPL/HTML-like table markup as strings, including non-HTML tags such as `<paragraph>` and `<content styleCode="bold">` | Verified from a live record. The YAML itself gives no markup description for these fields. | live API record, naproxen |
| `_missing_:openfda` (175,889 of 262,883 records on 2026-09-18) returns a record with `"openfda": {}`, an empty object, not a missing key | Verified live. Confirms filter 2's "has openfda" test must check for a non-empty object. | live API |

## Vercel Python functions (checked 2026-09-21)

| Fact | Status | Source |
| :--- | :--- | :--- |
| Supported Python versions: 3.12 (default), 3.13, 3.14; pinned with `pyproject.toml` `requires-python`, a `.python-version` file, or `Pipfile.lock`; no `runtime` key in `vercel.json` for Python | Verified. | https://vercel.com/docs/functions/runtimes/python/python-version |
| Without a detected framework preset (no FastAPI/Flask/Django dependency declared), each `.py` file under `/api` becomes its own function; each file must define a top-level `app`, `application`, or a `handler` class inheriting `http.server.BaseHTTPRequestHandler` | Verified. This project has no dependencies, so `api/search.py` and `api/check.py` will each become a function without any framework interfering. | https://vercel.com/docs/functions/runtimes/python/api-directory |
| Hobby plan: 12 functions per deployment for the file-based `/api` approach | Verified. | https://vercel.com/docs/functions/runtimes#functions-created-per-deployment |
| Python function bundle limit is 500 MB uncompressed (250 MB for other runtimes) | Verified. | https://vercel.com/docs/functions/limitations |
| Memory: 2 GB / 1 vCPU default and max on Hobby; 2 GB default, 4 GB / 2 vCPU max on Pro; cannot be set in `vercel.json` | Verified. | https://vercel.com/docs/functions/limitations |
| Duration with Fluid compute (default for projects created after 2025-04-23): Hobby 300s default and max; Pro 300s default, 800s max, 1800s extended (beta, set per-function) | Verified. | https://vercel.com/docs/functions/limitations |
| Request and response body limit: 4.5 MB, both directions, same on every plan | Verified. | https://vercel.com/docs/functions/limitations |
| `vercel.json` `functions.excludeFiles` (glob) controls what ships in a Python bundle; everything reachable at build time ships by default; `includeFiles` is not read by the Python builder | Verified for `excludeFiles`. `includeFiles` unverifiable in docs; the builder source has no `includeFiles` handling for Python. | https://vercel.com/docs/functions/runtimes/python |
| GitHub Actions deploy: `vercel pull --yes --environment=production --token=...`, `vercel build --prod --token=...`, `vercel deploy --prebuilt --prod --token=...`, with `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` as job env vars from secrets | Verified. | https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel |
| `vercel.json` `rewrites` route `/` and other non-file paths to `index.html`; the filesystem (a static `index.html`, files under `api/`) takes precedence over rewrites, so no rewrite is needed to serve them directly | Verified. | https://vercel.com/docs/project-configuration/vercel-json |
| A Python function can read files bundled with it; `open()` with a relative path resolves against the project root, not the function's own directory; the runtime filesystem is read-only except `/tmp` (500 MB) | Verified. | https://vercel.com/docs/functions/runtimes/python |

## FDA enzyme table and ONC high-priority DDI list (transcribed and independently checked 2026-09-21)

* `data/reference/fda_enzyme_table.json`: transcribed from https://www.fda.gov/drugs/drug-interactions-labeling/drug-development-and-drug-interactions-table-substrates-inhibitors-and-inducers, 8 tables, 53 rows. An independent re-parse of the same page found zero discrepancies across every cell of all 8 tables.
* `data/reference/onc_high_priority_pairs.json`: transcribed from Phansalkar et al. 2012 (PMC3422823), Table 2, "List of candidate drug–drug interactions (DDIs) discussed and the final pairs accepted by the expert panel as critical DDIs," 15 rows. An independent re-check of the source found two incomplete footnotes in the first transcription; both were corrected in the committed file (the `*` footnote's second sentence, and the missing `†` footnote about the FDA/Flockhart enzyme table source).
