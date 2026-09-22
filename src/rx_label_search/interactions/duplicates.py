"""Pure duplication-flag detection: shared base ingredients or a cited active-metabolite pair."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rx_label_search.normalize.rollup import metabolite_links, shared_bases
from rx_label_search.records import Alert, AlertEvidence


def base_alert_member(drug: Mapping[str, Any]) -> AlertEvidence:
    """
    Takes one resolved drug's entry.
    Builds its AlertEvidence with the shared base ingredients as the sentence.
    Gives the AlertEvidence, with an empty section since a duplication flag cites no label sentence.
    """
    record = drug["record"]
    return AlertEvidence(
        drug_name=drug["display_name"],
        set_id=record["set_id"],
        effective_time=record["effective_time"],
        section="",
        sentence=f"base ingredients: {', '.join(record.get('base_ingredients', ()))}",
        dailymed_url=f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={record['set_id']}",
    )


def build_base_ingredient_flag(first: Mapping[str, Any], second: Mapping[str, Any]) -> Alert | None:
    """
    Takes two resolved drugs.
    Checks whether their base ingredients overlap.
    Gives the duplication Alert, or None when they share no base ingredient.
    """
    shared = shared_bases(first["record"].get("base_ingredients", ()), second["record"].get("base_ingredients", ()))
    if not shared:
        return None
    return Alert(
        kind="duplication",
        risk="shared_ingredient",
        title=f"{first['display_name']} and {second['display_name']} share {', '.join(shared)}",
        tier=None,
        tier_name="heuristic",
        members=(base_alert_member(first), base_alert_member(second)),
        note="",
    )


def build_metabolite_flag(first: Mapping[str, Any], second: Mapping[str, Any], reference: Sequence[Mapping[str, Any]]) -> Alert | None:
    """
    Takes two resolved drugs and the cited active-metabolite reference entries.
    Checks whether a cited pair links their base ingredients.
    Gives the duplication Alert citing the reference sentence, or None when no cited pair links them.
    """
    links = metabolite_links(first["record"].get("base_ingredients", ()), second["record"].get("base_ingredients", ()), reference)
    if not links:
        return None
    link = links[0]
    members = (
        AlertEvidence(first["display_name"], first["record"]["set_id"], first["record"]["effective_time"], link["field"], link["sentence"], f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={link['set_id']}"),
        base_alert_member(second),
    )
    return Alert(
        kind="duplication",
        risk="active_metabolite",
        title=f"{first['display_name']} and {second['display_name']} are an active-metabolite pair",
        tier=None,
        tier_name="heuristic",
        members=members,
        note=f"cited from {link['source_url']}",
    )


def build_duplication_flags(drugs: Sequence[Mapping[str, Any]], metabolite_reference: Sequence[Mapping[str, Any]]) -> tuple[Alert, ...]:
    """
    Takes the resolved drugs on a medication list and the cited active-metabolite reference entries.
    Checks every pair for shared base ingredients or a cited metabolite relationship.
    Gives the tuple of duplication flags, empty when no pair qualifies.
    """
    flags: list[Alert] = []
    for i, first in enumerate(drugs):
        for second in drugs[i + 1 :]:
            base_flag = build_base_ingredient_flag(first, second)
            if base_flag is not None:
                flags.append(base_flag)
                continue
            metabolite_flag = build_metabolite_flag(first, second, metabolite_reference)
            if metabolite_flag is not None:
                flags.append(metabolite_flag)
    return tuple(flags)
