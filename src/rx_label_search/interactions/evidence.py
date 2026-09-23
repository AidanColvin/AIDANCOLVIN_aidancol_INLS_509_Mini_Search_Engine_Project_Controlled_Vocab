"""Pure evidence assembly: DailyMed links and the per-drug evidence records for an alert."""

from __future__ import annotations

from urllib.parse import quote

from rx_label_search.records import AlertEvidence, TermEvidence
from rx_label_search.vocabulary.terms import TERMS_BY_ID

DAILYMED_URL_TEMPLATE = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}"
DAILYMED_SEARCH_TEMPLATE = "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={name}"


def dailymed_url(set_id: str, name: str = "") -> str:
    """
    Takes an SPL set id and, for a drug with no label in the collection, its name.
    Builds the DailyMed label page URL, or the DailyMed search page for the name when there is no set id.
    Gives the URL string.
    """
    if not set_id and name:
        return DAILYMED_SEARCH_TEMPLATE.format(name=quote(name))
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
