"""Tests for the name dictionary built from label summaries."""

from __future__ import annotations

from typing import Any

from rx_label_search.collect.filters import summarize_record
from rx_label_search.normalize.name_dictionary import (
    add_entry,
    build_name_dictionary,
    ingredient_sets_for,
    name_entries,
    normalize_name,
)


def test_normalize_name_collapses_case_and_space() -> None:
    """
    Takes no arguments.
    Normalizes a padded mixed-case name and an empty string.
    Gives nothing, or fails if either result is wrong.
    """
    assert normalize_name("  Zyprexa   Zydis ") == "zyprexa zydis"
    assert normalize_name("") == ""


def test_dictionary_resolves_brand_and_generic(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Builds the dictionary from every fixture and looks up brand and substance names.
    Gives nothing, or fails if a lookup gives the wrong ingredient set.
    """
    dictionary = build_name_dictionary(summarize_record(r) for r in fixture_labels.values())
    assert ingredient_sets_for(dictionary, "zyprexa") == (("OLANZAPINE",),)
    assert ingredient_sets_for(dictionary, "AMBIEN") == (("ZOLPIDEM TARTRATE",),)
    assert ingredient_sets_for(dictionary, "Lyrica") == (("PREGABALIN",),)
    assert ingredient_sets_for(dictionary, "sacubitril") == (("SACUBITRIL", "VALSARTAN"),)
    assert ingredient_sets_for(dictionary, "no such drug") == ()


def test_add_entry_does_not_mutate_or_duplicate() -> None:
    """
    Takes no arguments.
    Adds the same ingredient set twice under one key.
    Gives nothing, or fails if the original was mutated or the set was duplicated.
    """
    original: dict[str, dict[str, Any]] = {}
    once = add_entry(original, "k", "K", "brand", ("A",))
    twice = add_entry(once, "k", "K", "generic", ("A",))
    assert original == {}
    assert twice["k"]["ingredient_sets"] == [["A"]]
    assert twice["k"]["kinds"] == ["brand", "generic"]


def test_name_entries_empty_summary() -> None:
    """
    Takes no arguments.
    Lists names from a summary with no names at all.
    Gives nothing, or fails if the list is not empty.
    """
    from rx_label_search.records import LabelSummary

    assert name_entries(LabelSummary("i", "s", "1", "20250101", (), (), ())) == []
    assert build_name_dictionary([]) == {}
