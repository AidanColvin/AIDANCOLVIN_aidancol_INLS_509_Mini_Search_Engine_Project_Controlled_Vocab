# Test fixtures

Every file under `labels/` wraps one real openFDA drug label record, fetched from the openFDA Drug Label API by SPL set id on the date shown. Each file has the shape `{"fetched_on", "source_url", "fixture_name", "label"}`, where `label` is the unmodified API record.

| Fixture | set_id | effective_time | version | Brand name | Substance names | Fetched |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| adderall | f22635fe-821d-4cde-aa12-419f8b53db81 | 20240529 | 21 | Adderall | DEXTROAMPHETAMINE SACCHARATE; AMPHETAMINE ASPARTATE MONOHYDRATE; DEXTROAMPHETAMINE SULFATE; AMPHETAMINE SULFATE | 2026-09-21 |
| cyclobenzaprine | 5d536e88-62be-45bd-bd09-0efc53fe12b9 | 20260909 | 14 | CYCLOBENZAPRINE HYDROCHLORIDE | CYCLOBENZAPRINE HYDROCHLORIDE | 2026-09-21 |
| desvenlafaxine | ff837eb1-24c3-4c63-9b4b-c6b5935a9b47 | 20260821 | 7 | DESVENLAFAXINE | DESVENLAFAXINE SUCCINATE | 2026-09-21 |
| dextroamphetamine | 0ef920a9-c5b9-4d31-a478-ee18d22a3c5b | 20260909 | 105 | DEXTROAMPHETAMINE SULFATE | DEXTROAMPHETAMINE SULFATE | 2026-09-21 |
| entresto | 000dc81d-ab91-450c-8eae-8eb74e72296f | 20260706 | 25 | ENTRESTO | SACUBITRIL; VALSARTAN | 2026-09-21 |
| gabapentin | 4a975ebe-ae0a-446a-8a3d-2ca325e28f93 | 20260911 | 2 | gabapentin | GABAPENTIN | 2026-09-21 |
| olanzapine_zyprexa | b418946a-1ab4-4d89-a012-d94fc361a3c4 | 20260211 | 68 | Zyprexa, ZYPREXA Intramuscular, ZYPREXA Zydis | OLANZAPINE | 2026-09-21 |
| oxycontin | bfdfe235-d717-4855-a3c8-a13d26dadede | 20260624 | 44 | OxyContin | OXYCODONE HYDROCHLORIDE | 2026-09-21 |
| pregabalin_lyrica | d4734e7d-5079-455e-8ff5-8f4539c998a9 | 20250415 | 18 | Lyrica | PREGABALIN | 2026-09-21 |
| trazodone | fa7afa93-b98c-4dc7-bbb8-ab6a058427b9 | 20260908 | 3 | Trazodone Hydrochloride | TRAZODONE HYDROCHLORIDE | 2026-09-21 |
| venlafaxine | c41d847b-88ba-49a5-9d73-269ac4caa4ed | 20260903 | 4 | Venlafaxine Hydrochloride | VENLAFAXINE HYDROCHLORIDE | 2026-09-21 |
| zolpidem_ambien | c36cadf4-65a4-4466-b409-c82020b42452 | 20250415 | 26 | Ambien | ZOLPIDEM TARTRATE | 2026-09-21 |

| losartan | a397502e-abe7-49cf-97c7-d53a616947eb | 20260903 | 4 | Losartan potassium | LOSARTAN POTASSIUM | 2026-09-21 |

| adderall_current_collection_winner | ac102599-3a5b-4154-899e-6ff262be7ff7 | 20260804 | 10 | DEXTROAMPHETAMINE SACCHARATE, AMPHETAMINE ASPARTATE, DEXTROAMPHETAMINE SULFATE AND AMPHETAMINE SULFATE | DEXTROAMPHETAMINE SACCHARATE; AMPHETAMINE ASPARTATE MONOHYDRATE; DEXTROAMPHETAMINE SULFATE; AMPHETAMINE SULFATE | 2026-09-21 |

Files under `rxnorm/` wrap one real RxNav REST response each, with the same `fetched_on` and `source_url` fields, so the name matcher and ingredient rollup tests run offline.

Fixture selection: brand labels (Zyprexa, Adderall, Ambien, Lyrica, OxyContin, Entresto) were chosen where the acceptance test types a brand name; the others are the newest human prescription label for that substance on the fetch date. Flexeril has no label in openFDA (the API returned no results on 2026-09-21), so the Flexril test relies on the RxNorm fixtures. Losartan is not one of the Section 9.6 interaction-checker drugs; it was added for Appendix C Scenario 2 (keyword "hypertension" plus T01 AND T02), since none of the checker fixtures both treat hypertension and carry a boxed warning.

`adderall_current_collection_winner` is the label that actually survives the Part 1 newest-per-ingredient-set filter for the four amphetamine salts as of 2026-09-21: an ANDA generic combination product, not either branded Adderall label. It carries no `controlled_substance` field, unlike the brand labels. The Section 3.6 acceptance test uses it, not the plain `adderall` fixture, for the checker's DEA-schedule and other label-content expectations, and reports the difference from the build prompt's assumption in `reports/BLOCKERS.md`.
