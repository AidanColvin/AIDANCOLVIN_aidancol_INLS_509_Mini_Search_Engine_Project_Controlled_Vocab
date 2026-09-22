"""Tests for term metadata and hierarchy expansion."""

from __future__ import annotations

from rx_label_search.records import TermEvidence
from rx_label_search.vocabulary.hierarchy import broadened_evidence, consistency_violations, term_ids
from rx_label_search.vocabulary.terms import TERMS, TERMS_BY_ID


def ev(term_id: str) -> TermEvidence:
    """
    Takes a term id.
    Builds a minimal TermEvidence for testing.
    Gives the TermEvidence.
    """
    return TermEvidence(term_id, "field", "sentence", "v")


def test_every_term_is_registered_once() -> None:
    """
    Takes no arguments.
    Checks the term table has 17 distinct ids matching T01 to T17.
    Gives nothing, or fails if any id is missing or duplicated.
    """
    assert len(TERMS) == 17
    assert set(TERMS_BY_ID) == {f"T{n:02d}" for n in range(1, 18)}


def test_broadened_evidence_adds_each_broader_term_once() -> None:
    """
    Takes no arguments.
    Broadens evidence carrying T10, T06, and T14.
    Gives nothing, or fails if T07, T11, or T13 is missing or duplicated.
    """
    evidence = broadened_evidence((ev("T10"), ev("T06"), ev("T14")))
    ids = [item.term_id for item in evidence]
    assert ids.count("T07") == 1
    assert ids.count("T11") == 1
    assert ids.count("T13") == 1
    assert term_ids(evidence) == {"T10", "T06", "T14", "T07", "T11", "T13"}


def test_broadened_evidence_does_not_duplicate_existing_broader() -> None:
    """
    Takes no arguments.
    Broadens evidence that already carries both a narrower and its broader term.
    Gives nothing, or fails if the broader term appears twice.
    """
    evidence = broadened_evidence((ev("T10"), ev("T07")))
    assert [item.term_id for item in evidence].count("T07") == 1


def test_broadened_evidence_empty_input() -> None:
    """
    Takes no arguments.
    Broadens an empty evidence tuple.
    Gives nothing, or fails if the result is not empty.
    """
    assert broadened_evidence(()) == ()


def test_consistency_violations_catch_each_rule() -> None:
    """
    Takes no arguments.
    Checks evidence sets that violate each consistency rule on its own.
    Gives nothing, or fails if any violation is missed or a valid set is flagged.
    """
    assert consistency_violations((ev("T10"),)) == ("T10 without T07",)
    assert consistency_violations((ev("T11"),)) == ("T11 without T06 or T12",)
    assert consistency_violations((ev("T13"),)) == ("T13 without any of T14 to T17",)
    assert consistency_violations(broadened_evidence((ev("T10"), ev("T06"), ev("T14")))) == ()
    assert consistency_violations(()) == ()
