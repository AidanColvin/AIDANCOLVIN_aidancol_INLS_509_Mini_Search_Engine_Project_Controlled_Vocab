"""Network I/O for the NLM RxNav REST API, with the request URLs built in one place."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

RXNAV_BASE_URL = "https://rxnav.nlm.nih.gov/REST/"
MAX_REQUESTS_PER_SECOND = 20
MIN_SECONDS_BETWEEN_REQUESTS = 1.0 / MAX_REQUESTS_PER_SECOND
DEFAULT_TIMEOUT_SECONDS = 30.0
APPROXIMATE_MAX_ENTRIES = 5
SEARCH_EXACT_THEN_NORMALIZED = 2
NLM_ATTRIBUTION = (
    "This product uses publicly available data from the U.S. National Library of Medicine (NLM), "
    "National Institutes of Health, Department of Health and Human Services; NLM is not responsible "
    "for the product and does not endorse or recommend this or any other product."
)


def rxnav_url(path: str, params: dict[str, str] | None = None) -> str:
    """
    Takes a REST path such as "approximateTerm.json" and optional query parameters.
    Joins them onto the RxNav base URL, keeping spaces in values as plus signs.
    Gives the full request URL.
    """
    if not params:
        return RXNAV_BASE_URL + path
    return RXNAV_BASE_URL + path + "?" + urllib.parse.urlencode(params)


def approximate_term_url(term: str) -> str:
    """
    Takes a drug name as typed.
    Builds the getApproximateMatch request URL.
    Gives the URL string.
    """
    return rxnav_url("approximateTerm.json", {"term": term, "maxEntries": str(APPROXIMATE_MAX_ENTRIES)})


def find_rxcui_url(name: str) -> str:
    """
    Takes a drug or substance name.
    Builds the findRxcuiByString request URL with exact-then-normalized search.
    Gives the URL string.
    """
    return rxnav_url("rxcui.json", {"name": name, "search": str(SEARCH_EXACT_THEN_NORMALIZED)})


def related_ingredients_url(rxcui: str) -> str:
    """
    Takes an RxNorm concept id.
    Builds the getRelatedByType request URL for ingredient (IN) concepts.
    Gives the URL string.
    """
    return rxnav_url(f"rxcui/{rxcui}/related.json", {"tty": "IN"})


def history_status_url(rxcui: str) -> str:
    """
    Takes an RxNorm concept id.
    Builds the getRxcuiHistoryStatus request URL.
    Gives the URL string.
    """
    return rxnav_url(f"rxcui/{rxcui}/historystatus.json")


def fetch_rxnav_json(url: str, timeout: float) -> Any:
    """
    Takes a full RxNav URL and a timeout in seconds.
    Performs the GET request and decodes the JSON body.
    Gives the decoded value, or raises urllib.error.URLError or json.JSONDecodeError.
    """
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)
