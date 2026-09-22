"""Jobs that resolve typed names to ingredient sets and build the base-ingredient map."""

from __future__ import annotations

import difflib
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from rx_label_search.normalize.name_dictionary import normalize_name
from rx_label_search.normalize.name_matcher import STATUS_RXNORM, STATUS_UNRESOLVED, match_name
from rx_label_search.normalize.rollup import sets_with_bases
from rx_label_search.normalize.rxnorm_client import (
    DEFAULT_TIMEOUT_SECONDS,
    MIN_SECONDS_BETWEEN_REQUESTS,
    approximate_term_url,
    fetch_rxnav_json,
    find_rxcui_url,
    history_status_url,
    related_ingredients_url,
)
from rx_label_search.normalize.rxnorm_responses import (
    approximate_candidates,
    history_ingredients,
    related_concepts,
    rxcui_ids,
)
from rx_label_search.records import NameMatch
from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.write_json import write_json

RXNORM_NAME_THRESHOLD = 0.75
BASE_INGREDIENTS_FILE = "base_ingredients.json"
RXNORM_CACHE_FILE = "rxnorm_cache.json"
Fetcher = Callable[[str], Any]


def live_fetcher(timeout: float) -> Fetcher:
    """
    Takes a timeout in seconds.
    Wraps the RxNav fetch with a pause that keeps calls under the NLM rate limit.
    Gives a function from URL to decoded JSON.
    """

    def fetch(url: str) -> Any:
        """
        Takes a full RxNav URL.
        Sleeps for the minimum spacing, then performs the request.
        Gives the decoded JSON.
        """
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
        return fetch_rxnav_json(url, timeout)

    return fetch


def best_rank_one_candidates(candidates: tuple[tuple[str, str, float, int], ...]) -> tuple[tuple[str, str], ...]:
    """
    Takes approximate-match candidates as (rxcui, name, score, rank).
    Keeps the distinct rxcui and name pairs at rank 1.
    Gives the tuple of (rxcui, name) pairs, empty when there is no rank-1 candidate.
    """
    seen: dict[str, str] = {}
    for rxcui, name, _, rank in candidates:
        if rank == 1 and rxcui not in seen:
            seen[rxcui] = name
    return tuple(seen.items())


def rxnorm_ingredient_names(rxcui: str, fetch: Fetcher) -> tuple[str, ...]:
    """
    Takes an RxNorm concept id and a fetch function.
    Reads the concept's ingredient names from the history-status endpoint, which also covers obsolete brands.
    Gives the sorted lowercase ingredient names, empty when RxNorm lists none.
    """
    names = {name.lower() for _, name in history_ingredients(fetch(history_status_url(rxcui)))}
    return tuple(sorted(names))


def resolve_via_rxnorm(
    query_text: str,
    fetch: Fetcher,
    summaries: Iterable[Mapping[str, Any]],
    salt_to_base: Mapping[str, Iterable[str]],
) -> NameMatch:
    """
    Takes a typed name, a fetch function, the collection summaries, and the salt-to-base map.
    Asks RxNorm for the closest concept, its ingredients, and the collection sets with exactly those bases.
    Gives a NameMatch with status matched_via_rxnorm, needs_confirmation, or unresolved and the full chain.
    """
    candidates = best_rank_one_candidates(approximate_candidates(fetch(approximate_term_url(query_text))))
    close = [(rxcui, name) for rxcui, name in candidates if difflib.SequenceMatcher(None, normalize_name(query_text), name.lower()).ratio() >= RXNORM_NAME_THRESHOLD]
    if not close:
        return NameMatch(query_text, STATUS_UNRESOLVED, None, (), (query_text,), tuple(name for _, name in candidates), 0.0, "RxNorm found no close name")
    if len(close) > 1:
        return NameMatch(query_text, "needs_confirmation", None, (), (query_text,), tuple(name for _, name in close), 0.0, "RxNorm returned more than one equally ranked concept")
    rxcui, name = close[0]
    bases = rxnorm_ingredient_names(rxcui, fetch)
    if not bases:
        return NameMatch(query_text, STATUS_UNRESOLVED, name, (), (query_text, name), (), 0.0, "RxNorm lists no ingredient for the matched concept")
    sets = sets_with_bases(summaries, salt_to_base, bases)
    chain = (query_text, name, ", ".join(bases))
    if len(sets) != 1:
        candidates_text = tuple(", ".join(ingredients) for ingredients in sets)
        reason = "no collection label has exactly these ingredients" if not sets else "more than one collection ingredient set matches"
        return NameMatch(query_text, "needs_confirmation" if sets else STATUS_UNRESOLVED, name, (), chain, candidates_text, 0.0, reason)
    return NameMatch(query_text, STATUS_RXNORM, name, sets[0], (*chain, ", ".join(sets[0])), (), 0.0, "matched via RxNorm")


