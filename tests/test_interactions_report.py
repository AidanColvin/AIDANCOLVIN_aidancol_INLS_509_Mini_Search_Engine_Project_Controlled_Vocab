"""Tests for the checker report formatting."""

from __future__ import annotations

from rx_label_search.interactions.report import (
    build_check_report,
    build_notice,
    medication_table_row,
    not_listed_or,
)
from rx_label_search.normalize.med_line_parser import parse_entry


def test_build_notice_matches_section_3_5_wording() -> None:
    """
    Takes no arguments.
    Fills the notice template with a build date.
    Gives nothing, or fails if the wording differs from the required text.
    """
    notice = build_notice("2026-09-21")
    assert notice.startswith('Results reflect FDA label text as of 2026-09-21.')
    assert "does not replace clinical judgment" in notice


def test_not_listed_or() -> None:
    """
    Takes no arguments.
    Joins a non-empty list and formats an empty one.
    Gives nothing, or fails if either result is wrong.
    """
    assert not_listed_or(["A", "B"]) == "A, B"
    assert not_listed_or([]) == "Not listed on label."


def test_medication_table_row_for_unresolved_entry() -> None:
    """
    Takes no arguments.
    Builds a table row for an entry with no resolved drug.
    Gives nothing, or fails if the row does not show empty resolution fields.
    """
    entry = parse_entry("qwxzvbn 10 mg")
    row = medication_table_row(entry, None)
    assert row["matched_name"] is None
    assert row["pdla_tags"] == []
    assert row["fda_class"] == "Not listed on label."


def test_build_check_report_assembles_every_section() -> None:
    """
    Takes no arguments.
    Builds a report from a checker result with no entries or alerts.
    Gives nothing, or fails if any section is missing.
    """
    result = {"entries": (), "resolved_drugs": [], "unresolved_entries": [], "alerts": ()}
    report = build_check_report(result, "2026-09-21")
    assert report["build_date"] == "2026-09-21"
    assert report["medication_table"] == []
    assert report["alerts"] == []
    assert report["no_warning_text"] == "No warning found in the labels checked."
    assert "2026-09-21" in report["notice"]
