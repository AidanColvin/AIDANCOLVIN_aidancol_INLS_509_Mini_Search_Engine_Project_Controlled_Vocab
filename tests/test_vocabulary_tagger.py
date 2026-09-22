"""Tests for the tagger orchestrator and the Phase 3 acceptance criteria."""

from __future__ import annotations

from typing import Any

from rx_label_search.records import Label
from rx_label_search.text.fields import label_from_record
from rx_label_search.vocabulary.hierarchy import consistency_violations, term_ids
from rx_label_search.vocabulary.tagger import tag_label, tag_record

GAZETTEER: frozenset[str] = frozenset({"mao inhibitors", "ace inhibitor"})


def tagged_ids(record: dict[str, Any]) -> frozenset[str]:
    """
    Takes a raw fixture label record.
    Tags it and reads its term ids.
    Gives the frozenset of term ids the label carries.
    """
    return term_ids(tag_record(record, GAZETTEER).evidence)


def test_oxycontin_carries_the_required_terms(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Tags OxyContin.
    Gives nothing, or fails if it does not carry every term the Phase 3 done criteria list.
    """
    required = {"T01", "T02", "T05", "T07", "T08", "T09", "T10", "T13", "T15"}
    assert required <= tagged_ids(fixture_labels["oxycontin"])


def test_cyclobenzaprine_carries_t14_and_t15(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Tags cyclobenzaprine.
    Gives nothing, or fails if T14 or T15 is missing.
    """
    assert {"T14", "T15"} <= tagged_ids(fixture_labels["cyclobenzaprine"])


def test_gabapentin_carries_t06_but_not_t01(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Tags gabapentin.
    Gives nothing, or fails if T06 is missing or T01 is present.
    """
    ids = tagged_ids(fixture_labels["gabapentin"])
    assert "T06" in ids
    assert "T01" not in ids


def test_entresto_carries_t09_but_not_t08(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Tags Entresto.
    Gives nothing, or fails if T09 is missing or T08 is present.
    """
    ids = tagged_ids(fixture_labels["entresto"])
    assert "T09" in ids
    assert "T08" not in ids


def test_every_fixture_passes_the_consistency_rules(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Tags every fixture and checks the three consistency rules on each.
    Gives nothing, or fails if any fixture violates a rule.
    """
    for name, record in fixture_labels.items():
        record_result = tag_record(record, GAZETTEER)
        assert consistency_violations(record_result.evidence) == (), name


def test_tag_label_stamps_identifiers_and_rule_version() -> None:
    """
    Takes no arguments.
    Tags a minimal label.
    Gives nothing, or fails if the identifiers or rule version are not carried through.
    """
    label = Label("id1", "set1", "3", "20250101", {"boxed_warning": ("Risk of death.",)}, {})
    result = tag_label(label, frozenset())
    assert result.label_id == "id1"
    assert result.set_id == "set1"
    assert result.effective_time == "20250101"
    assert result.rule_version
    assert term_ids(result.evidence) == {"T01"}


def test_tag_record_and_tag_label_agree(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Tags OxyContin through both entry points.
    Gives nothing, or fails if the term ids differ.
    """
    record = fixture_labels["oxycontin"]
    via_record = term_ids(tag_record(record, GAZETTEER).evidence)
    via_label = term_ids(tag_label(label_from_record(record), GAZETTEER).evidence)
    assert via_record == via_label


def test_tag_label_empty_label_gives_no_terms() -> None:
    """
    Takes no arguments.
    Tags a label with no fields at all.
    Gives nothing, or fails if any evidence is returned.
    """
    result = tag_label(Label("i", "s", "1", "20250101", {}, {}), frozenset())
    assert result.evidence == ()
