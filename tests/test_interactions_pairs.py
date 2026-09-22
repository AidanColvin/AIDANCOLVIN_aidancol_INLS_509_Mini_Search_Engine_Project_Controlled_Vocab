"""Tests for pair-alert detection."""

from __future__ import annotations

from typing import Any

from rx_label_search.interactions.pairs import build_pair_alert, build_pair_alerts, drug_own_names, sentence_mentions_drug, t17_evidence


def drug(name: str, record_extra: dict[str, Any]) -> dict[str, Any]:
    """
    Takes a display name and extra checker-record fields.
    Builds a minimal resolved-drug entry for pair-alert tests.
    Gives the dictionary.
    """
    base = {"set_id": f"s-{name}", "effective_time": "20250101", "evidence": [], "brand_names": [], "generic_names": [], "ingredient_set": [], "base_ingredients": []}
    return {"display_name": name, "record": {**base, **record_extra}}


def test_drug_own_names_includes_base_ingredients() -> None:
    """
    Takes no arguments.
    Reads own names from a drug whose base ingredient differs from its openfda names.
    Gives nothing, or fails if the base ingredient is missing.
    """
    other = drug("x", {"generic_names": ["Fluvoxamine Maleate"], "base_ingredients": ["fluvoxamine"]})
    assert "fluvoxamine" in drug_own_names(other)
    assert "fluvoxamine maleate" in drug_own_names(other)


def test_sentence_mentions_drug_by_name_and_by_class() -> None:
    """
    Takes no arguments.
    Checks a sentence naming the drug's base ingredient and one naming its pharm class.
    Gives nothing, or fails if either case is missed.
    """
    by_name = drug("x", {"base_ingredients": ["fluvoxamine"]})
    assert sentence_mentions_drug("must not be taken with fluvoxamine", by_name)
    by_class = drug("y", {"pharm_class_epc": ["Strong CYP3A4 Inhibitor"]})
    assert sentence_mentions_drug("contraindicated with strong cyp3a4 inhibitor drugs", by_class)
    assert not sentence_mentions_drug("contraindicated in pregnancy", by_name)


def test_t17_evidence_finds_the_right_row_or_none() -> None:
    """
    Takes no arguments.
    Reads T17 evidence from a record that has one and one that does not.
    Gives nothing, or fails if either result is wrong.
    """
    with_t17 = drug("x", {"evidence": [{"term_id": "T17", "field_name": "contraindications", "sentence": "s", "rule_version": "v"}]})
    without = drug("y", {"evidence": []})
    assert t17_evidence(with_t17) is not None
    assert t17_evidence(without) is None


def test_build_pair_alert_fires_and_skips() -> None:
    """
    Takes no arguments.
    Builds a pair alert for a matching pair and checks a non-matching pair gives none.
    Gives nothing, or fails if either result is wrong.
    """
    source = drug("A", {"evidence": [{"term_id": "T17", "field_name": "contraindications", "sentence": "must not be taken with fluvoxamine", "rule_version": "v"}]})
    other = drug("B", {"base_ingredients": ["fluvoxamine"]})
    alert = build_pair_alert(source, other)
    assert alert is not None
    assert alert.risk == "T17"
    unrelated = drug("C", {"base_ingredients": ["ibuprofen"]})
    assert build_pair_alert(source, unrelated) is None


def test_build_pair_alerts_checks_every_direction() -> None:
    """
    Takes no arguments.
    Builds pair alerts across a three-drug list where only one pairing matches.
    Gives nothing, or fails if the count is wrong.
    """
    source = drug("A", {"evidence": [{"term_id": "T17", "field_name": "contraindications", "sentence": "must not be taken with fluvoxamine", "rule_version": "v"}]})
    match = drug("B", {"base_ingredients": ["fluvoxamine"]})
    unrelated = drug("C", {"base_ingredients": ["ibuprofen"]})
    alerts = build_pair_alerts([source, match, unrelated])
    assert len(alerts) == 1
    assert build_pair_alerts([]) == ()
