"""Tests for the RxNav response readers against saved live responses."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rx_label_search.normalize.rxnorm_responses import (
    approximate_candidates,
    history_ingredients,
    history_name,
    related_concepts,
    rxcui_ids,
)
from rx_label_search.storage.read_json import read_json

RXNORM_DIR = Path(__file__).resolve().parent / "fixtures" / "rxnorm"


def load(name: str) -> dict[str, Any]:
    """
    Takes an RxNorm fixture name.
    Reads the fixture and unwraps the saved response.
    Gives the response mapping.
    """
    return read_json(RXNORM_DIR / f"{name}.json")["response"]


def test_flexril_approximate_match_names_flexeril() -> None:
    """
    Takes no arguments.
    Reads the saved approximate match for the typo "Flexril".
    Gives nothing, or fails if the first named candidate is not Flexeril at rank 1.
    """
    candidates = approximate_candidates(load("approximateTerm_Flexril"))
    assert candidates[0][:2] == ("224954", "Flexeril")
    assert candidates[0][3] == 1


def test_history_status_gives_cyclobenzaprine_for_obsolete_flexeril() -> None:
    """
    Takes no arguments.
    Reads the saved history status for the obsolete Flexeril concept.
    Gives nothing, or fails if the derived ingredient is not cyclobenzaprine.
    """
    response = load("historystatus_224954")
    assert history_name(response) == "Flexeril"
    assert history_ingredients(response) == (("21949", "cyclobenzaprine"),)


def test_salt_lookups_roll_up_to_base_ingredients() -> None:
    """
    Takes no arguments.
    Reads the saved findRxcuiByString and related-IN responses for the four Adderall salts.
    Gives nothing, or fails if any salt does not resolve to amphetamine or dextroamphetamine.
    """
    expected = {
        "amphetamine_aspartate_monohydrate": ("405812", "amphetamine"),
        "dextroamphetamine_saccharate": ("221088", "dextroamphetamine"),
        "amphetamine_sulfate": ("81952", "amphetamine"),
        "dextroamphetamine_sulfate": ("3287", "dextroamphetamine"),
    }
    for key, (rxcui, base) in expected.items():
        assert rxcui_ids(load(f"rxcui_search_{key}")) == (rxcui,)
        names = [name for _, name, tty in related_concepts(load(f"related_IN_{rxcui}")) if tty == "IN"]
        assert names == [base], key


def test_readers_handle_empty_responses() -> None:
    """
    Takes no arguments.
    Reads empty and minimal responses.
    Gives nothing, or fails if any reader does not return an empty result.
    """
    assert approximate_candidates({}) == ()
    assert rxcui_ids({"idGroup": {}}) == ()
    assert related_concepts({"relatedGroup": {"conceptGroup": [{"tty": "IN"}]}}) == ()
    assert history_ingredients({}) == ()
    assert history_name({}) == ""
