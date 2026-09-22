"""Pure orchestration of one interaction check: parse, resolve, look up, and flag."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from rx_label_search.interactions.duplicates import build_duplication_flags
from rx_label_search.interactions.groups import build_group_alerts
from rx_label_search.interactions.lookup import find_set_id_for_ingredients
from rx_label_search.interactions.pairs import build_pair_alerts
from rx_label_search.normalize.med_line_parser import parse_med_list
from rx_label_search.normalize.name_matcher import STATUS_MATCHED, STATUS_NEEDS_CONFIRMATION, STATUS_RXNORM, STATUS_UNRESOLVED
from rx_label_search.normalize.rollup import base_ingredients
from rx_label_search.records import Alert, MedEntry, NameMatch

Fetcher = Callable[[str], Any]


def resolve_entry(
    entry: MedEntry,
    dictionary: Mapping[str, Mapping[str, Any]],
    fetch: Fetcher | None,
    summaries: Sequence[Mapping[str, Any]],
    salt_to_base: Mapping[str, Sequence[str]],
) -> NameMatch:
    """
    Takes one parsed medication entry, the name dictionary, an optional RxNorm fetch function, the summaries, and the salt-to-base map.
    Resolves the entry's name text through the local dictionary, then RxNorm if it stays unresolved.
    Gives the NameMatch, unresolved with a reason when the entry has no name text.
    """
    from rx_label_search.normalize.run import resolve_name

    if not entry.name_text:
        return NameMatch(entry.raw_text, STATUS_UNRESOLVED, None, (), (entry.raw_text,), (), 0.0, "no drug name found in entry")
    return resolve_name(entry.name_text, dictionary, fetch, summaries, salt_to_base)


def resolved_drug(
    entry: MedEntry,
    match: NameMatch,
    ingredient_index: Mapping[str, str],
    checker_records: Mapping[str, Mapping[str, Any]],
    salt_to_base: Mapping[str, Sequence[str]],
) -> dict[str, Any] | None:
    """
    Takes one entry, its name match, the ingredient-set index, the checker records, and the salt-to-base map.
    Looks up the matched ingredient set's checker record and attaches its base ingredients.
    Gives a resolved-drug entry with display name, entry, match, and record, or None when the record cannot be found.
    """
    if match.status not in (STATUS_MATCHED, STATUS_RXNORM):
        return None
    set_id = find_set_id_for_ingredients(match.ingredient_set, ingredient_index)
    record = checker_records.get(set_id) if set_id else None
    if record is None:
        return None
    record_with_bases = {**record, "base_ingredients": base_ingredients(match.ingredient_set, salt_to_base)}
    return {"display_name": match.matched_name or entry.name_text, "entry": entry, "match": match, "record": record_with_bases}


def unresolved_reason(entry: MedEntry, match: NameMatch) -> dict[str, Any]:
    """
    Takes one entry and its name match.
    Builds the unresolved-entry report row.
    Gives the dictionary with the raw text, status, reason, and any candidates shown.
    """
    return {"raw_text": entry.raw_text, "status": match.status, "reason": match.reason, "candidates": list(match.candidates)}


def run_interaction_check(
    medication_text: str,
    dictionary: Mapping[str, Mapping[str, Any]],
    fetch: Fetcher | None,
    summaries: Sequence[Mapping[str, Any]],
    salt_to_base: Mapping[str, Sequence[str]],
    ingredient_index: Mapping[str, str],
    checker_records: Mapping[str, Mapping[str, Any]],
    metabolite_reference: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """
    Takes a free-text medication list and every lookup table the checker needs.
    Parses, resolves, and looks up every entry, then builds the group, pair, and duplication alerts.
    Gives a dictionary with parsed_entries, resolved_drugs, unresolved_entries, and alerts.
    """
    entries = parse_med_list(medication_text)
    matches = [resolve_entry(entry, dictionary, fetch, summaries, salt_to_base) for entry in entries]
    resolved = [
        drug
        for entry, match in zip(entries, matches, strict=True)
        if (drug := resolved_drug(entry, match, ingredient_index, checker_records, salt_to_base)) is not None
    ]
    unresolved = [
        unresolved_reason(entry, match)
        for entry, match in zip(entries, matches, strict=True)
        if match.status in (STATUS_UNRESOLVED, STATUS_NEEDS_CONFIRMATION)
    ]
    alerts: tuple[Alert, ...] = (*build_group_alerts(resolved), *build_pair_alerts(resolved), *build_duplication_flags(resolved, metabolite_reference))
    return {"entries": entries, "resolved_drugs": resolved, "unresolved_entries": unresolved, "alerts": alerts}
