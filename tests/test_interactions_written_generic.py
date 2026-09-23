"""Tests for resolving an entry by the generic the prescriber wrote (interactions/checker.py), the fix for lists L01-L41 all coming back "not found"."""

from __future__ import annotations

from rx_label_search.interactions.checker import (
    STATUS_INGREDIENT_ONLY,
    name_queries,
    resolve_entry,
    resolve_ingredient_only,
    resolve_written_generic,
    resolved_drug,
)
from rx_label_search.normalize.med_line_parser import parse_entry
from rx_label_search.normalize.name_matcher import STATUS_MATCHED

SUMMARIES = [
    {"set_id": "s1", "ingredient_set": ["DIVALPROEX SODIUM"], "brand_names": ["Depakote"], "generic_names": ["divalproex sodium"]},
    {"set_id": "s2", "ingredient_set": ["VERAPAMIL HYDROCHLORIDE"], "brand_names": ["Calan"], "generic_names": ["verapamil"]},
    {"set_id": "s3", "ingredient_set": ["TRANDOLAPRIL", "VERAPAMIL HYDROCHLORIDE"], "brand_names": ["Tarka"], "generic_names": ["trandolapril and verapamil"]},
    {"set_id": "s4", "ingredient_set": ["ASPIRIN", "DIPYRIDAMOLE"], "brand_names": ["Aggrenox"], "generic_names": ["aspirin and dipyridamole"]},
]
SALT_TO_BASE = {"DIVALPROEX SODIUM": ["valproate"], "VERAPAMIL HYDROCHLORIDE": ["verapamil"], "TRANDOLAPRIL": ["trandolapril"], "ASPIRIN": ["aspirin"], "DIPYRIDAMOLE": ["dipyridamole"]}


def test_written_generic_picks_the_single_ingredient_label() -> None:
    """
    Takes no arguments.
    Resolves "Calan SR (verapamil ER)", where a name lookup ties with a verapamil combination; list L37.
    Gives nothing; asserts the plain verapamil label is chosen, not the combination.
    """
    match = resolve_written_generic(parse_entry("Calan SR (verapamil ER) 240 mg once daily = 240 mg/day"), SUMMARIES, SALT_TO_BASE)
    assert match is not None and match.status == STATUS_MATCHED and match.ingredient_set == ("VERAPAMIL HYDROCHLORIDE",)


def test_written_salt_rolls_up_to_its_base() -> None:
    """
    Takes no arguments.
    Resolves "Depakote (divalproex sodium)"; lists L08, L26.
    Gives nothing; asserts the divalproex label is found through its base ingredient.
    """
    match = resolve_written_generic(parse_entry("Depakote (divalproex sodium) 500 mg twice daily = 1000 mg/day"), SUMMARIES, SALT_TO_BASE)
    assert match is not None and match.ingredient_set == ("DIVALPROEX SODIUM",)


def test_ingredient_with_no_single_label_still_takes_part() -> None:
    """
    Takes no arguments.
    Resolves "Bayer (aspirin OTC)" when the collection has aspirin only inside combinations; lists L05, L26.
    Gives nothing; asserts an ingredient-only match that the checker turns into a drug with no label.
    """
    entry = parse_entry("Bayer (aspirin OTC) 81 mg once daily = 81 mg/day")
    assert resolve_written_generic(entry, SUMMARIES, SALT_TO_BASE) is None
    match = resolve_ingredient_only(entry, None, SALT_TO_BASE)
    assert match is not None and match.status == STATUS_INGREDIENT_ONLY
    drug = resolved_drug(entry, match, {}, {}, SALT_TO_BASE)
    assert drug is not None and drug["record"]["no_label"] and drug["record"]["base_ingredients"] == ("aspirin",)
    assert drug["display_name"] == "Bayer"


def test_unknown_written_ingredient_is_not_accepted_without_rxnorm() -> None:
    """
    Takes no arguments.
    Tries an ingredient the collection has never seen, with no RxNorm fetch available.
    Gives nothing; asserts it is not accepted, so a typo never becomes a drug.
    """
    assert resolve_ingredient_only(parse_entry("Foo (notadrugzz) 5 mg daily"), None, SALT_TO_BASE) is None


def test_queries_try_generic_then_brand() -> None:
    """
    Takes no arguments.
    Lists the names tried for a brand-and-generic entry.
    Gives nothing; asserts the generic comes first, then the brand.
    """
    assert name_queries(parse_entry("Zyprexa (olanzapine) 10 mg once daily = 10 mg/day"))[:2] == ("olanzapine", "Zyprexa")
    match = resolve_entry(parse_entry("Depakote (divalproex sodium) 500 mg twice daily"), {}, None, SUMMARIES, SALT_TO_BASE)
    assert match.status == STATUS_MATCHED
