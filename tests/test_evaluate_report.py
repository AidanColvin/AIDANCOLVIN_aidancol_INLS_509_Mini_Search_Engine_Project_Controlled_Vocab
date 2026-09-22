"""Tests for the tag-evaluation report formatting."""

from __future__ import annotations

from rx_label_search.evaluate.report import format_metrics_row, format_tag_evaluation_report
from rx_label_search.evaluate.tag_metrics import TermMetrics


def test_format_metrics_row_has_every_number() -> None:
    """
    Takes no arguments.
    Formats one term's metrics.
    Gives nothing, or fails if the term id or any count is missing from the row.
    """
    row = format_metrics_row(TermMetrics("T06", 8, 2, 2, 10))
    assert "T06" in row
    assert "8" in row
    assert "0.800" in row


def test_report_notes_when_no_gold_cells_are_filled() -> None:
    """
    Takes no arguments.
    Formats the report with zero filled gold cells.
    Gives nothing, or fails if the placeholder notice is missing.
    """
    report = format_tag_evaluation_report((TermMetrics("T01", 0, 0, 0, 0),), 0)
    assert "No gold cells are filled in yet" in report


def test_report_omits_notice_when_cells_are_filled() -> None:
    """
    Takes no arguments.
    Formats the report with filled gold cells.
    Gives nothing, or fails if the placeholder notice appears anyway.
    """
    report = format_tag_evaluation_report((TermMetrics("T01", 1, 0, 0, 0),), 5)
    assert "No gold cells are filled in yet" not in report
