"""Tests for the collection invariant checks."""

from __future__ import annotations

from typing import Any

from rx_label_search.collect.verify import collection_problems


def test_fixtures_form_a_valid_collection(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks the fixtures as if they were a built collection.
    Gives nothing, or fails if any problem is reported.
    """
    count, problems = collection_problems(fixture_labels.values())
    assert count == len(fixture_labels)
    assert problems == []


def test_duplicates_and_bad_records_are_reported(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks a collection with a repeated label and an empty record.
    Gives nothing, or fails if the problems are not all reported.
    """
    gabapentin = fixture_labels["gabapentin"]
    count, problems = collection_problems([gabapentin, gabapentin, {}])
    assert count == 3
    assert any("duplicate ingredient set" in p for p in problems)
    assert any("missing openfda" in p for p in problems)


def test_empty_collection() -> None:
    """
    Takes no arguments.
    Checks an empty collection.
    Gives nothing, or fails if the count is not zero or problems are reported.
    """
    assert collection_problems([]) == (0, [])
