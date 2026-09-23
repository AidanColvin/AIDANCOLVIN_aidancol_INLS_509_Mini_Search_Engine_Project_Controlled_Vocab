"""Writes DIFF_VS_PREVIOUS_RUN.md: every metric and every list whose result changed between two graded test-pack runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

STATUS_RANK: dict[str, int] = {"MISS": 0, "PARTIAL": 1, "HIT": 2}


def load(run_dir: Path) -> dict:
    """
    Takes a run folder.
    Reads its evaluation.json.
    Gives the parsed evaluation.
    """
    return json.loads((run_dir / "evaluation.json").read_text())


def metric_rows(before: dict, after: dict) -> list[str]:
    """
    Takes two evaluations.
    Lines up the headline metrics side by side.
    Gives Markdown table rows.
    """
    b, a = before["summary"], after["summary"]
    rows: list[str] = []
    for grade in "DCBA":
        rb, ra = b["recall"][grade], a["recall"][grade]
        rows.append(f"| Recall {grade} (hits/expected) | {rb['hit']}/{rb['expected']} | {ra['hit']}/{ra['expected']} |")
    for key, label in (
        ("false_positives_controls", "False positives on L11, L29"),
        ("false_positives_total", "False positives, all rules"),
        ("totals_correct", "Totals correct"),
        ("duplicate_resolved", "Duplicate/unit/weekly/combination cases resolved"),
        ("grouping_present", "Grouping statements present"),
        ("cd_flags_with_working_specific_link", "C/D flags with a working drug-specific link"),
        ("cd_flags", "C/D flags shown"),
        ("flags_shown", "Flags shown"),
        ("entries_not_found", "Entries not resolved"),
        ("focused_on_load", "Input focused on load (lists)"),
        ("median_seconds", "Median seconds to results"),
        ("worst_seconds", "Worst seconds to results"),
    ):
        rows.append(f"| {label} | {b.get(key)} | {a.get(key)} |")
    return rows


def list_changes(before: dict, after: dict) -> tuple[list[str], list[str]]:
    """
    Takes two evaluations.
    Compares every expected item's status and every list's false positives.
    Gives (improvements, regressions) as Markdown table rows.
    """
    better: list[str] = []
    worse: list[str] = []
    for list_id, scores in after["lists"].items():
        old = before["lists"].get(list_id, {"items": [], "false_positives": []})
        for new_item, old_item in zip(scores["items"], old["items"]):
            delta = STATUS_RANK[new_item["status"]] - STATUS_RANK[old_item["status"]]
            if delta == 0:
                continue
            row = f"| {list_id} | {', '.join(new_item['drugs'])} ({new_item['category']}) | {old_item['status']} | {new_item['status']} | {new_item.get('site_grade') or '—'} |"
            (better if delta > 0 else worse).append(row)
        if len(scores["false_positives"]) > len(old["false_positives"]):
            worse.append(f"| {list_id} | new false positive: {scores['false_positives'][-1]['drugs']} | — | FP | {scores['false_positives'][-1]['site_grade']} |")
        if len(scores["false_positives"]) < len(old["false_positives"]):
            better.append(f"| {list_id} | false positive removed | FP | — | — |")
    return better, worse


def write_diff(before_dir: Path, after_dir: Path) -> str:
    """
    Takes the previous and the new run folders.
    Builds the comparison: metrics, then every improved and every regressed item, regressions flagged as P0.
    Gives the Markdown and writes it to DIFF_VS_PREVIOUS_RUN.md in the new run folder.
    """
    before, after = load(before_dir), load(after_dir)
    better, worse = list_changes(before, after)
    header = "| List | Item | Before | After | Site grade now |\n|---|---|---|---|---|"
    out = [
        f"# Diff: {before_dir.name} → {after_dir.name}", "",
        "## Metrics", "", f"| Metric | {before_dir.name} | {after_dir.name} |", "|---|---|---|", *metric_rows(before, after), "",
        f"## Regressions (P0): {len(worse)}", "", *( [header, *worse] if worse else ["None."] ), "",
        f"## Improvements: {len(better)}", "", header, *better, "",
    ]
    text = "\n".join(out)
    (after_dir / "DIFF_VS_PREVIOUS_RUN.md").write_text(text)
    return text


if __name__ == "__main__":
    print(write_diff(Path(sys.argv[1]), Path(sys.argv[2]))[:3000])
