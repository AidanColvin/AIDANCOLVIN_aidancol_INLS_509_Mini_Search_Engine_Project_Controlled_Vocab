"""Pure readers for the RxNav REST response shapes the tool depends on."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def approximate_candidates(response: Mapping[str, Any]) -> tuple[tuple[str, str, float, int], ...]:
    """
    Takes a decoded approximateTerm response.
    Reads the candidates that carry a name.
    Gives (rxcui, name, score, rank) tuples in response order, empty when there are none.
    """
    group = response.get("approximateGroup") or {}
    found: list[tuple[str, str, float, int]] = []
    for candidate in group.get("candidate") or []:
        name = candidate.get("name")
        if not name:
            continue
        found.append((str(candidate["rxcui"]), str(name), float(candidate.get("score", 0)), int(candidate.get("rank", 0))))
    return tuple(found)


def rxcui_ids(response: Mapping[str, Any]) -> tuple[str, ...]:
    """
    Takes a decoded findRxcuiByString response.
    Reads the RxNorm ids it lists.
    Gives the tuple of id strings, empty when nothing matched.
    """
    group = response.get("idGroup") or {}
    return tuple(str(value) for value in group.get("rxnormId") or [])


def related_concepts(response: Mapping[str, Any]) -> tuple[tuple[str, str, str], ...]:
    """
    Takes a decoded getRelatedByType response.
    Reads every related concept across the term-type groups.
    Gives (rxcui, name, tty) tuples, empty when the response has no concept properties.
    """
    group = response.get("relatedGroup") or {}
    found: list[tuple[str, str, str]] = []
    for concept_group in group.get("conceptGroup") or []:
        for concept in concept_group.get("conceptProperties") or []:
            found.append((str(concept["rxcui"]), str(concept["name"]), str(concept.get("tty", concept_group.get("tty", "")))))
    return tuple(found)


def history_ingredients(response: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    """
    Takes a decoded getRxcuiHistoryStatus response.
    Reads the derived ingredient concepts, which exist even for obsolete brand names.
    Gives (rxcui, name) tuples, empty when the response lists none.
    """
    history = response.get("rxcuiStatusHistory") or {}
    derived = history.get("derivedConcepts") or {}
    return tuple(
        (str(concept["ingredientRxcui"]), str(concept["ingredientName"]))
        for concept in derived.get("ingredientConcept") or []
    )


def history_name(response: Mapping[str, Any]) -> str:
    """
    Takes a decoded getRxcuiHistoryStatus response.
    Reads the concept's own name from its attributes.
    Gives the name, or an empty string when it is absent.
    """
    history = response.get("rxcuiStatusHistory") or {}
    return str((history.get("attributes") or {}).get("name") or "")
