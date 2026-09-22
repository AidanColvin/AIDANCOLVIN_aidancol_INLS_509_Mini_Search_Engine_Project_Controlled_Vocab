"""Pure base-ingredient rollup and duplicate detection."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def base_names_for(substance: str, salt_to_base: Mapping[str, Iterable[str]]) -> tuple[str, ...]:
    """
    Takes an openFDA substance name and the salt-to-base map built from RxNorm.
    Looks up the base ingredient names for the substance.
    Gives the sorted lowercase base names, or the substance itself lowercased when the map lacks it.
    """
    bases = salt_to_base.get(substance)
    if not bases:
        return (substance.lower(),)
    return tuple(sorted({base.lower() for base in bases}))


def base_ingredients(ingredient_set: Iterable[str], salt_to_base: Mapping[str, Iterable[str]]) -> tuple[str, ...]:
    """
    Takes an ingredient set and the salt-to-base map.
    Rolls every substance up to its base ingredient names and merges them.
    Gives the sorted, de-duplicated tuple of base names, empty for an empty set.
    """
    merged: set[str] = set()
    for substance in ingredient_set:
        merged.update(base_names_for(substance, salt_to_base))
    return tuple(sorted(merged))


def shared_bases(first: Iterable[str], second: Iterable[str]) -> tuple[str, ...]:
    """
    Takes two tuples of base ingredient names.
    Intersects them.
    Gives the sorted shared names, empty when nothing is shared.
    """
    return tuple(sorted(set(first) & set(second)))


def metabolite_links(first: Iterable[str], second: Iterable[str], reference: Iterable[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    """
    Takes two tuples of base ingredient names and the cited active-metabolite reference entries.
    Finds entries whose parent is in one tuple and whose metabolite is in the other.
    Gives the matching reference entries, empty when no cited pair links the two.
    """
    left, right = set(first), set(second)
    found: list[Mapping[str, Any]] = []
    for entry in reference:
        parent = str(entry["parent"]).lower()
        metabolite = str(entry["metabolite"]).lower()
        if (parent in left and metabolite in right) or (parent in right and metabolite in left):
            found.append(entry)
    return tuple(found)


def sets_with_bases(
    summaries: Iterable[Mapping[str, Any]],
    salt_to_base: Mapping[str, Iterable[str]],
    wanted: Iterable[str],
) -> tuple[tuple[str, ...], ...]:
    """
    Takes collection summaries, the salt-to-base map, and a set of base ingredient names.
    Finds the ingredient sets whose base rollup equals exactly the wanted names.
    Gives the matching ingredient-set tuples in summary order, empty when none match.
    """
    target = tuple(sorted({name.lower() for name in wanted}))
    found: list[tuple[str, ...]] = []
    for summary in summaries:
        ingredient_set = tuple(summary["ingredient_set"])
        if base_ingredients(ingredient_set, salt_to_base) == target and ingredient_set not in found:
            found.append(ingredient_set)
    return tuple(found)
