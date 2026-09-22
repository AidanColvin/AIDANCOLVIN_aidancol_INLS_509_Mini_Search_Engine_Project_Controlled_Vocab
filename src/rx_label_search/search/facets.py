"""Pure AND/OR facet filtering over PDLA tag sets."""

from __future__ import annotations

from collections.abc import Iterable

from rx_label_search.search.index import IndexedDocument

OPERATOR_AND = "AND"
OPERATOR_OR = "OR"


def document_matches_facets(document: IndexedDocument, term_ids: tuple[str, ...], operator: str) -> bool:
    """
    Takes one document, the selected PDLA term ids, and the join operator.
    Checks the document's tags against the selected terms with AND (intersection) or OR (union) semantics.
    Gives True when the document matches, True for every document when no terms are selected.
    """
    if not term_ids:
        return True
    if operator == OPERATOR_AND:
        return all(term_id in document.tags for term_id in term_ids)
    return any(term_id in document.tags for term_id in term_ids)


def apply_facets(documents: Iterable[IndexedDocument], term_ids: tuple[str, ...], operator: str) -> tuple[IndexedDocument, ...]:
    """
    Takes documents, the selected PDLA term ids, and the join operator.
    Filters the documents to those matching the facet selection.
    Gives the tuple of matching documents, unchanged when no terms are selected.
    """
    return tuple(document for document in documents if document_matches_facets(document, term_ids, operator))
