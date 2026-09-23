"""Tests for settling same-molecule salt ambiguity and preferring an exact RxNorm name over a fuzzy local match."""

from __future__ import annotations

from typing import Any

import pytest

from rx_label_search.normalize.name_matcher import STATUS_MATCHED, STATUS_NEEDS_CONFIRMATION, STATUS_RXNORM
from rx_label_search.normalize.run import preferred_same_molecule_set, resolve_name, same_molecule
from rx_label_search.normalize.rxnorm_client import approximate_term_url, history_status_url

ONDANSETRON_SETS = (("ONDANSETRON HYDROCHLORIDE",), ("ONDANSETRON",), ("ONDANSETRON", "ONDANSETRON HYDROCHLORIDE"))
SALT_TO_BASE = {
    "ONDANSETRON HYDROCHLORIDE": ["ondansetron"],
    "IBUPROFEN LYSINE": ["ibuprofen"],
    "HYDROXYZINE PAMOATE": ["hydroxyzine"],
    "HYDROXYZINE HYDROCHLORIDE": ["hydroxyzine"],
    "WARFARIN SODIUM": ["warfarin"],
    "DIPHENHYDRAMINE HYDROCHLORIDE": ["diphenhydramine"],
}


def fake_rxnorm(concept_name: str, rxcui: str, ingredient: str) -> Any:
    """
    Takes an RxNorm concept name, its id, and the ingredient it should report.
    Builds a fetch function that answers the approximate-term and history-status URLs for that concept.
    Gives the fetch function, which raises KeyError for any other URL.
    """
    responses = {
        approximate_term_url(concept_name): {"approximateGroup": {"candidate": [{"rxcui": rxcui, "name": concept_name, "score": "100", "rank": "1"}]}},
        history_status_url(rxcui): {"rxcuiStatusHistory": {"derivedConcepts": {"ingredientConcept": [{"ingredientRxcui": "9", "ingredientName": ingredient}]}}},
    }

    def fetch(url: str) -> Any:
        """
        Takes a full RxNav URL.
        Serves the prepared response for it.
        Gives the response, or raises KeyError for an unexpected URL.
        """
        return responses[url]

    return fetch


def test_preferred_set_is_plain_base_then_single_salt_then_alphabetical() -> None:
    """
    Takes no arguments.
    Chooses among ondansetron salt forms, among two hydroxyzine salts, and from no sets at all.
    Gives nothing, or fails if the plain base, the alphabetically first salt, or the ValueError is not produced.
    """
    assert preferred_same_molecule_set(ONDANSETRON_SETS, SALT_TO_BASE) == ("ONDANSETRON",)
    assert preferred_same_molecule_set((("HYDROXYZINE PAMOATE",), ("HYDROXYZINE HYDROCHLORIDE",)), SALT_TO_BASE) == ("HYDROXYZINE HYDROCHLORIDE",)
    with pytest.raises(ValueError):
        preferred_same_molecule_set((), SALT_TO_BASE)


def test_same_molecule_needs_identical_rollups() -> None:
    """
    Takes no arguments.
    Compares salt forms of one drug, a single set, and two different drugs.
    Gives nothing, or fails if any answer is wrong.
    """
    assert same_molecule(ONDANSETRON_SETS, SALT_TO_BASE)
    assert not same_molecule((("ONDANSETRON",),), SALT_TO_BASE)
    assert not same_molecule((("ACETAMINOPHEN",), ("ACETAMINOPHEN", "DIPHENHYDRAMINE HYDROCHLORIDE")), SALT_TO_BASE)


def test_local_brand_used_by_two_salt_forms_settles_on_the_plain_base() -> None:
    """
    Takes no arguments.
    Resolves "Motrin" from a dictionary where the brand appears on an ibuprofen label and an ibuprofen lysine label.
    Gives nothing, or fails if the match still needs confirmation or does not settle on plain IBUPROFEN with the chain extended.
    """
    dictionary = {"motrin": {"display": "Motrin", "kinds": ["brand"], "ingredient_sets": [["IBUPROFEN LYSINE"], ["IBUPROFEN"]]}}
    match = resolve_name("Motrin", dictionary, None, [], SALT_TO_BASE)
    assert match.status == STATUS_MATCHED
    assert match.ingredient_set == ("IBUPROFEN",)
    assert match.chain[-1] == "IBUPROFEN"
    assert "2 salt forms" in match.reason


