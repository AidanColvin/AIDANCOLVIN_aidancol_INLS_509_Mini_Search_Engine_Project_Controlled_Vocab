"""Tests for duplication-flag detection."""

from __future__ import annotations

from typing import Any

from rx_label_search.interactions.duplicates import build_base_ingredient_flag, build_duplication_flags, build_metabolite_flag

REFERENCE = [{"parent": "venlafaxine", "metabolite": "desvenlafaxine", "sentence": "cited sentence", "field": "description", "set_id": "s-venla", "effective_time": "20250101", "source_url": "https://example.test"}]


def drug(name: str, bases: list[str]) -> dict[str, Any]:
    """
    Takes a display name and its base ingredients.
    Builds a minimal resolved-drug entry for duplication tests.
    Gives the dictionary.
    """
    return {"display_name": name, "record": {"set_id": f"s-{name}", "effective_time": "20250101", "base_ingredients": bases}}


def test_build_base_ingredient_flag_fires_on_overlap_and_not_otherwise() -> None:
    """
    Takes no arguments.
    Checks two drugs sharing a base ingredient and two that share none.
    Gives nothing, or fails if either result is wrong.
    """
    a = drug("Adderall", ["amphetamine", "dextroamphetamine"])
    b = drug("Dextrostat", ["dextroamphetamine"])
    flag = build_base_ingredient_flag(a, b)
    assert flag is not None
    assert flag.kind == "duplication"
    c = drug("Ibuprofen", ["ibuprofen"])
    assert build_base_ingredient_flag(a, c) is None


def test_build_metabolite_flag_fires_on_cited_pair_and_not_otherwise() -> None:
    """
    Takes no arguments.
    Checks venlafaxine with desvenlafaxine against the reference and an unrelated pair.
    Gives nothing, or fails if either result is wrong.
    """
    venlafaxine = drug("Venlafaxine", ["venlafaxine"])
    desvenlafaxine = drug("Desvenlafaxine", ["desvenlafaxine"])
    flag = build_metabolite_flag(venlafaxine, desvenlafaxine, REFERENCE)
    assert flag is not None
    assert "example.test" in flag.note
    unrelated = drug("Ibuprofen", ["ibuprofen"])
    assert build_metabolite_flag(venlafaxine, unrelated, REFERENCE) is None


def test_build_duplication_flags_checks_every_pair_once() -> None:
    """
    Takes no arguments.
    Builds flags across a three-drug list with one base-ingredient overlap.
    Gives nothing, or fails if the count is wrong or the empty list crashes.
    """
    a = drug("Adderall", ["amphetamine", "dextroamphetamine"])
    b = drug("Dextrostat", ["dextroamphetamine"])
    c = drug("Ibuprofen", ["ibuprofen"])
    flags = build_duplication_flags([a, b, c], REFERENCE)
    assert len(flags) == 1
    assert build_duplication_flags([], REFERENCE) == ()
