# Phase 4: evaluate tagging

## What was built

The gold-set template builder and cell editor (`evaluate/gold.py`), per-term precision/recall/F1 with confusion counts (`evaluate/tag_metrics.py`), the markdown report formatter (`evaluate/report.py`), the jobs that tie them to the build directory and gold file (`evaluate/run.py`), and three CLI commands: `gold-template`, `gold-label`, and `evaluate-tags`.

## Commands run and results

```
PYTHONPATH=src .venv/bin/python -m rx_label_search gold-template --sample-size 8
PYTHONPATH=src .venv/bin/python -m rx_label_search evaluate-tags
.venv/bin/python -m pytest -q
```

`data/gold/gold_sample_PLACEHOLDER.json` was written from the first 8 tagged set ids, every cell `"gold": false` with the rationale `"PLACEHOLDER: replace with your own rationale before this label counts as real."`. `evaluate-tags` ran against it and reported 0 filled cells and 0.000 for every term's precision, recall, and F1, with the notice that every score is 0.0 until real labels replace the placeholders.

Tests: 259 passed, 0 failed, 0 skipped.

## How to fill in the real gold set

1. Run `gold-template` again with a larger `--sample-size` once you decide how many labels to hand-label, or point `--output` at a new file to keep the placeholder file untouched.
2. For each label and term you want to score, run:
   ```
   PYTHONPATH=src .venv/bin/python -m rx_label_search gold-label --gold-file data/gold/my_real_gold.json --set-id <SET_ID> --term T06 --value true --rationale "the label's dosage_and_administration section ties creatinine clearance to a lower dose"
   ```
   Repeat for as many (label, term) pairs as you want to score. A cell only counts once its rationale text differs from the placeholder string above.
3. Run `evaluate-tags --gold-file data/gold/my_real_gold.json --report reports/my_real_evaluation.md` to get per-term precision, recall, F1, and confusion counts against the tagger's actual output on the built collection.
4. The report only scores terms and labels you have hand-labeled; a term with no gold cells reports 0/0/0/0 and 0.000 for every score, which is not the same as the tagger being wrong.

## Label-driven differences

None; this phase evaluates against a placeholder file with no real values.

## What I should check by hand

Nothing yet; the harness is unverified against real judgments until you fill in `gold-label` entries.

## Open questions

None new in this phase.
