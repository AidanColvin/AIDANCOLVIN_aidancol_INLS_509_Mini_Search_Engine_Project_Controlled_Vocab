"""Pure orchestration of one search: tokenize, facet-filter, rank, and format hits."""

from __future__ import annotations

from collections.abc import Iterable

from rx_label_search.records import SearchHit
from rx_label_search.search.bm25 import rank_documents
from rx_label_search.search.facets import apply_facets
from rx_label_search.search.index import IndexedDocument
from rx_label_search.search.snippets import build_snippet, SNIPPET_RADIUS_CHARS
from rx_label_search.search.tokenize import tokenize


def hit_from_document(document: IndexedDocument, score: float, query_terms: tuple[str, ...]) -> SearchHit:
    """
    Takes a matched document, its BM25 score, and the query terms.
    Builds the display hit with a snippet around the first match.
    Gives the SearchHit.
    """
    return SearchHit(
        set_id=document.set_id,
        brand_name=document.brand_name,
        generic_name=document.generic_name,
        snippet=build_snippet(document.body_text, query_terms, SNIPPET_RADIUS_CHARS),
        tags=tuple(sorted(document.tags)),
        effective_time=document.effective_time,
        score=score,
    )


def run_query(
    query_text: str,
    term_ids: tuple[str, ...],
    operator: str,
    documents: Iterable[IndexedDocument],
    document_frequency: dict[str, int],
    total_documents: int,
    average_length: float,
) -> tuple[SearchHit, ...]:
    """
    Takes the query text, selected PDLA term ids, the join operator, the candidate documents, and the index statistics.
    Applies the facet filter first, then ranks the facet-filtered documents by BM25 when a query was typed.
    Gives the tuple of hits best first, or every facet-matching document in set-id order when the query is blank.
    """
    filtered = apply_facets(documents, term_ids, operator)
    query_terms = tokenize(query_text)
    if not query_terms:
        return tuple(hit_from_document(document, 0.0, ()) for document in sorted(filtered, key=lambda d: d.set_id))
    ranked = rank_documents(query_terms, filtered, document_frequency, total_documents, average_length)
    return tuple(hit_from_document(document, score, query_terms) for document, score in ranked)
