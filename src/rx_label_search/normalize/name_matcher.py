"""Pure matching of typed drug names against the name dictionary with typo tolerance."""

from __future__ import annotations

import difflib
from collections.abc import Mapping
from typing import Any

from rx_label_search.normalize.name_dictionary import normalize_name
from rx_label_search.records import NameMatch

LOCAL_MATCH_THRESHOLD = 0.85
AMBIGUITY_MARGIN = 0.03
MAX_CANDIDATES = 5
STATUS_MATCHED = "matched"
STATUS_NEEDS_CONFIRMATION = "needs_confirmation"
STATUS_UNRESOLVED = "unresolved"
STATUS_RXNORM = "matched_via_rxnorm"


def leading_words(text: str, count: int) -> str:
    """
    Takes a text and a word count.
    Keeps only the first count words.
    Gives the shortened text, unchanged when it has no more words than count.
    """
    return " ".join(text.split()[:count])


def similarity(query: str, key: str) -> float:
    """
    Takes a normalized query and a normalized dictionary key.
    Scores the query against the whole key and against the key's leading words of the same length.
    Gives the higher ratio between 0.0 and 1.0.
    """
    whole = difflib.SequenceMatcher(None, query, key).ratio()
    prefix = leading_words(key, len(query.split()))
    if prefix == key:
        return whole
    return max(whole, difflib.SequenceMatcher(None, query, prefix).ratio())


def score_keys(query: str, keys: tuple[str, ...]) -> tuple[tuple[float, str], ...]:
    """
    Takes a normalized query and the dictionary keys.
    Scores every key against the query and keeps the best few.
    Gives (score, key) pairs sorted best first, at most MAX_CANDIDATES long, empty for no keys.
    """
    scored = sorted(((similarity(query, key), key) for key in keys), key=lambda pair: (-pair[0], pair[1]))
    return tuple(scored[:MAX_CANDIDATES])


def quick_candidates(query: str, keys: tuple[str, ...]) -> tuple[str, ...]:
    """
    Takes a normalized query and the dictionary keys.
    Narrows the keys to those difflib considers close by whole string or by leading words.
    Gives the tuple of candidate keys, empty when nothing is close.
    """
    word_count = len(query.split())
    by_prefix: dict[str, list[str]] = {}
    for key in keys:
        by_prefix.setdefault(leading_words(key, word_count), []).append(key)
    close_whole = difflib.get_close_matches(query, keys, n=MAX_CANDIDATES * 4, cutoff=LOCAL_MATCH_THRESHOLD - 0.1)
    close_prefix = difflib.get_close_matches(query, tuple(by_prefix), n=MAX_CANDIDATES * 4, cutoff=LOCAL_MATCH_THRESHOLD - 0.1)
    expanded = [key for prefix in close_prefix for key in by_prefix[prefix]]
    return tuple(dict.fromkeys([*close_whole, *expanded]))


def candidate_sets(dictionary: Mapping[str, Mapping[str, Any]], key: str) -> tuple[tuple[str, ...], ...]:
    """
    Takes the name dictionary and one of its keys.
    Reads the ingredient sets stored under the key.
    Gives a tuple of ingredient-set tuples, empty when the key is unknown.
    """
    entry = dictionary.get(key)
    if entry is None:
        return ()
    return tuple(tuple(ingredients) for ingredients in entry["ingredient_sets"])


def describe_candidate(dictionary: Mapping[str, Mapping[str, Any]], key: str) -> str:
    """
    Takes the name dictionary and one of its keys.
    Formats the key's display name with its ingredient sets.
    Gives a string such as "Adderall → AMPHETAMINE ...".
    """
    sets = " | ".join(", ".join(ingredients) for ingredients in candidate_sets(dictionary, key))
    return f"{dictionary[key]['display']} → {sets}"


def match_name(query_text: str, dictionary: Mapping[str, Mapping[str, Any]]) -> NameMatch:
    """
    Takes a typed drug name and the name dictionary.
    Finds the closest dictionary entry, marking close or multi-set results as needing confirmation.
    Gives a NameMatch with status matched, needs_confirmation, or unresolved and the mapping chain.
    """
    query = normalize_name(query_text)
    if not query:
        return NameMatch(query_text, STATUS_UNRESOLVED, None, (), (query_text,), (), 0.0, "empty name")
    keys = tuple(dictionary)
    exact = candidate_sets(dictionary, query)
    if exact:
        return finish_match(query_text, dictionary, query, 1.0, exact)
    narrowed = quick_candidates(query, keys)
    scored = score_keys(query, narrowed)
    if not scored or scored[0][0] < LOCAL_MATCH_THRESHOLD:
        return NameMatch(query_text, STATUS_UNRESOLVED, None, (), (query_text,), tuple(describe_candidate(dictionary, k) for _, k in scored[:3]), scored[0][0] if scored else 0.0, "no dictionary name is close enough")
    best_score, best_key = scored[0]
    rivals = [key for score, key in scored[1:] if best_score - score <= AMBIGUITY_MARGIN and candidate_sets(dictionary, key) != candidate_sets(dictionary, best_key)]
    if rivals:
        candidates = tuple(describe_candidate(dictionary, k) for k in (best_key, *rivals))
        return NameMatch(query_text, STATUS_NEEDS_CONFIRMATION, None, (), (query_text,), candidates, best_score, "two or more names are equally close")
    return finish_match(query_text, dictionary, best_key, best_score, candidate_sets(dictionary, best_key))


def finish_match(
    query_text: str,
    dictionary: Mapping[str, Mapping[str, Any]],
    key: str,
    score: float,
    sets: tuple[tuple[str, ...], ...],
) -> NameMatch:
    """
    Takes the typed name, the dictionary, the chosen key, its score, and the key's ingredient sets.
    Builds the final match, asking for confirmation when the key maps to more than one ingredient set.
    Gives a NameMatch with status matched or needs_confirmation.
    """
    display = str(dictionary[key]["display"])
    if len(sets) != 1:
        candidates = tuple(f"{display} → {', '.join(ingredients)}" for ingredients in sets)
        return NameMatch(query_text, STATUS_NEEDS_CONFIRMATION, display, (), (query_text, display), candidates, score, "the name is used by more than one ingredient set")
    chain = (query_text, display) if normalize_name(query_text) != key else (query_text,)
    return NameMatch(query_text, STATUS_MATCHED, display, sets[0], (*chain, ", ".join(sets[0])), (), score, "")
