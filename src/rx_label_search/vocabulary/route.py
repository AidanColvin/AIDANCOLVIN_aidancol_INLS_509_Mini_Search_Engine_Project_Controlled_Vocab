"""Rule for T02 Oral Route."""

from __future__ import annotations

from rx_label_search.records import Label, TermEvidence
from rx_label_search.text.fields import openfda_values
from rx_label_search.vocabulary.terms import RULE_VERSION

ORAL_ROUTE = "ORAL"


def tag_t02_oral_route(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Checks whether openfda.route lists ORAL among the drug's routes.
    Gives evidence naming the field and the route list, or None when ORAL is not listed.
    """
    routes = openfda_values(label, "route")
    if ORAL_ROUTE not in routes:
        return None
    return TermEvidence("T02", "openfda.route", ", ".join(routes), RULE_VERSION)
