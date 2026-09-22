"""Pure request/response handling for the search API, separate from the HTTP transport."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rx_label_search.search.facets import OPERATOR_AND, OPERATOR_OR
from rx_label_search.search.run import load_ranking_documents, search_with_snippets
from rx_label_search.storage.read_json import read_json

MAX_SEARCH_RESULTS = 50


def parse_search_params(params: dict[str, list[str]]) -> tuple[str, tuple[str, ...], str, int]:
    """
    Takes the request's query parameters, each value a list as query strings allow repeats.
    Reads the search text, PDLA term ids, join operator, and result limit.
    Gives (query text, term ids, operator, limit), with safe defaults for anything missing or invalid.
    """
    query_text = (params.get("q") or [""])[0]
    term_ids = tuple(params.get("term") or ())
    operator = (params.get("operator") or [OPERATOR_AND])[0]
    if operator not in (OPERATOR_AND, OPERATOR_OR):
        operator = OPERATOR_AND
    try:
        limit = min(MAX_SEARCH_RESULTS, max(1, int((params.get("limit") or ["10"])[0])))
    except ValueError:
        limit = 10
    return query_text, term_ids, operator, limit


def build_search_response(build_dir: Path, params: dict[str, list[str]], build_date: str) -> dict[str, Any]:
    """
    Takes the build directory, the request's query parameters, and the build date.
    Runs one search against the lean ranking documents and attaches snippets to the returned hits.
    Gives the JSON-ready response with the hits, the query it ran, and the build date.
    """
    from dataclasses import asdict

    query_text, term_ids, operator, limit = parse_search_params(params)
    documents = load_ranking_documents(build_dir)
    hits = search_with_snippets(build_dir, query_text, term_ids, operator, documents, limit)
    return {
        "build_date": build_date,
        "query": query_text,
        "terms": list(term_ids),
        "operator": operator,
        "hits": [asdict(hit) for hit in hits],
    }


def available_terms() -> list[dict[str, str]]:
    """
    Takes no arguments.
    Reads the PDLA term table.
    Gives the list of {"term_id", "name", "property_group"} dictionaries, in T01 to T17 order.
    """
    from rx_label_search.vocabulary.terms import TERMS

    return [{"term_id": term.term_id, "name": term.name, "property_group": term.property_group} for term in TERMS]


def load_build_date(build_dir: Path) -> str:
    """
    Takes the build directory.
    Reads the build date recorded in the collection stats file.
    Gives the date string, or "unknown" when the stats file is missing.
    """
    stats_path = build_dir / "collection_stats.json"
    if not stats_path.is_file():
        return "unknown"
    return str(read_json(stats_path).get("build_date", "unknown"))
