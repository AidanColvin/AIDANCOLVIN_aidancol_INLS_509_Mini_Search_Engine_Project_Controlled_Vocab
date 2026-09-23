"""Jobs that resolve typed names to ingredient sets and build the base-ingredient map."""

from __future__ import annotations

import dataclasses
import difflib
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from rx_label_search.normalize.name_dictionary import normalize_name
from rx_label_search.normalize.name_matcher import STATUS_MATCHED, STATUS_NEEDS_CONFIRMATION, STATUS_RXNORM, STATUS_UNRESOLVED, candidate_sets, match_name
from rx_label_search.normalize.rollup import base_ingredients, base_names_for, sets_with_bases
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
SAME_MOLECULE_REASON = "the name is used by more than one ingredient set"
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


def salted_member_count(ingredient_set: tuple[str, ...], salt_to_base: Mapping[str, Iterable[str]]) -> int:
    """
    Takes one ingredient set and the salt-to-base map.
    Counts the members whose base rollup is not simply the member's own name, meaning the member is a salt or ester form.
    Gives the count, zero when every member is already a base ingredient name.
    """
    return sum(base_names_for(member, salt_to_base) != (member.lower(),) for member in ingredient_set)


def preferred_same_molecule_set(sets: tuple[tuple[str, ...], ...], salt_to_base: Mapping[str, Iterable[str]]) -> tuple[str, ...]:
    """
    Takes two or more ingredient sets that roll up to the same base ingredients, and the salt-to-base map.
    Picks the one with the fewest members, then the fewest salt forms, then the alphabetically first, so "ONDANSETRON" wins over "ONDANSETRON HYDROCHLORIDE" and a single salt wins over a two-salt mixture.
    Gives the chosen ingredient set, or raises ValueError when no sets are given.
    """
    if not sets:
        raise ValueError("no ingredient sets to choose from")
    return min(sets, key=lambda ingredient_set: (len(ingredient_set), salted_member_count(ingredient_set, salt_to_base), tuple(ingredient_set)))


def same_molecule(sets: tuple[tuple[str, ...], ...], salt_to_base: Mapping[str, Iterable[str]]) -> bool:
    """
    Takes two or more ingredient sets and the salt-to-base map.
    Checks whether every set rolls up to exactly the same base ingredients.
    Gives True when they are all one molecule (or one fixed combination) in different salt forms, False otherwise or for fewer than two sets.
    """
    if len(sets) < 2:
        return False
    rollups = {base_ingredients(ingredient_set, salt_to_base) for ingredient_set in sets}
    return len(rollups) == 1


def settle_same_molecule_match(local: NameMatch, dictionary: Mapping[str, Mapping[str, Any]], salt_to_base: Mapping[str, Iterable[str]]) -> NameMatch:
    """
    Takes a local match that needs confirmation because its name is used by several ingredient sets, the dictionary, and the salt-to-base map.
    Settles it on the preferred set when every candidate set is the same molecule in a different salt form, since the choice cannot change which drug was meant.
    Gives the settled matched NameMatch, or the original match when the sets are genuinely different drugs or the match is not this kind of confirmation.
    """
    if local.status != STATUS_NEEDS_CONFIRMATION or local.reason != SAME_MOLECULE_REASON or local.matched_name is None:
        return local
    sets = candidate_sets(dictionary, normalize_name(local.matched_name))
    if not same_molecule(sets, salt_to_base):
        return local
    chosen = preferred_same_molecule_set(sets, salt_to_base)
    reason = f"same molecule in {len(sets)} salt forms; chose {', '.join(chosen)}"
    return NameMatch(local.query, STATUS_MATCHED, local.matched_name, chosen, (*local.chain, ", ".join(chosen)), (), local.score, reason)


def resolve_via_rxnorm(
    query_text: str,
    fetch: Fetcher,
    summaries: Iterable[Mapping[str, Any]],
    salt_to_base: Mapping[str, Iterable[str]],
) -> NameMatch:
    """
    Takes a typed name, a fetch function, the collection summaries, and the salt-to-base map.
    Asks RxNorm for the closest concept, its ingredients, and the collection sets with exactly those bases, settling on the preferred salt form when several sets are the same molecule.
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
    if not sets:
        return NameMatch(query_text, STATUS_UNRESOLVED, name, (), chain, (), 0.0, "no collection label has exactly these ingredients")
    chosen = sets[0] if len(sets) == 1 else preferred_same_molecule_set(sets, salt_to_base)
    reason = "matched via RxNorm" if len(sets) == 1 else f"matched via RxNorm; same molecule in {len(sets)} salt forms, chose {', '.join(chosen)}"
    return NameMatch(query_text, STATUS_RXNORM, name, chosen, (*chain, ", ".join(chosen)), (), 0.0, reason)


def rxnorm_has_exact_name(query_text: str, fetch: Fetcher) -> bool:
    """
    Takes the typed name and a fetch function.
    Asks RxNorm's approximate-term endpoint whether a rank-1 candidate's name equals the typed name after normalization.
    Gives True for an exact name, False when every candidate is merely close or there are none.
    """
    candidates = best_rank_one_candidates(approximate_candidates(fetch(approximate_term_url(query_text))))
    return any(normalize_name(candidate_name) == normalize_name(query_text) for _, candidate_name in candidates)


def prefer_exact_rxnorm_name(local: NameMatch, query_text: str, fetch: Fetcher, summaries: Iterable[Mapping[str, Any]], salt_to_base: Mapping[str, Iterable[str]]) -> NameMatch:
    """
    Takes a fuzzy local match, the typed name, the fetch function, the summaries, and the salt-to-base map.
    Checks RxNorm for the typed name as an exact concept name and, when it is one that resolves to a collection label, prefers that over the local guess, so "Coumadin" is not read as the homeopathic "COUMARIN".
    Gives the RxNorm match with its reason extended, or the local match when RxNorm has no exact name or no collection label for it.
    """
    if not rxnorm_has_exact_name(query_text, fetch):
        return local
    via_rxnorm = resolve_via_rxnorm(query_text, fetch, summaries, salt_to_base)
    if via_rxnorm.status != STATUS_RXNORM:
        return local
    return dataclasses.replace(via_rxnorm, reason=f"{via_rxnorm.reason}; exact RxNorm name preferred over the fuzzy local match {local.matched_name}")


def resolve_name(
    query_text: str,
    dictionary: Mapping[str, Mapping[str, Any]],
    fetch: Fetcher | None,
    summaries: Iterable[Mapping[str, Any]],
    salt_to_base: Mapping[str, Iterable[str]],
) -> NameMatch:
    """
    Takes a typed name, the name dictionary, an optional RxNorm fetch function, the summaries, and the salt-to-base map.
    Tries the local dictionary first, settling a same-molecule salt ambiguity on the spot, checks RxNorm for an exact name when the local match was only fuzzy, and otherwise falls back to RxNorm only when the local match is unresolved.
    Gives the NameMatch from whichever step settled it.
    """
    local = settle_same_molecule_match(match_name(query_text, dictionary), dictionary, salt_to_base)
    if fetch is None or not query_text.strip():
        return local
    if local.status == STATUS_MATCHED and local.score < 1.0:
        return prefer_exact_rxnorm_name(local, query_text, fetch, summaries, salt_to_base)
    if local.status != STATUS_UNRESOLVED:
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
