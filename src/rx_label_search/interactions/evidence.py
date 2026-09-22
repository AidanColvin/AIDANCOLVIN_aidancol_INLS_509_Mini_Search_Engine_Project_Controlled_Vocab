"""Pure evidence assembly: DailyMed links and the per-drug evidence records for an alert."""

from __future__ import annotations

from rx_label_search.records import AlertEvidence, TermEvidence
from rx_label_search.vocabulary.terms import TERMS_BY_ID

DAILYMED_URL_TEMPLATE = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}"


def dailymed_url(set_id: str) -> str:
    """
    Takes an SPL set id.
    Builds the DailyMed label page URL for it.
    Gives the URL string.
    """
    return DAILYMED_URL_TEMPLATE.format(set_id=set_id)


def evidence_for_term(drug_name: str, set_id: str, effective_time: str, term_evidence: TermEvidence) -> AlertEvidence:
    """
    Takes a drug's display name, set id, effective time, and the TermEvidence behind one alert member.
    Builds the AlertEvidence record with the DailyMed link.
    Gives the AlertEvidence.
    """
    return AlertEvidence(
        drug_name=drug_name,
        set_id=set_id,
        effective_time=effective_time,
        section=term_evidence.field_name,
        sentence=term_evidence.sentence,
        dailymed_url=dailymed_url(set_id),
    )


def term_display_name(term_id: str) -> str:
    """
    Takes a PDLA term id.
    Looks up its preferred display name.
    Gives the name, or the term id itself when it is not a registered term.
    """
    term = TERMS_BY_ID.get(term_id)
    return term.name if term is not None else term_id
