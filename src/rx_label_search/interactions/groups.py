"""Pure group-alert detection: two or more listed drugs sharing one interaction-risk term."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rx_label_search.interactions.evidence import evidence_for_term, term_display_name
from rx_label_search.interactions.tiers import highest_tier, tier_for_field, tier_name as lookup_tier_name
from rx_label_search.records import Alert, AlertEvidence, TermEvidence

GROUP_RISK_TERMS = ("T14", "T15", "T16")


def term_evidence_from_json(evidence_rows: Sequence[Mapping[str, Any]]) -> tuple[TermEvidence, ...]:
    """
    Takes a checker record's evidence rows.
    Converts them to TermEvidence records.
    Gives the tuple, empty for no rows.
    """
    return tuple(TermEvidence(row["term_id"], row["field_name"], row["sentence"], row["rule_version"]) for row in evidence_rows)


def drugs_sharing_term(drugs: Sequence[Mapping[str, Any]], term_id: str) -> list[Mapping[str, Any]]:
    """
    Takes the resolved drugs on a medication list and one interaction-risk term id.
    Finds every drug whose checker record carries that term.
    Gives the list of matching drug entries, empty when fewer than one carries it.
    """
    return [drug for drug in drugs if any(row["term_id"] == term_id for row in drug["record"]["evidence"])]


def alert_member(drug: Mapping[str, Any], term_id: str) -> AlertEvidence:
    """
    Takes one resolved drug and the term id its group alert is about.
    Builds its AlertEvidence from that term's first evidence row.
    Gives the AlertEvidence.
    """
    record = drug["record"]
    evidence = next(TermEvidence(row["term_id"], row["field_name"], row["sentence"], row["rule_version"]) for row in record["evidence"] if row["term_id"] == term_id)
    return evidence_for_term(drug["display_name"], record["set_id"], record["effective_time"], evidence)


def build_group_alert(drugs: Sequence[Mapping[str, Any]], term_id: str) -> Alert | None:
    """
    Takes the resolved drugs on a medication list and one interaction-risk term id.
    Builds one group alert when two or more drugs share the term.
    Gives the Alert, or None when fewer than two drugs share it.
    """
    sharing = drugs_sharing_term(drugs, term_id)
    if len(sharing) < 2:
        return None
    members = tuple(alert_member(drug, term_id) for drug in sharing)
    tiers = tuple(tier_for_field(member.section) for member in members)
    tier = highest_tier(tiers)
    name = term_display_name(term_id)
    return Alert(
        kind="group",
        risk=term_id,
        title=f"{name} shared by {len(members)} drugs",
        tier=tier,
        tier_name=f"{lookup_tier_name(tier)} (heuristic)",
        members=members,
        note="",
    )


def build_group_alerts(drugs: Sequence[Mapping[str, Any]]) -> tuple[Alert, ...]:
    """
    Takes the resolved drugs on a medication list.
    Builds one group alert per shared interaction-risk type among T14, T15, and T16.
    Gives the tuple of alerts, empty when no risk type is shared by two or more drugs.
    """
    return tuple(alert for term_id in GROUP_RISK_TERMS if (alert := build_group_alert(drugs, term_id)) is not None)
