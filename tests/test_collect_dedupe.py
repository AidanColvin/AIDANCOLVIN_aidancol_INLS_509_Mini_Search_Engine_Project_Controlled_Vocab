"""Tests for newest-label selection."""

from __future__ import annotations

from rx_label_search.collect.dedupe import newest_per_ingredient_set, recency_key, version_number, winner_ids
from rx_label_search.records import LabelSummary


def make(label_id: str, effective_time: str, version: str, ingredients: tuple[str, ...]) -> LabelSummary:
    """
    Takes an id, effective time, version, and ingredient set.
    Builds a label summary with empty name fields.
    Gives the summary.
    """
    return LabelSummary(label_id, "set-" + label_id, version, effective_time, ingredients, (), ())


def test_version_number_handles_non_digits() -> None:
    """
    Takes no arguments.
    Converts a numeric and a non-numeric version.
    Gives nothing, or fails if either conversion is wrong.
    """
    assert version_number("12") == 12
    assert version_number("") == 0


def test_newest_prefers_effective_time_then_version_then_id() -> None:
    """
    Takes no arguments.
    Chooses among three labels of one ingredient set with tied and untied keys.
    Gives nothing, or fails if the wrong label wins.
    """
    a = make("a", "20250101", "9", ("X",))
    b = make("b", "20250102", "1", ("X",))
    c = make("c", "20250102", "2", ("X",))
    d = make("d", "20250102", "2", ("X",))
    newest = newest_per_ingredient_set([a, b, c, d])
    assert newest[("X",)].label_id == "d"
    assert recency_key(c) < recency_key(d)


def test_newest_keeps_one_per_set_and_empty() -> None:
    """
    Takes no arguments.
    Runs the selection over two ingredient sets and over nothing.
    Gives nothing, or fails if the winners are wrong.
    """
    a = make("a", "20250101", "1", ("X",))
    b = make("b", "20250101", "1", ("X", "Y"))
    assert winner_ids(newest_per_ingredient_set([a, b])) == frozenset({"a", "b"})
    assert newest_per_ingredient_set([]) == {}
    assert winner_ids({}) == frozenset()
