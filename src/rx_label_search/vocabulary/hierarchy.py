"""Pure indexing-time broader-term expansion, matching Appendix C Section 2."""

from __future__ import annotations

from rx_label_search.records import TermEvidence
from rx_label_search.vocabulary.terms import NARROWER_TO_BROADER, RULE_VERSION


def broadened_evidence(evidence: tuple[TermEvidence, ...]) -> tuple[TermEvidence, ...]:
    """
    Takes the evidence assigned by every rule function on one label.
    Adds one broader-term evidence entry for each narrower term already present, without duplicating a broader term.
    Gives the evidence tuple with the broader entries appended in narrower-to-broader order.
    """
    present = {item.term_id for item in evidence}
    added: list[TermEvidence] = []
    for narrower, broader in NARROWER_TO_BROADER.items():
        if narrower in present and broader not in present:
            source = next(item for item in evidence if item.term_id == narrower)
            added.append(TermEvidence(broader, source.field_name, source.sentence, RULE_VERSION))
            present.add(broader)
    return (*evidence, *added)


def term_ids(evidence: tuple[TermEvidence, ...]) -> frozenset[str]:
    """
    Takes a label's evidence tuple.
    Collects the distinct term ids it carries.
    Gives the frozenset of term ids, empty for no evidence.
    """
    return frozenset(item.term_id for item in evidence)


def consistency_violations(evidence: tuple[TermEvidence, ...]) -> tuple[str, ...]:
    """
    Takes a label's fully broadened evidence tuple.
    Checks the three consistency rules: no T10 without T07, no T11 without T06 or T12, no T13 without T14 to T17.
    Gives the tuple of violation messages, empty when every rule holds.
    """
    present = term_ids(evidence)
    violations: list[str] = []
    if "T10" in present and "T07" not in present:
        violations.append("T10 without T07")
    if "T11" in present and not present & {"T06", "T12"}:
        violations.append("T11 without T06 or T12")
    if "T13" in present and not present & {"T14", "T15", "T16", "T17"}:
        violations.append("T13 without any of T14 to T17")
    return tuple(violations)
