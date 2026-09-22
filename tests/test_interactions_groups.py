"""Tests for group-alert detection."""

from __future__ import annotations

from typing import Any

from rx_label_search.interactions.groups import build_group_alert, build_group_alerts, drugs_sharing_term


def drug(name: str, term_ids: tuple[str, ...], field: str = "warnings") -> dict[str, Any]:
    """
    Takes a display name and the term ids to give it.
    Builds a minimal resolved-drug entry for group-alert tests.
    Gives the dictionary.
    """
    evidence = [{"term_id": term_id, "field_name": field, "sentence": f"{term_id} risk.", "rule_version": "v"} for term_id in term_ids]
    return {"display_name": name, "record": {"set_id": f"s-{name}", "effective_time": "20250101", "evidence": evidence}}


def test_drugs_sharing_term_filters_correctly() -> None:
    """
    Takes no arguments.
    Filters three drugs for a term two of them carry.
    Gives nothing, or fails if the wrong drugs are returned.
    """
    drugs = [drug("a", ("T14",)), drug("b", ("T15",)), drug("c", ("T14", "T15"))]
    assert [d["display_name"] for d in drugs_sharing_term(drugs, "T14")] == ["a", "c"]


def test_build_group_alert_requires_at_least_two() -> None:
    """
    Takes no arguments.
    Builds a group alert for a term only one drug carries and one two drugs carry.
    Gives nothing, or fails if either result is wrong.
    """
    drugs = [drug("a", ("T14",)), drug("b", ("T15",))]
    assert build_group_alert(drugs, "T14") is None
    drugs = [drug("a", ("T14",)), drug("b", ("T14",))]
    alert = build_group_alert(drugs, "T14")
    assert alert is not None
    assert len(alert.members) == 2
    assert alert.tier_name.endswith("(heuristic)")


def test_build_group_alerts_covers_all_three_risk_types() -> None:
    """
    Takes no arguments.
    Builds group alerts for a list sharing all three group risk terms.
    Gives nothing, or fails if fewer than three alerts are returned.
    """
    drugs = [drug("a", ("T14", "T15", "T16")), drug("b", ("T14", "T15", "T16"))]
    alerts = build_group_alerts(drugs)
    assert {alert.risk for alert in alerts} == {"T14", "T15", "T16"}


def test_build_group_alerts_empty_list() -> None:
    """
    Takes no arguments.
    Builds group alerts for an empty drug list.
    Gives nothing, or fails if any alert is returned.
    """
    assert build_group_alerts([]) == ()