def resolve_name(
    query_text: str,
    dictionary: Mapping[str, Mapping[str, Any]],
    fetch: Fetcher | None,
    summaries: Iterable[Mapping[str, Any]],
    salt_to_base: Mapping[str, Iterable[str]],
) -> NameMatch:
    """
    Takes a typed name, the name dictionary, an optional RxNorm fetch function, the summaries, and the salt-to-base map.
    Tries the local dictionary first and falls back to RxNorm only when the local match is unresolved.
    Gives the NameMatch from whichever step settled it.
    """
    local = match_name(query_text, dictionary)
    if local.status != STATUS_UNRESOLVED or fetch is None or not query_text.strip():
        return local
    return resolve_via_rxnorm(query_text, fetch, summaries, salt_to_base)


def lookup_bases_for_substance(substance: str, fetch: Fetcher) -> dict[str, Any]:
    """
    Takes an openFDA substance name and a fetch function.
    Finds the substance's RxNorm concept and its ingredient (IN) concepts.
    Gives a cache entry with the rxcui found and the ingredient rxcuis and names, empty lists when unknown.
    """
    ids = rxcui_ids(fetch(find_rxcui_url(substance)))
    if not ids:
        return {"rxcui": None, "ingredients": []}
    related = related_concepts(fetch(related_ingredients_url(ids[0])))
    ingredients = [{"rxcui": rxcui, "name": name} for rxcui, name, tty in related if tty == "IN"]
    return {"rxcui": ids[0], "ingredients": ingredients}


def unique_substances(summaries: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    """
    Takes collection summaries.
    Collects every distinct substance name across their ingredient sets.
    Gives the sorted tuple of names, empty for no summaries.
    """
    return tuple(sorted({name for summary in summaries for name in summary["ingredient_set"]}))


def salt_to_base_map(cache: Mapping[str, Mapping[str, Any]]) -> dict[str, list[str]]:
    """
    Takes the RxNorm cache keyed by substance name.
    Reduces each entry to its list of base ingredient names.
    Gives a mapping from substance to base names, omitting substances with no ingredients found.
    """
    return {
        substance: [str(item["name"]) for item in entry.get("ingredients", [])]
        for substance, entry in cache.items()
        if entry.get("ingredients")
    }


def read_cache(path: Path) -> dict[str, Any]:
    """
    Takes the cache file path.
    Reads the cache when it exists.
    Gives the cache mapping, empty when the file is missing.
    """
    if not path.is_file():
        return {}
    return read_json(path)


def build_base_ingredient_map(build_dir: Path, fetch: Fetcher, fetch_date: str) -> dict[str, list[str]]:
    """
    Takes the build directory, a fetch function, and the fetch date.
    Looks up every substance in the collection summaries through RxNorm, reusing cached entries, and writes both files.
    Gives the salt-to-base map that was written.
    """
    summaries = read_json(build_dir / "collection_summaries.json")
    cache_path = build_dir / RXNORM_CACHE_FILE
    cache = read_cache(cache_path)
    for index, substance in enumerate(unique_substances(summaries)):
        if substance in cache:
            continue
        cache[substance] = {**lookup_bases_for_substance(substance, fetch), "fetched_on": fetch_date}
        if index % 100 == 0:
            write_json(cache_path, cache)
    write_json(cache_path, cache)
    mapping = salt_to_base_map(cache)
    write_json(build_dir / BASE_INGREDIENTS_FILE, mapping)
    return mapping


def default_fetcher() -> Fetcher:
    """
    Takes no arguments.
    Builds the live rate-limited RxNav fetcher with the default timeout.
    Gives the fetch function.
    """
    return live_fetcher(DEFAULT_TIMEOUT_SECONDS)
