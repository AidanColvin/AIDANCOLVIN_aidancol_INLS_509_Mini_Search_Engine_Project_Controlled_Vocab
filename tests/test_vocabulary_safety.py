"""Tests for T01 and T04 against fixtures and constructed edge cases."""

from __future__ import annotations

from typing import Any

from rx_label_search.records import Label
from rx_label_search.text.fields import label_from_record
from rx_label_search.vocabulary.safety import (
    cell_percentage,
    drug_group_columns,
    tag_t01_boxed_warning,
    tag_t04_high_frequency_adverse_effect,
    table_high_frequency_reaction,
)


def test_t01_assigns_on_oxycontin_and_omits_on_gabapentin(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks the boxed warning rule on a label with one and a label without one.
    Gives nothing, or fails if either result is wrong.
    """
    oxycontin = label_from_record(fixture_labels["oxycontin"])
    gabapentin = label_from_record(fixture_labels["gabapentin"])
    assert tag_t01_boxed_warning(oxycontin) is not None
    assert tag_t01_boxed_warning(gabapentin) is None


def test_t01_empty_label() -> None:
    """
    Takes no arguments.
    Checks the boxed warning rule on a label with no fields.
    Gives nothing, or fails if evidence is returned.
    """
    assert tag_t01_boxed_warning(Label("i", "s", "1", "20250101", {}, {})) is None


def test_drug_group_columns_skips_placebo_and_short_header() -> None:
    """
    Takes no arguments.
    Reads drug-group columns from a normal header and a one-column header.
    Gives nothing, or fails if placebo is included or the short header is not empty.
    """
    assert drug_group_columns(("Reaction", "Drug (n=10)", "Placebo (n=5)")) == (1,)
    assert drug_group_columns(("Reaction",)) == ()


def test_cell_percentage_reads_parens_and_percent_sign() -> None:
    """
    Takes no arguments.
    Reads a percentage from a bare parenthesized number, a count-then-percent cell, and plain text.
    Gives nothing, or fails if any read is wrong or a non-numeric cell is not None.
    """
    assert cell_percentage("(23)") == 23.0
    assert cell_percentage("30 (21)") == 21.0
    assert cell_percentage("23%") == 23.0
    assert cell_percentage("N/A") is None


def test_table_high_frequency_reaction_on_oxycontin(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Reads the OxyContin adverse reaction table for a reaction at or above ten percent.
    Gives nothing, or fails if none is found or a placebo-only reaction is returned.
    """
    html = fixture_labels["oxycontin"]["adverse_reactions_table"][0]
    found = table_high_frequency_reaction(html, 10.0)
    assert found is not None
    assert found[0] == "Constipation"


def test_table_high_frequency_reaction_below_threshold_and_no_table() -> None:
    """
    Takes no arguments.
    Reads a table whose only drug-group rate is below the threshold and an empty fragment.
    Gives nothing, or fails if either case returns a match.
    """
    html = "<table><tr><th>Reaction</th><th>Drug (n=10)</th><th>Placebo (n=10)</th></tr><tr><td>Rash</td><td>(5)</td><td>(4)</td></tr></table>"
    assert table_high_frequency_reaction(html, 10.0) is None
    assert table_high_frequency_reaction("<p>none</p>", 10.0) is None


def test_t04_assigns_on_oxycontin_via_table(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Runs the full T04 rule on the OxyContin fixture.
    Gives nothing, or fails if no evidence is returned or the field is wrong.
    """
    evidence = tag_t04_high_frequency_adverse_effect(label_from_record(fixture_labels["oxycontin"]))
    assert evidence is not None
    assert evidence.field_name == "adverse_reactions_table"


def test_t04_assigns_via_prose_when_no_qualifying_table() -> None:
    """
    Takes no arguments.
    Builds a label whose only adverse_reactions field is prose stating a qualifying rate.
    Gives nothing, or fails if no evidence is returned or the field is wrong.
    """
    label = Label("i", "s", "1", "20250101", {"adverse_reactions": ("Nausea occurred in 15% of patients compared with 3% for placebo.",)}, {})
    evidence = tag_t04_high_frequency_adverse_effect(label)
    assert evidence is not None
    assert evidence.field_name == "adverse_reactions"


def test_t04_omits_when_nothing_reaches_threshold() -> None:
    """
    Takes no arguments.
    Builds a label whose only reported rate is below ten percent.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"adverse_reactions": ("Rash occurred in 3% of patients.",)}, {})
    assert tag_t04_high_frequency_adverse_effect(label) is None
