"""Tests for HTML table parsing."""

from __future__ import annotations

from typing import Any

from rx_label_search.text.html_tables import parse_tables, strip_tags


def test_parse_tables_reads_rows_and_cells() -> None:
    """
    Takes no arguments.
    Parses a small table with a header row and two body rows.
    Gives nothing, or fails if rows or cells are wrong.
    """
    html = "<table><tr><th>Reaction</th><th>Drug (%)</th></tr><tr><td>Nausea</td><td>23</td></tr><tr><td>Rash</td><td>&lt;1</td></tr></table>"
    assert parse_tables(html) == ((("Reaction", "Drug (%)"), ("Nausea", "23"), ("Rash", "<1")),)


def test_parse_tables_empty_and_strip_tags() -> None:
    """
    Takes no arguments.
    Parses a fragment with no table and strips tags from a fragment.
    Gives nothing, or fails if either result is wrong.
    """
    assert parse_tables("<p>no table</p>") == ()
    assert strip_tags("<p>a <b>b</b>  c</p>") == "a b c"
    assert strip_tags("") == ""


def test_oxycontin_adverse_table_parses(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Parses the first adverse reactions table of the OxyContin fixture.
    Gives nothing, or fails if the header row does not name the drug column.
    """
    tables = parse_tables(fixture_labels["oxycontin"]["adverse_reactions_table"][0])
    assert tables
    header = tables[0][0]
    assert any("OXYCONTIN" in cell for cell in header)
