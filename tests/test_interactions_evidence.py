"""Tests for DailyMed link building and evidence assembly."""

from __future__ import annotations

from rx_label_search.interactions.evidence import dailymed_url, evidence_for_term, term_display_name
from rx_label_search.records import TermEvidence


def test_dailymed_url_uses_the_verified_pattern() -> None:
    """
    Takes no arguments.
    Builds the URL for a sample set id.
    Gives nothing, or fails if the URL does not match the verified pattern.
    """
    assert dailymed_url("abc-123") == "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=abc-123"


def test_evidence_for_term_builds_the_full_record() -> None:
    """
    Takes no arguments.
    Builds an AlertEvidence from a drug name and a TermEvidence.
    Gives nothing, or fails if any field is wrong.
    """
    evidence = evidence_for_term("Trazodone", "s1", "20250101", TermEvidence("T14", "warnings", "Serotonin syndrome.", "v1"))
    assert evidence.drug_name == "Trazodone"
    assert evidence.section == "warnings"
    assert evidence.sentence == "Serotonin syndrome."
    assert evidence.dailymed_url.endswith("s1")


def test_term_display_name_known_and_unknown() -> None:
    """
    Takes no arguments.
    Reads the display name for a known term and an unknown id.
    Gives nothing, or fails if either result is wrong.
    """
    assert term_display_name("T14") == "Serotonin Syndrome Risk"
    assert term_display_name("T99") == "T99"
