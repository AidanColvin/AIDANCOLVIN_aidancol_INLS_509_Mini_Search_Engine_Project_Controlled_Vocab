"""Tests for AND/OR facets and snippet extraction."""

from __future__ import annotations

from rx_label_search.search.facets import apply_facets, document_matches_facets
from rx_label_search.search.index import IndexedDocument, build_indexed_document
from rx_label_search.search.snippets import build_snippet, find_first_query_word_position, snippet_for_query


def doc(set_id: str, tags: frozenset[str]) -> IndexedDocument:
    """
    Takes a set id and a tag set.
    Builds a minimal indexed document for facet tests.
    Gives the IndexedDocument.
    """
    return build_indexed_document({"set_id": set_id}, tags)


def test_and_is_intersection_or_is_union() -> None:
    """
    Takes no arguments.
    Filters three documents by two terms with AND and with OR.
    Gives nothing, or fails if either result is wrong.
    """
    documents = [doc("a", frozenset({"T01"})), doc("b", frozenset({"T02"})), doc("c", frozenset({"T01", "T02"}))]
    assert [d.set_id for d in apply_facets(documents, ("T01", "T02"), "AND")] == ["c"]
    assert [d.set_id for d in apply_facets(documents, ("T01", "T02"), "OR")] == ["a", "b", "c"]


def test_no_terms_selected_matches_everything() -> None:
    """
    Takes no arguments.
    Filters with no term ids selected.
    Gives nothing, or fails if any document is dropped.
    """
    documents = [doc("a", frozenset())]
    assert document_matches_facets(documents[0], (), "AND")
    assert len(apply_facets(documents, (), "OR")) == 1


def test_find_first_query_word_position_and_missing() -> None:
    """
    Takes no arguments.
    Finds the position of a query word present and one absent.
    Gives nothing, or fails if either result is wrong.
    """
    assert find_first_query_word_position("Treats severe hypertension in adults", ("hypertension",)) == 14
    assert find_first_query_word_position("no match here", ("zzz",)) is None


def test_build_snippet_marks_cut_edges() -> None:
    """
    Takes no arguments.
    Builds a snippet from long text around a match near the middle and one with no match.
    Gives nothing, or fails if either ellipsis is missing or present incorrectly.
    """
    text = "x" * 200 + " hypertension " + "y" * 200
    snippet = build_snippet(text, ("hypertension",), 20)
    assert snippet.startswith("…")
    assert snippet.endswith("…")
    assert "hypertension" in snippet
    no_match = build_snippet("short text with no match", ("zzz",), 20)
    assert not no_match.startswith("…")


def test_build_snippet_empty_text() -> None:
    """
    Takes no arguments.
    Builds a snippet from an empty body.
    Gives nothing, or fails if the result is not empty.
    """
    assert build_snippet("", ("x",), 20) == ""


def test_snippet_for_query_tokenizes_first() -> None:
    """
    Takes no arguments.
    Builds a snippet using a raw query string with punctuation.
    Gives nothing, or fails if the match is not found.
    """
    snippet = snippet_for_query("Used for muscle spasm relief.", "muscle spasm?")
    assert "muscle spasm" in snippet
