"""Rule for T05 Medication Guide."""

from __future__ import annotations

from rx_label_search.records import Label, TermEvidence
from rx_label_search.text.fields import label_text
from rx_label_search.vocabulary.terms import RULE_VERSION


def tag_t05_medication_guide(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Checks whether its spl_medguide field carries any text.
    Gives evidence naming the field and a short excerpt, or None when the field is empty.
    """
    text = label_text(label, "spl_medguide")
    if not text:
        return None
    return TermEvidence("T05", "spl_medguide", text[:200], RULE_VERSION)
