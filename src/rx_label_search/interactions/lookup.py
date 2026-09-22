"""Pure indexing from an ingredient set to the collection label that carries it."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def ingredient_set_key(ingredient_set: Iterable[str]) -> str:
    """
    Takes an ingredient set, in any order.
    Sorts and joins it into one string key.
    Gives the key, empty when the set is empty.
    """
    return "|".join(sorted(ingredient_set))


def build_ingredient_set_index(summaries: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """
    Takes the collection summaries, each with an ingredient_set and a set_id.
    Maps every ingredient set's key to its set id.
    Gives the mapping, empty for no summaries.
    """
    return {ingredient_set_key(summary["ingredient_set"]): summary["set_id"] for summary in summaries}


def find_set_id_for_ingredients(ingredient_set: Iterable[str], index: Mapping[str, str]) -> str | None:
    """
    Takes an ingredient set and the ingredient-set-to-set-id index.
    Looks up the set id that carries it.
    Gives the set id, or None when no collection label carries that exact set.
    """
    return index.get(ingredient_set_key(ingredient_set))
