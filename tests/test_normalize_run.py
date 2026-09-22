"""Tests for name resolution with the RxNorm fallback served from saved responses."""

from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Any

import pytest

from rx_label_search.collect.filters import summarize_record
from rx_label_search.collect.run import summary_to_json
from rx_label_search.normalize.name_dictionary import build_name_dictionary
from rx_label_search.normalize.name_matcher import STATUS_MATCHED, STATUS_RXNORM, STATUS_UNRESOLVED
from rx_label_search.normalize.run import (
    best_rank_one_candidates,
    lookup_bases_for_substance,
    resolve_name,
    salt_to_base_map,
    unique_substances,
)
from rx_label_search.storage.read_json import read_json

RXNORM_DIR = Path(__file__).resolve().parent / "fixtures" / "rxnorm"


def fixture_fetch(url: str) -> Any:
    """
    Takes a full RxNav URL.
    Serves the saved response whose source_url matches, so no network is used.
    Gives the response, or raises KeyError when no fixture was saved for the URL.
    """
    for path in RXNORM_DIR.glob("*.json"):
        document = read_json(path)
        if document["source_url"] == url:
            return document["response"]
    raise KeyError(url)


@pytest.fixture(scope="module")
def context(fixture_labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """
    Takes the fixture labels.
    Builds the dictionary, summaries, and salt-to-base map from fixtures and saved RxNorm responses.
    Gives a mapping with those three objects.
    """
    summaries = [summarize_record(record) for record in fixture_labels.values()]
    summary_docs = [summary_to_json(summary) for summary in summaries]
    cache = {substance: lookup_bases_for_substance(substance, fixture_fetch) for substance in unique_substances(summary_docs)}
    return {
        "dictionary": build_name_dictionary(summaries),
        "summaries": summary_docs,
        "salt_to_base": salt_to_base_map(cache),
    }


def test_flexril_resolves_via_rxnorm_with_chain(context: dict[str, Any]) -> None:
    """
    Takes the fixture context.
    Resolves the typo "Flexril" through the RxNorm fallback.
    Gives nothing, or fails if the chain is not Flexril, Flexeril, cyclobenzaprine, CYCLOBENZAPRINE HYDROCHLORIDE.
    """
    match = resolve_name("Flexril", context["dictionary"], fixture_fetch, context["summaries"], context["salt_to_base"])
    assert match.status == STATUS_RXNORM
    assert match.ingredient_set == ("CYCLOBENZAPRINE HYDROCHLORIDE",)
    assert match.chain == ("Flexril", "Flexeril", "cyclobenzaprine", "CYCLOBENZAPRINE HYDROCHLORIDE")


def test_local_match_never_calls_rxnorm(context: dict[str, Any]) -> None:
    """
    Takes the fixture context.
    Resolves a brand name that the local dictionary knows, with a fetch function that must not be called.
    Gives nothing, or fails if the fallback ran.
    """

    def forbidden(url: str) -> Any:
        """
        Takes a URL.
        Fails the test because the fallback should not run.
        Gives nothing, always raising AssertionError.
        """
        raise AssertionError(f"unexpected RxNorm call: {url}")

    match = resolve_name("Lyrica", context["dictionary"], forbidden, context["summaries"], context["salt_to_base"])
    assert match.status == STATUS_MATCHED
    assert match.ingredient_set == ("PREGABALIN",)


def test_unresolved_without_fetch_stays_unresolved(context: dict[str, Any]) -> None:
    """
    Takes the fixture context.
    Resolves "Flexril" with no fetch function.
    Gives nothing, or fails if the status is not unresolved.
    """
    assert resolve_name("Flexril", context["dictionary"], None, context["summaries"], context["salt_to_base"]).status == STATUS_UNRESOLVED


def test_salt_to_base_map_from_fixture_responses(context: dict[str, Any]) -> None:
    """
    Takes the fixture context.
    Reads the salt-to-base map built from saved responses.
    Gives nothing, or fails if the Adderall salts or venlafaxine do not roll up as expected.
    """
    mapping = context["salt_to_base"]
    assert mapping["AMPHETAMINE ASPARTATE MONOHYDRATE"] == ["amphetamine"]
    assert mapping["DEXTROAMPHETAMINE SULFATE"] == ["dextroamphetamine"]
    assert mapping["VENLAFAXINE HYDROCHLORIDE"] == ["venlafaxine"]
    assert mapping["DESVENLAFAXINE SUCCINATE"] == ["desvenlafaxine"]


def test_best_rank_one_candidates_dedupes() -> None:
    """
    Takes no arguments.
    Reduces candidates that repeat one rxcui at rank 1 and include a rank 2.
    Gives nothing, or fails if the result is not the single rank-1 pair.
    """
    candidates = (("1", "A", 9.0, 1), ("1", "A", 9.0, 1), ("2", "B", 5.0, 2))
    assert best_rank_one_candidates(candidates) == (("1", "A"),)
    assert best_rank_one_candidates(()) == ()


def test_unique_substances_and_empty_map() -> None:
    """
    Takes no arguments.
    Collects substances from two summaries and reduces an empty cache.
    Gives nothing, or fails if either result is wrong.
    """
    assert unique_substances([{"ingredient_set": ["B", "A"]}, {"ingredient_set": ["A"]}]) == ("A", "B")
    assert salt_to_base_map({}) == {}
    assert urllib.parse.quote("x") == "x"
