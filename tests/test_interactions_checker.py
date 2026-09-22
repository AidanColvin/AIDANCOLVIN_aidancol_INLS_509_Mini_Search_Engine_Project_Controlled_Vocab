"""Tests for the checker orchestration, including unresolved entries and identifiers."""

from __future__ import annotations

from typing import Any

from rx_label_search.interactions.checker import resolve_entry, resolved_drug, run_interaction_check, unresolved_reason
from rx_label_search.normalize.med_line_parser import parse_entry
from rx_label_search.normalize.name_matcher import STATUS_MATCHED, STATUS_UNRESOLVED

DICTIONARY: dict[str, dict[str, Any]] = {"aspirin": {"display": "Aspirin", "kinds": ["generic"], "ingredient_sets": [["ASPIRIN"]]}}
INDEX = {"ASPIRIN": "set-aspirin"}
RECORDS = {"set-aspirin": {"set_id": "set-aspirin", "effective_time": "20250101", "evidence": [], "brand_names": [], "generic_names": ["ASPIRIN"], "ingredient_set": ["ASPIRIN"]}}


def test_resolve_entry_empty_name_is_unresolved() -> None:
    """
    Takes no arguments.
    Resolves an entry whose name text is empty.
    Gives nothing, or fails if the status is not unresolved.
    """
    entry = parse_entry("10 mg")
    assert resolve_entry(entry, DICTIONARY, None, [], {}).status == STATUS_UNRESOLVED


def test_resolve_entry_matches_the_dictionary() -> None:
    """
    Takes no arguments.
    Resolves an entry naming a drug the dictionary knows.
    Gives nothing, or fails if the status is not matched.
    """
    entry = parse_entry("aspirin 81 mg daily")
    assert resolve_entry(entry, DICTIONARY, None, [], {}).status == STATUS_MATCHED


def test_resolved_drug_looks_up_the_checker_record() -> None:
    """
    Takes no arguments.
    Builds a resolved drug for a matched entry and one whose ingredient set has no checker record.
    Gives nothing, or fails if either result is wrong.
    """
    entry = parse_entry("aspirin 81 mg daily")
    match = resolve_entry(entry, DICTIONARY, None, [], {})
    drug = resolved_drug(entry, match, INDEX, RECORDS, {})
    assert drug is not None
    assert drug["record"]["set_id"] == "set-aspirin"
    assert resolved_drug(entry, match, {}, {}, {}) is None


def test_unresolved_reason_shape() -> None:
    """
    Takes no arguments.
    Builds the unresolved-entry row for an unresolved match.
    Gives nothing, or fails if any field is missing.
    """
    entry = parse_entry("qwxzvbn 10 mg")
    match = resolve_entry(entry, DICTIONARY, None, [], {})
    row = unresolved_reason(entry, match)
    assert row["raw_text"] == entry.raw_text
    assert row["status"] == STATUS_UNRESOLVED


def test_run_interaction_check_handles_empty_input() -> None:
    """
    Takes no arguments.
    Runs the checker on a blank medication list.
    Gives nothing, or fails if any of the four result keys are non-empty.
    """
    result = run_interaction_check("", DICTIONARY, None, [], {}, INDEX, RECORDS, [])
    assert result["entries"] == ()
    assert result["resolved_drugs"] == []
    assert result["unresolved_entries"] == []
    assert result["alerts"] == ()


def test_run_interaction_check_resolves_a_known_drug() -> None:
    """
    Takes no arguments.
    Runs the checker on one entry the dictionary knows.
    Gives nothing, or fails if it is not resolved and unresolved_entries is not empty.
    """
    result = run_interaction_check("aspirin 81 mg daily", DICTIONARY, None, [], {}, INDEX, RECORDS, [])
    assert len(result["resolved_drugs"]) == 1
    assert result["unresolved_entries"] == []
