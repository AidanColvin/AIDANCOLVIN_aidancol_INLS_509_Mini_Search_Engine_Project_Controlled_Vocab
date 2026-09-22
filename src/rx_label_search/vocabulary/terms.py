"""Metadata for the PDLA terms T01 to T17, matching Appendix C exactly."""

from __future__ import annotations

from typing import NamedTuple

RULE_VERSION = "pdla-rules-v1"


class TermInfo(NamedTuple):
    """One PDLA term's id, preferred name, and property group."""

    term_id: str
    name: str
    property_group: str


TERMS: tuple[TermInfo, ...] = (
    TermInfo("T01", "Boxed Warning", "Safety signal"),
    TermInfo("T02", "Oral Route", "Route"),
    TermInfo("T03", "Pediatric Indication", "Patient group"),
    TermInfo("T04", "High-Frequency Adverse Effect", "Safety signal"),
    TermInfo("T05", "Medication Guide", "Patient information"),
    TermInfo("T06", "Renal Dose Adjustment", "Dosing"),
    TermInfo("T07", "Controlled Substance", "DEA control"),
    TermInfo("T08", "Single Active Ingredient", "Product form"),
    TermInfo("T09", "Brand Name Product", "Product form"),
    TermInfo("T10", "Schedule II Controlled Substance", "DEA control"),
    TermInfo("T11", "Organ Impairment Dose Adjustment", "Dosing"),
    TermInfo("T12", "Hepatic Dose Adjustment", "Dosing"),
    TermInfo("T13", "Interaction Risk", "Interaction risk"),
    TermInfo("T14", "Serotonin Syndrome Risk", "Interaction risk"),
    TermInfo("T15", "CNS Depression Risk", "Interaction risk"),
    TermInfo("T16", "QT Prolongation Risk", "Interaction risk"),
    TermInfo("T17", "Contraindicated Combination", "Interaction risk"),
)
TERMS_BY_ID: dict[str, TermInfo] = {term.term_id: term for term in TERMS}
NARROWER_TO_BROADER: dict[str, str] = {"T10": "T07", "T06": "T11", "T12": "T11", "T14": "T13", "T15": "T13", "T16": "T13", "T17": "T13"}
BROADER_TERMS: frozenset[str] = frozenset({"T11", "T13"})
