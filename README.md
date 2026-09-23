# AIDANCOLVIN_aidancol_INLS_509_Mini_Search_Engine_Project_Controlled_Vocab
INLS 509-001 Information Retrieval Mini Search Engine Project, Part II: Mini Controlled Vocabulary

Hey, thanks so much for being my peer exchange user! I know everyone's busy, so I really appreciate you taking the time to help me out. It should only take a few minutes.

## Instructions

1. Open [MiniVocab_Aidan_Colvin_aidancol.md](https://github.com/AidanColvin/AIDANCOLVIN_aidancol_INLS_509_Mini_Search_Engine_Project_Controlled_Vocab/blob/main/MiniVocab_Aidan_Colvin_aidancol.md).
2. Take a look at my planned document collection and controlled vocabulary.
3. Think of a scenario where you'd use my controlled vocabulary to search or refine results.
4. Write your question in complete sentences.
5. Pick the term(s) from my vocabulary that fit your question.
6. Send me your name, PID, question, and selected term(s) at aidancol@live.unc.edu.

If you want me to do yours too, just send it my way and I'll get it done. Thanks again, it means a lot!

## Tool

This repo also holds **Drug Interaction Screen**, live at https://rx-label-search-aidancolvins-projects.vercel.app and built here as the Python package `rx_label_search`, which turns the Part 1 collection and the Part II PDLA vocabulary above into a working search engine, tagger, and drug-drug interaction checker over FDA prescription drug labels. It is not limited to one drug class. See `DATA_SOURCES.md` for every data source it uses and `reports/FINAL_REPORT.md` for the full build record.

**What it does:**

* **Search.** Keyword search over every label's main text and openfda names, ranked with BM25, refined with PDLA term filters (AND or OR). On the site this runs behind the one box: a word that is not a medication name is looked up in the labels.
* **Tag.** Assigns all 17 PDLA terms to every label, with the field and sentence behind each tag, and categorizes each drug by active ingredient, FDA pharmacologic class, route, and DEA schedule.
* **Check.** Takes a free-text medication list of any length, resolves brand names, generic names, and typos, and flags drug-drug interaction risks the FDA labels state, with the label sentence and a DailyMed link behind every flag.
* **Rate.** Gives every flag a heuristic tier based on which label section its evidence came from: Contraindicated, Boxed warning, Warning, or Interaction note.

**Notice shown on every result:** "Results reflect FDA label text as of {build date}. \"No warning found\" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database." The only negative wording it ever uses is "No warning found in the labels checked."

**How to use it:** it's one page and one box. The cursor starts in it; type a medication and press Return, or paste a whole list separated by commas, semicolons, or new lines. Each entry becomes a row: the name the checker matched, the dose it read, and the label's own safety terms (Boxed Warning, QT Prolongation Risk, Renal Dose Adjustment, and so on). An entry the checker can't place says what happened and what to do ("More than one label matches. Choose one:" or "Not found in the FDA labels. Did you mean:"). Anything that isn't a medication name at all, like "grapefruit" or "drowsiness", is looked up in the label text instead, with the labels of the drugs already on the list shown first. Results appear under the list as soon as they're ready: alert cards with the drug names, a tier, the label sentence, and a DailyMed link; or "No warning found in the labels checked."

### Setup

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e ".[test]"
```

### Running the build pipeline

Each command reads the previous command's output from `data/build/` (gitignored) and writes its own. Run them in order for a full weekly-style rebuild; the GitHub Actions workflow at `.github/workflows/rebuild.yml` runs the same sequence on a schedule and on push to `main`.

```bash
PYTHONPATH=src python -m rx_label_search download              # fetch the openFDA bulk label files
PYTHONPATH=src python -m rx_label_search collect                # apply the Part 1 scope filters, dedupe, build the name dictionary
PYTHONPATH=src python -m rx_label_search verify-collection       # check the built collection's invariants
PYTHONPATH=src python -m rx_label_search base-ingredients        # map every substance to its RxNorm base ingredient
PYTHONPATH=src python -m rx_label_search tag                     # run all 17 PDLA rules, cached and parallel
PYTHONPATH=src python -m rx_label_search build-index              # build the search index (lean ranking file + snippet shards)
PYTHONPATH=src python -m rx_label_search build-checker-data       # build the interaction checker's lookup tables
```

### Using the tool from the command line

```bash
PYTHONPATH=src python -m rx_label_search query "muscle spasm" --term T14 --term T15 --operator AND --limit 10
PYTHONPATH=src python -m rx_label_search check "10 mg Zyprexa X 1 daily, 20 mg adderall X 3 daily, Lyrica 100 mg X 3 daily"
PYTHONPATH=src python -m rx_label_search parse-meds "10 mg ambien X daily"
PYTHONPATH=src python -m rx_label_search resolve "trazdone" --no-rxnorm
```

### Evaluating the tagger and the search index

```bash
PYTHONPATH=src python -m rx_label_search gold-template --sample-size 20          # write a placeholder gold file
# then, for each label and term you hand-label:
PYTHONPATH=src python -m rx_label_search gold-label --gold-file data/gold/my_gold.json --set-id <SET_ID> --term T06 --value true --rationale "..."
PYTHONPATH=src python -m rx_label_search evaluate-tags --gold-file data/gold/my_gold.json
PYTHONPATH=src python -m rx_label_search evaluate-search --queries queries.tsv --judgments judgments.tsv --k 10
```

`data/gold/gold_sample_PLACEHOLDER.json` is a demonstration file with obviously fake values; it proves the harness runs and is never used as real ground truth. See `reports/phase4_evaluate.md` for how to record real hand labels.

### Running the tests

```bash
.venv/bin/python -m pytest -q
```

`tests/test_style.py` and `tests/test_no_attribution.py` enforce the coding and attribution rules on every file in `src/`, `tests/`, and `api/`.

### Building and testing the front end

```bash
cd web
npm ci
npx tsc          # type-checks web/src/ and web/tests/ against tsconfig.json
npm test         # type-checks, then runs the compiled tests with node:test
npm run build    # compiles web/src/ to public/js/, the deployed bundle
```

`web/tests/style.test.ts` enforces the Section 8.2 coding rules (a three-line
Takes/Does/Gives comment on every top-level function, explicit parameter and
return types, no `any`, a typed `catch`, no shadowed parameter names) by
tokenizing every file in `web/src/` and `web/tests/` with TypeScript's own
compiler API — see `reports/redesign_phase4_toolchain.md` for why that
needed the compiler's scanner rather than the classic parser API.

### Serving it as a website

`api/search.py` and `api/check.py` are stateless Vercel Python functions (no framework, file-based routing) that call the same package the CLI does. `public/index.html`, `public/styles.css`, and the compiled `public/js/` (built from `web/src/`, gitignored) are the front end: one page and one field, already focused, with inline spelling correction and candidate choice, the label's safety terms on every resolved row, a label-text lookup under any entry that is not a medication name, and alert cards graded A to E, worst first, with totals by ingredient above the medication cards. There is no separate search page; the label search index serves those lookups. Deploys happen only through `.github/workflows/rebuild.yml`, never by hand; see `reports/phase7_serve.md` for the original Vercel project setup and `reports/redesign_phase4_toolchain.md` for the CI step that builds the front end before each deploy.

### Validating the interaction checker against a key

`scripts/validate_interactions.py` scores the checker's `/api/check` output against a blind-test fixture of patient medication lists and their expected interactions (`data/reference/drug_interaction_screen_fixture.json`). It runs every list in four entry-order and separator variants, scores each expected item as a hit, partial, or miss against a documented category and severity map, and writes a report.

```bash
# start a local server that serves public/ and the same /api/check and /api/search code Vercel runs
PYTHONPATH=src .venv/bin/python scripts/dev_server.py --port 8000 &

PYTHONPATH=src .venv/bin/python scripts/validate_interactions.py \
  --base-url http://127.0.0.1:8000 \
  --out-md docs/interaction-validation.md \
  --out-json docs/interaction-validation.json
```

That harness calls the API and predates the class rules; its last result is in [`docs/interaction-validation.md`](docs/interaction-validation.md).

### The black-box test pack

`TEST_PACK.md` holds 41 blind patient lists, a 36-row clinical rulebook, and the answer key. A Playwright runner (`test_runs/<run>/tools/run_pack.js`) pastes each list into the public site in a fresh browser and captures what the page shows. `scripts/grade_test_pack.py` scores only those captures. `scripts/report_test_pack.py` writes the per-list results, the evaluation report, and the rulebook coverage. `scripts/diff_test_runs.py` compares two runs. Every run is committed under `test_runs/`, with `LESSONS_LEARNED.md`, the generalization lists G01–G06, and `FINAL_SUMMARY.md`.

The class rules behind the checker live in `data/reference/interaction_knowledge.json`: 90 rules (shared-effect groups, perpetrator-victim pairs with label dose caps, therapeutic duplication, and dose ceilings). Each rule has a grade, a mechanism, an action, its rulebook row, and its sources. `build-checker-data` also writes `data/build/rule_evidence.json`, which holds the FDA label sentence found for each rule and label.

### Design choices worth knowing

* **No stemming in this version.** The tokenizer lowercases, strips punctuation, and keeps numbers, with no stemming, so "spasm" and "spasms" are different tokens. This keeps ranking simple and predictable for v1; a future version could add stemming or a synonym list.
* **Precision over recall.** Every PDLA rule omits a term rather than guessing when the field it needs is missing or ambiguous. The interaction checker never says "safe" and marks an ambiguous name "needs confirmation" instead of picking silently.
* **Every tag and alert carries evidence.** A term with no evidence is not assigned; an alert with no evidence is not raised.

### Files (added by this build)

| Path | What it is |
| :--- | :--- |
| `src/rx_label_search/` | the package: `collect/`, `text/`, `normalize/`, `vocabulary/`, `search/`, `interactions/`, `evaluate/`, `serve/`, `storage/`, plus `records.py` and `cli.py` |
| `api/search.py`, `api/check.py` | Vercel serverless entry points |
| `public/index.html`, `public/styles.css`, `public/js/` (gitignored, built) | the redesigned front end |
| `web/` | the front end's TypeScript source, tests, and toolchain (`npm run build` produces `public/js/`) |
| `design/2026-09-22-redesign/` | the approved design boards and reference images the front-end redesign was built from |
| `data/reference/` | committed, cited reference files (FDA enzyme table, ONC pair list, active-metabolite pairs, the interaction-checker blind-test fixture) |
| `scripts/dev_server.py`, `scripts/validate_interactions.py` | a local server for `public/` and `/api/*`, and the harness that scores the checker against the fixture; see `docs/interaction-validation.md` |
| `TEST_PACK.md`, `test_runs/`, `scripts/grade_test_pack.py`, `scripts/report_test_pack.py`, `scripts/diff_test_runs.py` | the black-box test pack, every committed run, and the grader, report, and diff scripts |
| `data/reference/interaction_knowledge.json` | the 90 class-level interaction rules with grades, mechanisms, actions, rulebook rows, and sources |
| `docs/interaction-validation.md`, `.json` | the harness's latest result and its raw sidecar |
| `docs/screenshots/` | first-screen, results, and edge-state screenshots at 375px and 1440px, light and dark |
| `data/gold/gold_sample_PLACEHOLDER.json` | the demonstration gold file |
| `tests/fixtures/` | committed real openFDA label and RxNorm fixtures, with fetch dates, documented in `tests/fixtures/FIXTURES.md` |
| `reports/` | the phase-by-phase build record; start at `reports/FINAL_REPORT.md` |
| `DATA_SOURCES.md` | every data source, its license, and how it is used |
| `.github/workflows/rebuild.yml` | the weekly rebuild-and-deploy workflow |
| `vercel.json`, `.vercelignore` | Vercel project and function-bundling configuration |
| `pyproject.toml` | package metadata; `pytest` is the only dependency |

## Rubric

### 4. Peer exchange [20 points]
Invite a peer classmate as a hypothetical user of your search engine.

Describe your planned document collection to them: What documents will be in the collection? Why do you think they are interesting? Also, describe your controlled vocabulary to them: What does each term mean? In what scenarios can they be useful?

Ask the user to come up with a scenario in which they would use your controlled vocabulary when searching or refining results. Ask them to explain their question in complete sentences, and take note of the term(s) they selected.

Answer the following questions:
* <u>What is the name and PID of your user?</u>
* <u>Who invited you as a user to use their search engines (if any)? What are their names and PIDs?</u>
* <u>What was your user's question in natural language?</u>
* <u>What terms did they select to represent that question?</u>
