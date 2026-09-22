"""Pure formatting of the tag-evaluation report."""

from __future__ import annotations

from rx_label_search.evaluate.tag_metrics import TermMetrics

_HEADER = "| Term | TP | FP | FN | TN | Precision | Recall | F1 |\n| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"


def format_metrics_row(metrics: TermMetrics) -> str:
    """
    Takes one term's metrics.
    Formats it as one markdown table row.
    Gives the row string.
    """
    return (
        f"| {metrics.term_id} | {metrics.true_positive} | {metrics.false_positive} | {metrics.false_negative} | "
        f"{metrics.true_negative} | {metrics.precision:.3f} | {metrics.recall:.3f} | {metrics.f1:.3f} |"
    )


def format_tag_evaluation_report(all_metrics: tuple[TermMetrics, ...], gold_cell_count: int) -> str:
    """
    Takes every term's metrics and the number of filled gold cells the report covers.
    Builds the full markdown report.
    Gives the report text, noting when no gold cells were filled in.
    """
    lines = [
        "# Tag evaluation",
        "",
        f"Filled gold cells: {gold_cell_count}.",
        "",
        _HEADER,
        *(format_metrics_row(metrics) for metrics in all_metrics),
    ]
    if gold_cell_count == 0:
        lines.append("")
        lines.append("No gold cells are filled in yet. Every score above is 0.0 until real labels replace the placeholders.")
    return "\n".join(lines)
