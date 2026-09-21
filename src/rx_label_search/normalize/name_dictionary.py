"""Pure construction and lookup of the drug name dictionary."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from rx_label_search.records import LabelSummary

KIND_BRAND = "brand"
KIND_GENERIC = "generic"
KIND_SUBSTANCE = "substance"
_SPACES = re.compile(r"\s+")


def normalize_name(name: str) -> str:
    """
    Takes a drug name as typed or as listed on a label.
    Lowercases it, trims it, and collapses internal whitespace.
    Gives the normalized key, empty when the name is blank.
    """
    return _SPACES.sub(" ", name.strip().lower())


def name_entries(summary: LabelSummary) -> list[tuple[str, str, str]]:
    """
    Takes a label summary.
    Lists every brand, generic, and substance name on it with its kind.
    Gives a list of (kind, display name, normalized key) triples, empty when the summary has no names.
    """
    triples: list[tuple[str, str, str]] = []
    for kind, names in (
        (KIND_BRAND, summary.brand_names),
        (KIND_GENERIC, summary.generic_names),
        (KIND_SUBSTANCE, summary.ingredient_set),
    ):
        for name in names:
            key = normalize_name(name)
            if key:
                triples.append((kind, name, key))
    return triples


def add_entry(
    dictionary: dict[str, dict[str, Any]],
    key: str,
    display: str,
    kind: str,
    ingredients: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    """
    Takes a dictionary under construction, a normalized key, its display name, kind, and ingredient set.
    Records the ingredient set under the key without duplicating sets already present.
    Gives a new dictionary with the entry added.
    """
    updated = dict(dictionary)
    entry = dict(updated.get(key, {"display": display, "kinds": [], "ingredient_sets": []}))
    kinds = list(entry["kinds"])
    if kind not in kinds:
        kinds.append(kind)
    sets = [tuple(existing) for existing in entry["ingredient_sets"]]
    if ingredients not in sets:
        sets.append(ingredients)
    entry["kinds"] = kinds
    entry["ingredient_sets"] = [list(existing) for existing in sets]
    updated[key] = entry
    return updated


def build_name_dictionary(summaries: Iterable[LabelSummary]) -> dict[str, dict[str, Any]]:
    """
    Takes label summaries from every label that passed the scope filters, before de-duplication.
    Maps every normalized brand, generic, and substance name to the ingredient sets it appears with.
    Gives the dictionary keyed by normalized name, empty for no summaries.
    """
    dictionary: dict[str, dict[str, Any]] = {}
    for summary in summaries:
        for kind, display, key in name_entries(summary):
            dictionary = add_entry(dictionary, key, display, kind, summary.ingredient_set)
    return dictionary


def ingredient_sets_for(dictionary: Mapping[str, Mapping[str, Any]], name: str) -> tuple[tuple[str, ...], ...]:
    """
    Takes a name dictionary and a drug name.
    Looks up the ingredient sets recorded under the name's normalized key.
    Gives a tuple of ingredient-set tuples, empty when the name is unknown.
    """
    entry = dictionary.get(normalize_name(name))
    if entry is None:
        return ()
    return tuple(tuple(ingredients) for ingredients in entry["ingredient_sets"])
