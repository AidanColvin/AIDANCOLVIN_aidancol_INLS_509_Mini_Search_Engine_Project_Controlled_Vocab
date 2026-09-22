"""Tests for base-ingredient rollup, shared bases, and cited metabolite links."""

from __future__ import annotations

from pathlib import Path

from rx_label_search.normalize.rollup import (
    base_ingredients,
    base_names_for,
    metabolite_links,
    sets_with_bases,
    shared_bases,
)
from rx_label_search.storage.read_json import read_json

REFERENCE = read_json(Path(__file__).resolve().parent.parent / "data" / "reference" / "active_metabolites.json")["pairs"]
SALT_TO_BASE = {
    "AMPHETAMINE ASPARTATE MONOHYDRATE": ["amphetamine"],
    "AMPHETAMINE SULFATE": ["amphetamine"],
    "DEXTROAMPHETAMINE SACCHARATE": ["dextroamphetamine"],
    "DEXTROAMPHETAMINE SULFATE": ["dextroamphetamine"],
    "DESVENLAFAXINE SUCCINATE": ["desvenlafaxine"],
    "VENLAFAXINE HYDROCHLORIDE": ["venlafaxine"],
}
ADDERALL = ("AMPHETAMINE ASPARTATE MONOHYDRATE", "AMPHETAMINE SULFATE", "DEXTROAMPHETAMINE SACCHARATE", "DEXTROAMPHETAMINE SULFATE")


def test_adderall_rolls_up_to_two_bases() -> None:
    """
    Takes no arguments.
    Rolls the four Adderall salts up through the salt-to-base map.
    Gives nothing, or fails if the result is not amphetamine and dextroamphetamine.
    """
    assert base_ingredients(ADDERALL, SALT_TO_BASE) == ("amphetamine", "dextroamphetamine")
    assert base_ingredients((), SALT_TO_BASE) == ()


def test_unknown_substance_keeps_its_own_name() -> None:
    """
    Takes no arguments.
    Rolls up a substance absent from the map.
    Gives nothing, or fails if the lowercase substance itself is not returned.
    """
    assert base_names_for("OLANZAPINE", SALT_TO_BASE) == ("olanzapine",)


def test_shared_bases_flags_adderall_with_dextroamphetamine() -> None:
    """
    Takes no arguments.
    Intersects the Adderall bases with a dextroamphetamine-only product's bases.
    Gives nothing, or fails if dextroamphetamine is not shared or an unrelated pair shares anything.
    """
    adderall = base_ingredients(ADDERALL, SALT_TO_BASE)
    dex = base_ingredients(("DEXTROAMPHETAMINE SULFATE",), SALT_TO_BASE)
    assert shared_bases(adderall, dex) == ("dextroamphetamine",)
    assert shared_bases(adderall, ("olanzapine",)) == ()


def test_metabolite_link_between_venlafaxine_and_desvenlafaxine() -> None:
    """
    Takes no arguments.
    Looks for a cited metabolite link in both directions and for an unrelated pair.
    Gives nothing, or fails if the cited pair is missed or the unrelated pair links.
    """
    links = metabolite_links(("venlafaxine",), ("desvenlafaxine",), REFERENCE)
    assert len(links) == 1
    assert links[0]["set_id"] == "ff837eb1-24c3-4c63-9b4b-c6b5935a9b47"
    assert metabolite_links(("desvenlafaxine",), ("venlafaxine",), REFERENCE) == links
    assert metabolite_links(("olanzapine",), ("venlafaxine",), REFERENCE) == ()


def test_sets_with_bases_finds_exact_rollup() -> None:
    """
    Takes no arguments.
    Searches summaries for the ingredient sets whose bases are exactly the wanted names.
    Gives nothing, or fails if the wrong sets are returned.
    """
    summaries = [
        {"ingredient_set": list(ADDERALL)},
        {"ingredient_set": ["DEXTROAMPHETAMINE SULFATE"]},
        {"ingredient_set": ["VENLAFAXINE HYDROCHLORIDE"]},
    ]
    assert sets_with_bases(summaries, SALT_TO_BASE, ("dextroamphetamine",)) == (("DEXTROAMPHETAMINE SULFATE",),)
    assert sets_with_bases(summaries, SALT_TO_BASE, ("Amphetamine", "dextroamphetamine")) == (ADDERALL,)
    assert sets_with_bases([], SALT_TO_BASE, ("x",)) == ()
