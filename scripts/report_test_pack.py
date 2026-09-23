"""Writes the per-list result files, RESULTS_FROM_WEBSITE.md, RULEBOOK_COVERAGE.md, and the metric tables of EVALUATION_REPORT.md for one test-pack run."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade_test_pack as grader  # noqa: E402


def fence(text: str) -> str:
    """
    Takes page text.
    Wraps it in a fenced block that cannot be closed early by the text itself.
    Gives the fenced block.
    """
    return "````text\n" + text.rstrip() + "\n````"


def list_result_markdown(capture: dict, statuses: dict[str, int], version: str) -> str:
    """
    Takes one list's browser capture, the HTTP status by URL, and the site version string.
    Lays out the capture in the order the pack asks for.
    Gives the Markdown for results/<ID>.md.
    """
    list_id = capture["id"]
    out = [f"# {list_id} — Results from current website", f"Site version: {version}", f"Input submitted: {capture['input']}", ""]
    out += ["## Visible text of the results region (verbatim)", "", fence(capture.get("text") or "(nothing captured)"), ""]
    out += ["## Severity grades, categories, and grouping statements", ""]
    strip = ", ".join(f"{cell['letter']} {cell['name']}: {cell['count']}" for cell in capture.get("severity") or [])
    out += [f"- Severity strip: {strip or 'not shown'}", f"- Caption: {capture.get('caption') or 'none'}", f"- Status line: {capture.get('statusText') or 'none'}"]
    alerts = capture.get("alerts") or []
    if not alerts:
        out.append("- Alerts: none shown.")
    for alert in alerts:
        out.append(f"- Grade {alert.get('grade')} ({(alert.get('grade_text') or '').split(' — ')[0]}) — {alert.get('drugs')} — {alert.get('category')}")
    out += ["", "## Hyperlinks in the results", "", "| Link text | href | HTTP |", "|---|---|---|"]
    for link in capture.get("links") or []:
        out.append(f"| {link['text'] or '(no text)'} | {link['href']} | {statuses.get(link['href'], 'not checked')} |")
    out += ["", "## Daily totals the site computed", ""]
    meds = capture.get("meds") or []
    for med in meds:
        out.append(f"- {med.get('brand')}: {med.get('dose') or 'no dose or total shown'}")
    if not meds:
        out.append("- No medication cards shown.")
    entries = capture["input"].split(", ")
    dup_alerts = [alert for alert in alerts if "duplication" in (alert.get("classes") or "")]
    out += ["", "## Merging of duplicates, brand/generic pairs, IR/ER forms, and combination products", ""]
    out.append(f"- Entries submitted: {len(entries)}. Medication cards shown: {len(meds)}. Duplication alerts: {len(dup_alerts)}.")
    for alert in dup_alerts:
        out.append(f"  - {alert.get('drugs')}: {alert.get('category')}")
    out += ["", "## Files", "", f"- Screenshot: screenshots/{list_id}.png", f"- DOM of the results region: dom/{list_id}.html", ""]
    out += ["## Console errors and 4xx/5xx responses", ""]
    problems = (capture.get("consoleErrors") or []) + (capture.get("badResponses") or [])
    out += [f"- {problem}" for problem in problems] or ["- None."]
    out += ["", "## Timing and input", ""]
    out.append(f"- Input focused on load without a click: {'yes' if capture.get('focusedOnLoad') else 'no'} ({capture.get('focus')})")
    out.append(f"- Seconds to interactive: {capture.get('secondsToInteractive')}")
    out.append(f"- Seconds from Enter to final results: {capture.get('secondsToResults')}")
    out.append(f"- Attempts: {capture.get('attempts')}")
    out += [f"- Defect: {defect}" for defect in capture.get("defects") or []]
    return "\n".join(out) + "\n"


def write_results(pack: Path, run_dir: Path) -> None:
    """
    Takes TEST_PACK.md and the run folder.
    Writes results/<ID>.md for every list and assembles RESULTS_FROM_WEBSITE.md, then checks it against Section 5.
    Gives nothing; raises AssertionError when the combined file does not match the pack.
    """
    lists, _ = grader.load_pack(pack)
    statuses: dict[str, int] = json.loads((run_dir / "link_status.json").read_text())
    (run_dir / "results").mkdir(exist_ok=True)
    combined = [f"# Results from the website", "", f"Run folder: {run_dir.name}. One section per list, L01–L41.", ""]
    for list_id, line in lists.items():
        capture = json.loads((run_dir / "raw" / f"{list_id}.json").read_text())
        version = capture.get("siteVersion", "unknown")
        (run_dir / "results" / f"{list_id}.md").write_text(list_result_markdown(capture, statuses, version))
        combined += [f"## {list_id} — Results from current website", "", f"Input submitted: {capture['input']}", "", fence(capture.get("text") or ""), ""]
    text = "\n".join(combined)
    (run_dir / "RESULTS_FROM_WEBSITE.md").write_text(text)
    headers = re.findall(r"^## ([LG]\d\d) — Results from current website$", text, re.M)
    assert headers == list(lists), f"section IDs wrong: {headers}"
    inputs = re.findall(r"^Input submitted: (.*)$", text, re.M)
    assert inputs == list(lists.values()), "an input line differs from Section 5"


def write_coverage(evaluation: dict, run_dir: Path) -> None:
    """
    Takes the evaluation and the run folder.
    Tabulates, for each rulebook row, the lists it applies to and how often the site flagged the drugs and named the syndrome.
    Gives nothing; writes RULEBOOK_COVERAGE.md.
    """
    out = ["# Rulebook coverage", "", "Rows are Section 3 of TEST_PACK.md. A row applies to a list when the list holds drugs from each side of the row (different entries, different drugs).",
           "\"Flagged\" means the site showed an alert holding at least two of the row's drugs. \"Named\" means that alert's text also names the row's syndrome.",
           "In the list column, a bare ID means named, ~ means flagged but syndrome not named, ✗ means not flagged.", "",
           "| Row | Combination | Lists it applies to | Flagged | Named | Lists |", "|---|---|---|---|---|---|"]
    for number, cell in evaluation["summary"]["coverage"].items():
        out.append(f"| {number} | {cell['name']} | {cell['applies']} | {cell['flagged']} | {cell['named']} | {' '.join(cell['lists']) or '—'} |")
    uncovered = [str(number) for number, cell in evaluation["summary"]["coverage"].items() if cell["applies"] == 0]
    out += ["", f"Rows no list in L01–L41 exercises: {', '.join(uncovered)}.", ""]
    (run_dir / "RULEBOOK_COVERAGE.md").write_text("\n".join(out))


def pct(part: int, whole: int) -> str:
    """
    Takes a count and a total.
    Formats the share as a percentage.
    Gives "n/a" when the total is zero.
    """
    return "n/a" if not whole else f"{100 * part / whole:.1f}%"


def metrics_markdown(evaluation: dict) -> str:
    """
    Takes the evaluation.
    Lays out the summary table and the per-list scorecard.
    Gives the Markdown for sections 1 and 2 of EVALUATION_REPORT.md.
    """
    summary = evaluation["summary"]
    recall = summary["recall"]
    precision = summary["precision"]
    out = ["## 1. Summary", "", "| Metric | Value |", "|---|---|"]
    for grade, label in (("D", "contraindicated"), ("C", "major"), ("B", "moderate"), ("A", "minor")):
        cell = recall[grade]
        out.append(f"| Recall, grade {grade} ({label}) | {cell['hit']}/{cell['expected']} hits = {pct(cell['hit'], cell['expected'])} (plus {cell['partial']} partial) |")
    shown = sum(cell["shown"] for cell in precision.values())
    supported = sum(cell["supported"] for cell in precision.values())
    out.append(f"| Precision, overall | {supported}/{shown} flags backed by the key = {pct(supported, shown)} |")
    for grade in "DCBA":
        cell = precision[grade]
        out.append(f"| Precision, grade {grade} | {cell['supported']}/{cell['shown']} = {pct(cell['supported'], cell['shown'])} |")
    out += [
        f"| False positives on controls L11, L29 (B or above) | {summary['false_positives_controls']} |",
        f"| False positives, all should_not_flag rules | {summary['false_positives_total']} |",
        f"| Totals correct | {summary['totals_correct']}/{summary['totals_expected']} |",
        f"| Duplicate, unit, weekly, and combination cases resolved | {summary['duplicate_resolved']}/{summary['duplicate_cases']} |",
        f"| Grouping statements present | {summary['grouping_present']}/{summary['grouping_expected']} |",
        f"| Flags with a working primary-source link | {summary['flags_with_working_primary_link']}/{summary['flags_shown']} |",
        f"| C or D flags with a working drug-specific link | {summary['cd_flags_with_working_specific_link']}/{summary['cd_flags']} |",
        f"| Entries the site could not resolve | {summary['entries_not_found']}/{summary['entries_total']} |",
        f"| Input focused on load | {summary['focused_on_load']}/{summary['lists_scored']} lists |",
        f"| Seconds from Enter to results, median / worst | {summary['median_seconds']} / {summary['worst_seconds']} |",
    ]
    rows_applying = sum(cell["applies"] for cell in summary["coverage"].values())
    rows_named = sum(cell["named"] for cell in summary["coverage"].values())
    out.append(f"| Rulebook rows caught and named (row-list pairs) | {rows_named}/{rows_applying} |")
    out += ["", "## 2. Per-list scorecard", "", "| List | Expected | Hit | Partial | Miss | False pos. | Totals correct | Grouping present | Flags with working link | Not resolved |", "|---|---|---|---|---|---|---|---|---|---|"]
    for list_id, scores in evaluation["lists"].items():
        items = scores["items"]
        count = lambda status: sum(item["status"] == status for item in items)  # noqa: E731
        totals = scores["totals"]
        grouping = scores["grouping"]
        links = scores["links"]
        out.append(
            f"| {list_id} | {len(items)} | {count('HIT')} | {count('PARTIAL')} | {count('MISS')} | {len(scores['false_positives'])} | "
            f"{sum(row['correct'] for row in totals)}/{len(totals)} | {sum(row['present'] for row in grouping)}/{len(grouping)} | "
            f"{sum(row['primary_working'] for row in links)}/{len(links)} | {len(scores['not_found'])} |"
        )
    return "\n".join(out) + "\n"


def misses_markdown(evaluation: dict) -> str:
    """
    Takes the evaluation.
    Lists every MISS and PARTIAL with the key's expectation, what the site showed, the rulebook rows, and an automatic black-box hypothesis.
    Gives the Markdown for section 3 of EVALUATION_REPORT.md.
    """
    out = ["## 3. Every MISS and PARTIAL", "", "| List | Drugs | Expected category, grade | Status | Site showed | Rulebook row | Black-box hypothesis |", "|---|---|---|---|---|---|---|"]
    for list_id, scores in evaluation["lists"].items():
        for item in scores["items"]:
            if item["status"] == "HIT":
                continue
            drugs = {i for drug in item["drugs"] for i in grader.ingredients_of(drug)}
            rows = [str(entry["row"]) for entry in scores["rulebook"] if len(drugs & set(entry["drugs"])) >= min(2, len(drugs))]
            unresolved = [entry for entry in scores["not_found"] if drugs & set(grader.parse_entry(entry).ingredients)]
            if unresolved:
                hypothesis = f"parser: {len(unresolved)} of these entries came back \"not found\" (the Brand (generic) dose = total line was not split into name and dose)"
            elif item["site_grade"]:
                hypothesis = "flagged, but the grade or category does not match: " + item["reason"]
            elif item["category"] in grader.DUPLICATE_CATEGORIES | {"dose ceiling", "dosing frequency", "combination parsing"}:
                hypothesis = "no dose arithmetic across entries (no ceiling table, no per-molecule total)"
            else:
                hypothesis = "names resolved but no alert: no class-level rule or missing pair in the label data"
            site_showed = f"{item['site_grade']} — {item['site_category']}" if item["site_grade"] else item["reason"]
            out.append(f"| {list_id} | {', '.join(item['drugs'])} | {item['category']}, {item['pack_grade']} ({item['severity']}) | {item['status']} | {site_showed} | {', '.join(rows) or '—'} | {hypothesis} |")
    return "\n".join(out) + "\n"


def false_positive_markdown(evaluation: dict) -> str:
    """
    Takes the evaluation.
    Lists every false positive found by the rules.
    Gives the Markdown table, or a line saying there were none.
    """
    rows = [(list_id, fp) for list_id, scores in evaluation["lists"].items() for fp in scores["false_positives"]]
    if not rows:
        return "No false positives: no flag at B or above on L11 or L29, and none on any should_not_flag entry.\n"
    out = ["| List | Rule | Site flag | Site grade |", "|---|---|---|---|"]
    out += [f"| {list_id} | {fp['rule']} | {fp['drugs']} — {fp['category']} | {fp['site_grade']} |" for list_id, fp in rows]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    pack_path, run_path = Path(sys.argv[1]), Path(sys.argv[2])
    evaluation_data = grader.grade_run(pack_path, run_path)
    write_results(pack_path, run_path)
    write_coverage(evaluation_data, run_path)
    (run_path / "metrics.md").write_text(metrics_markdown(evaluation_data) + "\n" + misses_markdown(evaluation_data) + "\n## False positives\n\n" + false_positive_markdown(evaluation_data))
    print((run_path / "metrics.md").read_text()[:4000])
