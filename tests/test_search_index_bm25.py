"""Tests for index construction and BM25 scoring."""

from __future__ import annotations

from rx_label_search.search.bm25 import inverse_document_frequency, rank_documents, score_document, term_score
from rx_label_search.search.index import (
    average_document_length,
    build_document_frequencies,
    build_indexed_document,
    document_text,
)


def test_document_text_joins_fields_and_names() -> None:
    """
    Takes no arguments.
    Builds document text from a record with two indexed fields and openfda names.
    Gives nothing, or fails if any piece is missing.
    """
    record = {"indications_and_usage": ["treats hypertension"], "boxed_warning": ["risk of death"], "openfda": {"brand_name": ["Foo"], "generic_name": ["bar"], "substance_name": ["BAR HYDROCHLORIDE"]}}
    text = document_text(record)
    assert "hypertension" in text
    assert "risk of death" in text
    assert "Foo" in text
    assert "BAR HYDROCHLORIDE" in text


def test_document_text_empty_record() -> None:
    """
    Takes no arguments.
    Builds document text from an empty record.
    Gives nothing, or fails if the result is not empty.
    """
    assert document_text({}) == ""


def test_build_indexed_document_has_tokens_and_tags() -> None:
    """
    Takes no arguments.
    Builds an indexed document from a small record with two tags.
    Gives nothing, or fails if the tokens, length, or tags are wrong.
    """
    record = {"set_id": "s1", "effective_time": "20250101", "indications_and_usage": ["treats hypertension"], "openfda": {"brand_name": ["Foo"], "generic_name": ["bar"]}}
    document = build_indexed_document(record, frozenset({"T01", "T02"}))
    assert document.tags == frozenset({"T01", "T02"})
    assert "hypertension" in document.tokens
    assert document.length == len(document.tokens)


def test_document_frequencies_and_average_length() -> None:
    """
    Takes no arguments.
    Builds frequencies and average length from two documents sharing one token.
    Gives nothing, or fails if either result is wrong.
    """
    a = build_indexed_document({"set_id": "a", "indications_and_usage": ["hypertension pain"]}, frozenset())
    b = build_indexed_document({"set_id": "b", "indications_and_usage": ["hypertension"]}, frozenset())
    frequencies = build_document_frequencies([a, b])
    assert frequencies["hypertension"] == 2
    assert frequencies["pain"] == 1
    assert average_document_length([a, b]) == 1.5
    assert average_document_length([]) == 0.0


def test_idf_decreases_as_document_frequency_rises() -> None:
    """
    Takes no arguments.
    Computes idf for a rare and a common term.
    Gives nothing, or fails if the rare term does not score higher.
    """
    rare = inverse_document_frequency("x", 1, 100)
    common = inverse_document_frequency("x", 90, 100)
    assert rare > common
    assert inverse_document_frequency("x", 0, 0) == 0.0


def test_term_score_zero_when_absent_or_no_average_length() -> None:
    """
    Takes no arguments.
    Scores a term that does not occur and one where the average length is zero.
    Gives nothing, or fails if either is not 0.0.
    """
    assert term_score(0, 2.0, 10, 10.0, 1.2, 0.75) == 0.0
    assert term_score(1, 2.0, 10, 0.0, 1.2, 0.75) == 0.0


def test_rank_documents_orders_by_score_and_drops_zero() -> None:
    """
    Takes no arguments.
    Builds a small index and ranks a query that matches one document strongly and one not at all.
    Gives nothing, or fails if the ranking or the drop of the zero-score document is wrong.
    """
    a = build_indexed_document({"set_id": "a", "indications_and_usage": ["hypertension hypertension hypertension"]}, frozenset())
    b = build_indexed_document({"set_id": "b", "indications_and_usage": ["headache"]}, frozenset())
    frequencies = build_document_frequencies([a, b])
    ranked = rank_documents(("hypertension",), [a, b], frequencies, 2, average_document_length([a, b]))
    assert [document.set_id for document, _ in ranked] == ["a"]


def test_score_document_sums_multiple_terms() -> None:
    """
    Takes no arguments.
    Scores a document against two query terms it both contains.
    Gives nothing, or fails if the two-term score is not greater than either term alone.
    """
    document = build_indexed_document({"set_id": "a", "indications_and_usage": ["hypertension and edema"]}, frozenset())
    idf = {"hypertension": 1.0, "edema": 1.0}
    both = score_document(("hypertension", "edema"), document, idf, float(document.length))
    one = score_document(("hypertension",), document, idf, float(document.length))
    assert both > one
