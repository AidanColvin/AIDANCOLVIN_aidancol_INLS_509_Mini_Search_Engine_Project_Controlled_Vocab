"""Pure BM25 scoring, with K1 and B as named module constants."""

from __future__ import annotations

import math
from collections.abc import Iterable

from rx_label_search.search.index import IndexedDocument

K1 = 1.2
B = 0.75


def inverse_document_frequency(term: str, document_frequency: int, total_documents: int) -> float:
    """
    Takes a query term, the number of documents it appears in, and the total document count.
    Computes the BM25 inverse document frequency with the standard 0.5 smoothing.
    Gives the score, 0.0 when there are no documents.
    """
    if total_documents == 0:
        return 0.0
    return math.log((total_documents - document_frequency + 0.5) / (document_frequency + 0.5) + 1.0)


def term_score(term_frequency: int, idf: float, document_length: int, average_length: float, k1: float, b: float) -> float:
    """
    Takes a term's frequency in one document, its inverse document frequency, the document's length, the average length, and K1 and B.
    Computes that term's contribution to the document's BM25 score.
    Gives the score, 0.0 when the term does not occur or the average length is 0.
    """
    if term_frequency == 0 or average_length == 0:
        return 0.0
    length_norm = 1 - b + b * (document_length / average_length)
    return idf * (term_frequency * (k1 + 1)) / (term_frequency + k1 * length_norm)


def score_document(query_terms: tuple[str, ...], document: IndexedDocument, idf_by_term: dict[str, float], average_length: float) -> float:
    """
    Takes the query terms, one document, the precomputed inverse document frequencies, and the average length.
    Sums each query term's BM25 contribution to the document.
    Gives the total score, 0.0 when no query term occurs in the document.
    """
    return sum(
        term_score(document.term_frequencies.get(term, 0), idf_by_term.get(term, 0.0), document.length, average_length, K1, B)
        for term in query_terms
    )


def rank_documents(
    query_terms: tuple[str, ...],
    documents: Iterable[IndexedDocument],
    document_frequency: dict[str, int],
    total_documents: int,
    average_length: float,
) -> tuple[tuple[IndexedDocument, float], ...]:
    """
    Takes the query terms, the candidate documents, the collection's document frequencies, the total document count, and the average length.
    Scores every candidate and sorts them by descending score, breaking ties by set id.
    Gives the tuple of (document, score) pairs, keeping only scores above 0.0.
    """
    idf_by_term = {term: inverse_document_frequency(term, document_frequency.get(term, 0), total_documents) for term in query_terms}
    scored = [(document, score_document(query_terms, document, idf_by_term, average_length)) for document in documents]
    positive = [pair for pair in scored if pair[1] > 0.0]
    return tuple(sorted(positive, key=lambda pair: (-pair[1], pair[0].set_id)))
