"""Pure checks that a built collection meets the Part 1 scope rules."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from rx_label_search.collect.filters import has_openfda, ingredient_set, is_human_prescription


def collection_problems(records: Iterable[Mapping[str, Any]]) -> tuple[int, list[str]]:
    """
    Takes the raw records of a built collection.
    Checks that every record is a human prescription label with openfda and that no ingredient set repeats.
    Gives the record count and a list of problem strings, empty when the collection is valid.
    """
    problems: list[str] = []
    seen: Counter[tuple[str, ...]] = Counter()
    count = 0
    for record in records:
        count += 1
        label_id = str(record.get("id", "?"))
        if not has_openfda(record):
            problems.append(f"{label_id}: missing openfda")
        if not is_human_prescription(record):
            problems.append(f"{label_id}: not a human prescription drug")
        ingredients = ingredient_set(record)
        if not ingredients:
            problems.append(f"{label_id}: empty ingredient set")
        seen[ingredients] += 1
    problems.extend(f"duplicate ingredient set: {ingredients}" for ingredients, n in seen.items() if n > 1)
    return count, problems