def test_local_brand_used_by_different_drugs_still_needs_confirmation() -> None:
    """
    Takes no arguments.
    Resolves a brand whose two ingredient sets are genuinely different products.
    Gives nothing, or fails if the ambiguity is settled instead of reported.
    """
    dictionary = {"tylenol pm": {"display": "Tylenol PM", "kinds": ["brand"], "ingredient_sets": [["ACETAMINOPHEN", "DIPHENHYDRAMINE HYDROCHLORIDE"], ["ACETAMINOPHEN"]]}}
    assert resolve_name("Tylenol PM", dictionary, None, [], SALT_TO_BASE).status == STATUS_NEEDS_CONFIRMATION


def test_rxnorm_fallback_settles_salt_forms_instead_of_asking() -> None:
    """
    Takes no arguments.
    Resolves "Zofran" through a fake RxNorm where the collection carries three ondansetron salt forms.
    Gives nothing, or fails if the match does not settle on plain ONDANSETRON via RxNorm.
    """
    summaries = [{"ingredient_set": list(ingredient_set)} for ingredient_set in ONDANSETRON_SETS]
    match = resolve_name("Zofran", {}, fake_rxnorm("Zofran", "1", "ondansetron"), summaries, SALT_TO_BASE)
    assert match.status == STATUS_RXNORM
    assert match.ingredient_set == ("ONDANSETRON",)
    assert "3 salt forms" in match.reason


def test_exact_rxnorm_name_beats_a_fuzzy_local_match() -> None:
    """
    Takes no arguments.
    Resolves "Coumadin" where the local dictionary only fuzzily matches the homeopathic substance COUMARIN but RxNorm knows the exact brand.
    Gives nothing, or fails if the fuzzy local guess wins, or if the local guess is not kept when RxNorm is off.
    """
    dictionary = {"coumarin": {"display": "COUMARIN", "kinds": ["substance"], "ingredient_sets": [["COUMARIN"]]}}
    summaries = [{"ingredient_set": ["WARFARIN SODIUM"]}, {"ingredient_set": ["COUMARIN"]}]
    match = resolve_name("Coumadin", dictionary, fake_rxnorm("Coumadin", "2", "warfarin"), summaries, SALT_TO_BASE)
    assert match.status == STATUS_RXNORM
    assert match.ingredient_set == ("WARFARIN SODIUM",)
    assert "preferred over the fuzzy local match COUMARIN" in match.reason
    offline = resolve_name("Coumadin", dictionary, None, summaries, SALT_TO_BASE)
    assert (offline.status, offline.ingredient_set) == (STATUS_MATCHED, ("COUMARIN",))


def test_typo_keeps_the_fuzzy_local_match_when_rxnorm_is_only_close() -> None:
    """
    Takes no arguments.
    Resolves the typo "trazdone" where RxNorm's closest name is "trazodone", not the typed text.
    Gives nothing, or fails if the local fuzzy match is discarded.
    """
    dictionary = {"trazodone": {"display": "trazodone", "kinds": ["generic"], "ingredient_sets": [["TRAZODONE HYDROCHLORIDE"]]}}
    fetch = fake_rxnorm("trazodone", "3", "trazodone")

    def close_fetch(url: str) -> Any:
        """
        Takes a full RxNav URL.
        Answers the approximate query for the typo with the correctly spelled concept.
        Gives the response, or raises KeyError for an unexpected URL.
        """
        if url == approximate_term_url("trazdone"):
            return fetch(approximate_term_url("trazodone"))
        return fetch(url)

    match = resolve_name("trazdone", dictionary, close_fetch, [{"ingredient_set": ["TRAZODONE HYDROCHLORIDE"]}], {"TRAZODONE HYDROCHLORIDE": ["trazodone"]})
    assert match.status == STATUS_MATCHED
    assert match.ingredient_set == ("TRAZODONE HYDROCHLORIDE",)
