"""Tests for typo-tolerant name matching against a fixture-built dictionary."""

from __future__ import annotations

from typing import Any

import pytest

from rx_label_search.collect.filters import summarize_record
from rx_label_search.normalize.name_dictionary import build_name_dictionary
from rx_label_search.normalize.name_matcher import (
    STATUS_MATCHED,
    STATUS_NEEDS_CONFIRMATION,
    STATUS_UNRESOLVED,
    leading_words,
    match_name,
    similarity,
)


@pytest.fixture(scope="module")
def dictionary(fixture_labels: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """
    Takes the fixture labels.
    Builds the name dictionary from every fixture.
    Gives the dictionary.
    """
    return build_name_dictionary(summarize_record(record) for record in fixture_labels.values())


def test_exact_brand_matches_with_chain(dictionary: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture dictionary.
    Matches the typed name "Zyprexa".
    Gives nothing, or fails if the status, ingredient set, or chain is wrong.
    """
    match = match_name("Zyprexa", dictionary)
    assert match.status == STATUS_MATCHED
    assert match.ingredient_set == ("OLANZAPINE",)
    assert match.chain == ("Zyprexa", "OLANZAPINE")


def test_typo_trazdone_resolves_to_trazodone(dictionary: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture dictionary.
    Matches the typo "trazdone".
    Gives nothing, or fails if it does not resolve to trazodone hydrochloride with the mapping shown.
    """
    match = match_name("trazdone", dictionary)
    assert match.status == STATUS_MATCHED
    assert match.ingredient_set == ("TRAZODONE HYDROCHLORIDE",)
    assert match.chain[0] == "trazdone"
    assert "razodone" in match.chain[1]


def test_flexril_is_unresolved_locally(dictionary: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture dictionary.
    Matches "Flexril", whose brand has no label in openFDA.
    Gives nothing, or fails if the local matcher does not report it unresolved.
    """
    assert match_name("Flexril", dictionary).status == STATUS_UNRESOLVED


def test_ambiguous_substance_needs_confirmation(dictionary: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture dictionary.
    Matches "dextroamphetamine", which appears in the Adderall set and in a single-ingredient set.
    Gives nothing, or fails if the matcher picks silently instead of listing candidates.
    """
    match = match_name("dextroamphetamine", dictionary)
    assert match.status == STATUS_NEEDS_CONFIRMATION
    assert len(match.candidates) >= 2


def test_empty_and_nonsense_names(dictionary: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture dictionary.
    Matches an empty string and a nonsense string.
    Gives nothing, or fails if either is not unresolved.
    """
    assert match_name("", dictionary).status == STATUS_UNRESOLVED
    assert match_name("qwxzvbn", dictionary).status == STATUS_UNRESOLVED


def test_similarity_helpers() -> None:
    """
    Takes no arguments.
    Scores a query against a longer key by its leading words.
    Gives nothing, or fails if the prefix comparison does not raise the score.
    """
    assert leading_words("a b c", 2) == "a b"
    assert similarity("trazdone", "trazodone hydrochloride") > 0.9
    assert similarity("x", "x") == 1.0
