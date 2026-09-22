"""Tests for duplication-flag detection."""

from __future__ import annotations

from typing import Any

from rx_label_search.interactions.duplicates import DUPLICATE_THERAPY_TIER_NAME, build_base_ingredient_flag, build_duplication_flags, build_metabolite_flag

REFERENCE = [{"parent": "venlafaxine", "metabolite": "desvenlafaxine", "sentence": "cited sentence", "field": "description", "set_id": "s-Desvenlafaxine", "effective_time": "20250101", "source_url": "https://example.test"}]


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
    assert flag.tier_name == DUPLICATE_THERAPY_TIER_NAME
    assert flag.members[0].section == ""
    assert flag.members[1].section == ""
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
    assert flag.tier_name == DUPLICATE_THERAPY_TIER_NAME
    unrelated = drug("Ibuprofen", ["ibuprofen"])
    assert build_metabolite_flag(venlafaxine, unrelated, REFERENCE) is None


def test_build_metabolite_flag_attributes_the_sentence_to_the_cited_label_only() -> None:
    """
    Takes no arguments.
    Checks which member carries the citation when only one drug's own resolved label matches the reference's set_id.
    Gives nothing, or fails if the sentence is attributed to the wrong drug or to both.
    """
    venlafaxine = drug("Venlafaxine", ["venlafaxine"])
    desvenlafaxine = drug("Desvenlafaxine", ["desvenlafaxine"])
    flag = build_metabolite_flag(venlafaxine, desvenlafaxine, REFERENCE)
    assert flag is not None
    parent_member, metabolite_member = flag.members
    assert parent_member.drug_name == "Venlafaxine"
    assert parent_member.section == ""
    assert metabolite_member.drug_name == "Desvenlafaxine"
    assert metabolite_member.section == "description"
    assert metabolite_member.sentence == "cited sentence"
    assert metabolite_member.set_id == "s-Desvenlafaxine"


def test_build_metabolite_flag_falls_back_when_neither_label_matches_the_citation() -> None:
    """
    Takes no arguments.
    Checks a cited pair whose reference set_id matches neither drug's own resolved label.
    Gives nothing, or fails if a sentence is attributed to a label it did not come from.
    """
    mismatched_reference = [{**REFERENCE[0], "set_id": "s-some-other-label"}]
    venlafaxine = drug("Venlafaxine", ["venlafaxine"])
    desvenlafaxine = drug("Desvenlafaxine", ["desvenlafaxine"])
    flag = build_metabolite_flag(venlafaxine, desvenlafaxine, mismatched_reference)
    assert flag is not None
    assert flag.members[0].section == ""
    assert flag.members[1].section == ""


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
