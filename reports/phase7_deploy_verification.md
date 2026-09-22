# Phase 7 deploy verification

The one remaining gap from `reports/phase7_serve.md` — a live deployment — is closed. `rx-label-search` is live, public, and verified end to end against the production data it built for itself.

## Live URL

https://rx-label-search-hwgoaykin-aidancolvins-projects.vercel.app

This is the URL Vercel assigned this specific production deployment. Every future deploy through the workflow will print a new URL of the same shape in its log; there is no custom domain attached yet.

## What was set up

* **Vercel project:** `rx-label-search` (id `prj_LjFAfFxSQ8gPFnsC7iMPRC0SSmuY`) under team `aidancolvins-projects` (id `team_XipeCSRlfPloqYTXYgB7onnj`), created bare through the Vercel API, never linked to the GitHub repo through Vercel's own git integration. Deploys can only happen through `.github/workflows/rebuild.yml`.
* **GitHub repo secrets:** `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, all set and confirmed present with `gh secret list`. Their values are never written to any file, report, or log in this repo.
* **Workflow trigger:** `.github/workflows/rebuild.yml` already had `workflow_dispatch`; no change was needed there.

## Bugs found and fixed to get a green deploy

Four attempts, three real bugs, each found from an actual failing GitHub Actions run and fixed by reading its log, not guessed at:

1. **`uv` missing on the runner.** `vercel build` run locally (as opposed to on Vercel's own build machines) shells out to `uv` for the Python runtime and failed with `Error: uv is required but was not found in PATH`. Fixed by adding a `pip install uv` step before the deploy step.
2. **New project needs explicit settings.** The very first deploy to a brand-new project failed with `The projectSettings object is required for new projects, but is missing in the deployment payload`. Fixed by setting the project's `framework` to `null` (the "Other" preset, matching the static-page-plus-Python-functions layout) through the Vercel API, a one-time setting that persists for every later deploy.
3. **A folder-name typo caused a real deploy failure.** `vercel.json`'s function `excludeFiles` said `part1_document_collection/**`; the actual folder is `document_collection_part_1/`. Because the name never matched, the Python build's file tracer treated `document_collection_part_1/*.md` and every file under `reports/` as files the function needed, then failed with `Error: ENOENT: no such file or directory, readlink '.../document_collection_part_1/document_collection_part_1_v1_submitted.md'` when it tried to read them, because `.vercelignore` had already stripped them from the uploaded source. Fixed by correcting the folder name and adding `reports/**` to `excludeFiles` so both files agree on what the function bundle excludes.
4. **SSO protection blocked public access.** Once the deploy itself succeeded, the live URL returned `302` to `vercel.com/sso-api`: the team's default project protection required a Vercel login to view any deployment. This directly conflicts with the build prompt's "free, open-access" requirement, so it was disabled through the Vercel API (`ssoProtection: null`). This is a project setting, not something the GitHub Actions workflow can affect, and needed to be set once by hand here.

All four fixes are either committed to the repo (1 and 3, both need no further action) or are one-time Vercel project settings (2 and 4, already applied and will not need to be redone by future deploys).

## Verification against known inputs

### Homepage

`GET /` returns `200`, `access-control-allow-origin: *`, and the page HTML contains the search box (`#search-box`), the PDLA term filter container (`#term-filters`), the medication-list box (`#med-box`), the results areas (`#search-results`, `#check-results`), and the notice line (`#notice-line`) — every element Section 3.5 and the build prompt's front-end requirement ask for.

### `api/search`

`GET /api/search?terms_only=1` returns all 17 PDLA terms and today's build date.

`GET /api/search?q=muscle+spasm&term=T14&term=T15&operator=AND&limit=3` returns 3 ranked hits, cyclobenzaprine first with score 7.2 and tags including T14 and T15 — the same result Appendix C Scenario 3 and `reports/phase5_search.md` already verified locally against the fixtures.

### `api/check`

`POST /api/check` with the exact Section 3.1 test input (`"10 mg Zyprexa X 1 daily , 20 mg adderall X 3 daily , 10 mg ambien X daily , trazdone 50 mg X 1 daily , desvenlafaxine 50 mg X 1 daily , Flexril 10 mg X 3 times daily , Lyrica 100 mg X 3 daily"`, `use_rxnorm: true`) against the live production collection returns:

* All 7 entries resolved, 0 unresolved. Daily totals: 10, 60, 10, 50, 50, 30, 300 mg/day, matching Section 3.6.
* "Flexril" resolves through a live RxNorm call to Flexeril, then to cyclobenzaprine, then to CYCLOBENZAPRINE HYDROCHLORIDE — the first confirmation that the RxNorm fallback works from inside the deployed function, not only against saved test fixtures.
* Two group alerts: Serotonin Syndrome Risk and CNS Depression Risk, each shared by 4 drugs on the live full collection (the fixture-scoped acceptance test in `reports/phase6_check.md` found 4 members each on its smaller fixture set too; the live collection can add more, which is expected and correct, not a bug).
* The notice text is the exact required wording, with today's build date filled in.

## Final workflow status

Run `35679459340` (triggered by the fix-3 push) completed with every step green, including `Deploy to Vercel`, in 29m56s. `gh run list --workflow=rebuild.yml` shows this as the latest run and it is a success.

## What I should check by hand

* No custom domain is attached; the site is reachable only at the `*.vercel.app` URL above. Attaching `rx-label-search.<yourdomain>` or a Vercel-provided alias is optional and up to you.
* The `ssoProtection` and `framework` project settings were set once, by hand, through the API in this session, since neither is something version-controlled in the repo. If the Vercel project is ever deleted and recreated, both need to be set again before the site is genuinely public.
