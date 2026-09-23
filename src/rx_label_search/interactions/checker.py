"""Pure orchestration of one interaction check: parse, resolve, look up, and flag."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from rx_label_search.interactions.duplicates import build_duplication_flags
from rx_label_search.interactions.groups import build_group_alerts
from rx_label_search.interactions.knowledge import Knowledge, grade_duplicates, knowledge_alerts, merge_label_alerts
from rx_label_search.interactions.lookup import find_set_id_for_ingredients
from rx_label_search.interactions.pairs import build_pair_alerts
from rx_label_search.interactions.totals import molecule_totals
from rx_label_search.normalize.med_line_parser import parse_med_list
from rx_label_search.normalize.name_matcher import STATUS_MATCHED, STATUS_NEEDS_CONFIRMATION, STATUS_RXNORM, STATUS_UNRESOLVED
from rx_label_search.normalize.rollup import base_ingredients, base_names_for, sets_with_bases
from rx_label_search.records import Alert, MedEntry, NameMatch

Fetcher = Callable[[str], Any]
STATUS_INGREDIENT_ONLY = "matched_ingredient_only"


def written_bases(entry: MedEntry, salt_to_base: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    """
    Takes one entry whose generic was written out, such as "divalproex sodium" or "hydrocodone/acetaminophen", and the salt-to-base map.
    Rolls each written component up to its base ingredient, keeping a component that is already a base name as written.
    Gives the sorted base names, empty when the entry names no generic.
    """
    bases: set[str] = set()
    for component in entry.components:
        bases.update(base_names_for(component.upper(), salt_to_base))
    return tuple(sorted(bases))


def resolve_written_generic(entry: MedEntry, summaries: Sequence[Mapping[str, Any]], salt_to_base: Mapping[str, Sequence[str]]) -> NameMatch | None:
    """
    Takes one entry, the collection summaries, and the salt-to-base map.
    Finds the collection labels whose ingredients roll up to exactly the written generic's base ingredients, preferring the plainest salt form when several do.
    Gives a matched NameMatch, or None when the entry names no generic or no label has exactly those ingredients.
    """
    from rx_label_search.normalize.run import preferred_same_molecule_set

    bases = written_bases(entry, salt_to_base)
    if not bases:
        return None
    sets = sets_with_bases(summaries, salt_to_base, bases)
    if not sets:
        return None
    chosen = sets[0] if len(sets) == 1 else closest_written_set(entry, sets, summaries) or preferred_same_molecule_set(sets, salt_to_base)
    return NameMatch(entry.name_text, STATUS_MATCHED, entry.name_text, chosen, (entry.raw_text, entry.name_text, ", ".join(chosen)), (), 1.0, "the written generic's ingredients match this label exactly")


def closest_written_set(entry: MedEntry, sets: tuple[tuple[str, ...], ...], summaries: Sequence[Mapping[str, Any]]) -> tuple[str, ...] | None:
    """
    Takes one entry and several same-molecule ingredient sets that fit its written generic, plus the collection summaries.
    Prefers the set whose label carries the typed brand, then the set whose salt words were written (such as "propionate" or "succinate").
    Gives the preferred set, or None when neither the brand nor the written words single one out.
    """
    brand = (entry.brand_text or "").lower()
    if brand:
        branded = [ingredient_set for ingredient_set in sets if any(tuple(summary["ingredient_set"]) == ingredient_set and brand in " ".join(summary.get("brand_names", ())).lower() for summary in summaries)]
        if len(branded) == 1:
            return branded[0]
    written = set(" ".join(entry.components).lower().split())
    scored = sorted(((len(written & set(" ".join(ingredient_set).lower().split())), ingredient_set) for ingredient_set in sets), key=lambda pair: -pair[0])
    if len(scored) > 1 and scored[0][0] > scored[1][0]:
        return scored[0][1]
    return None


def known_base_names(salt_to_base: Mapping[str, Sequence[str]]) -> frozenset[str]:
    """
    Takes the salt-to-base map.
    Collects every base ingredient name it knows, from RxNorm.
    Gives the lowercase names.
    """
    return frozenset(base.lower() for bases in salt_to_base.values() for base in bases)


def resolve_ingredient_only(entry: MedEntry, fetch: Fetcher | None, salt_to_base: Mapping[str, Sequence[str]]) -> NameMatch | None:
    """
    Takes one entry whose written generic matched no collection label, an optional RxNorm fetch function, and the salt-to-base map.
    Accepts the written ingredients when each is a base name RxNorm already gave the collection or an exact RxNorm concept name, so an OTC drug such as aspirin still takes part in the class rules.
    Gives an ingredient-only NameMatch, or None when any component cannot be confirmed.
    """
    from rx_label_search.normalize.run import rxnorm_has_exact_name

    bases = written_bases(entry, salt_to_base)
    if not bases:
        return None
    known = known_base_names(salt_to_base)
    for base in bases:
        if base in known:
            continue
        if fetch is None or not rxnorm_has_exact_name(base, fetch):
            return None
    reason = "no FDA label in this collection has exactly these ingredients; the written generic was confirmed as an ingredient name"
    return NameMatch(entry.name_text, STATUS_INGREDIENT_ONLY, entry.name_text, tuple(base.upper() for base in bases), (entry.raw_text, entry.name_text), (), 1.0, reason)


def name_queries(entry: MedEntry) -> tuple[str, ...]:
    """
    Takes one parsed medication entry.
    Lists the names worth trying, most specific first: the generic written in parentheses, then the brand, then brand and generic together.
    Gives the distinct non-empty names in that order, empty when the entry has no name text at all.
    """
    brand = entry.brand_text or ""
    queries = (entry.name_text, brand, f"{brand} {' / '.join(entry.components)}".strip() if brand and entry.components else "")
    seen: list[str] = []
    for query in queries:
        if query and query.lower() not in (item.lower() for item in seen):
            seen.append(query)
    return tuple(seen)


def fits_components(entry: MedEntry, match: NameMatch, salt_to_base: Mapping[str, Sequence[str]]) -> bool:
    """
    Takes one entry, a resolved name match, and the salt-to-base map.
    Checks that a combination written as "a/b" resolved to a product with at least that many base ingredients, and a single generic to a single-ingredient product.
    Gives True when the match fits the written components or the entry names no components.
    """
    if not entry.components:
        return True
    bases = base_ingredients(match.ingredient_set, salt_to_base)
    if len(entry.components) > 1:
        return len(bases) >= len(entry.components)
    return len(bases) == 1


def resolve_entry(
    entry: MedEntry,
    dictionary: Mapping[str, Mapping[str, Any]],
    fetch: Fetcher | None,
    summaries: Sequence[Mapping[str, Any]],
    salt_to_base: Mapping[str, Sequence[str]],
) -> NameMatch:
    """
    Takes one parsed medication entry, the name dictionary, an optional RxNorm fetch function, the summaries, and the salt-to-base map.
    Resolves the entry's generic, then its brand, then both together, through the local dictionary and then RxNorm, keeping the first match whose ingredients fit what was written.
    Gives the NameMatch, unresolved with a reason when the entry has no name text, or the first attempt's result when no name resolves.
    """
    from rx_label_search.normalize.run import resolve_name

    queries = name_queries(entry)
    if not queries:
        return NameMatch(entry.raw_text, STATUS_UNRESOLVED, None, (), (entry.raw_text,), (), 0.0, "no drug name found in entry")
    written = resolve_written_generic(entry, summaries, salt_to_base)
    if written is not None:
        return written
    first: NameMatch | None = None
    for query in queries:
        match = resolve_name(query, dictionary, fetch, summaries, salt_to_base)
        first = first or match
        if match.status in (STATUS_MATCHED, STATUS_RXNORM) and fits_components(entry, match, salt_to_base):
            return match
    ingredient_only = resolve_ingredient_only(entry, fetch, salt_to_base)
    if ingredient_only is not None:
        return ingredient_only
    return first or NameMatch(entry.raw_text, STATUS_UNRESOLVED, None, (), (entry.raw_text,), (), 0.0, "no drug name found in entry")


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
    if match.status == STATUS_INGREDIENT_ONLY:
        return {"display_name": entry.brand_text or entry.name_text, "entry": entry, "match": match, "record": ingredient_only_record(entry, match)}
    if match.status not in (STATUS_MATCHED, STATUS_RXNORM):
        return None
    set_id = find_set_id_for_ingredients(match.ingredient_set, ingredient_index)
    record = checker_records.get(set_id) if set_id else None
    if record is None:
        return None
    record_with_bases = {**record, "base_ingredients": base_ingredients(match.ingredient_set, salt_to_base)}
    return {"display_name": entry.brand_text or match.matched_name or entry.name_text, "entry": entry, "match": match, "record": record_with_bases}


def ingredient_only_record(entry: MedEntry, match: NameMatch) -> dict[str, Any]:
    """
    Takes one entry resolved to ingredients only and its match.
    Builds a checker record with the ingredients but no label, no set id, and no label evidence.
    Gives the record dictionary, marked with no_label so the report can say the label is not in the collection.
    """
    bases = tuple(name.lower() for name in match.ingredient_set)
    return {
        "set_id": "",
        "effective_time": "",
        "brand_names": [entry.brand_text] if entry.brand_text else [],
        "generic_names": [entry.name_text],
        "ingredient_set": list(match.ingredient_set),
        "route": [],
        "pharm_class_epc": [],
        "schedule": None,
        "evidence": [],
        "base_ingredients": bases,
        "no_label": True,
    }


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
    knowledge: Knowledge | None = None,
    rule_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Takes a free-text medication list, every lookup table the checker needs, and optionally the class-rule knowledge table with its label-evidence index.
    Parses, resolves, and looks up every entry, adds up each ingredient, then builds the class-rule, label, and duplication alerts and merges the label alerts into the rules that cover them.
    Gives a dictionary with entries, resolved_drugs, unresolved_entries, alerts, and molecule_totals.
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
    label_alerts = (*build_group_alerts(resolved), *build_pair_alerts(resolved))
    duplicates = build_duplication_flags(resolved, metabolite_reference)
    if knowledge is None:
        return {"entries": entries, "resolved_drugs": resolved, "unresolved_entries": unresolved, "alerts": (*label_alerts, *duplicates), "molecule_totals": []}
    totals = molecule_totals(resolved, knowledge.mme_factors)
    rules = knowledge_alerts(resolved, knowledge, rule_evidence or {}, totals)
    alerts: tuple[Alert, ...] = (*merge_label_alerts(rules, label_alerts, resolved), *grade_duplicates(duplicates, resolved, knowledge, totals))
    return {"entries": entries, "resolved_drugs": resolved, "unresolved_entries": unresolved, "alerts": alerts, "molecule_totals": totals}
