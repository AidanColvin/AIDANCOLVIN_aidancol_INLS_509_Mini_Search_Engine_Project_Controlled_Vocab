"""Tests for the lean ranking file and snippet-shard serialization, isolated to a temp directory."""

from __future__ import annotations

from pathlib import Path

from rx_label_search.search.index import build_indexed_document
from rx_label_search.search.run import (
    attach_snippet,
    build_search_index_file,
    document_to_ranking_json,
    load_body_text,
    load_ranking_documents,
    ranking_document_from_json,
    search_with_snippets,
)
from rx_label_search.storage.write_jsonl import write_jsonl


def test_ranking_document_round_trips_without_body_text() -> None:
    """
    Takes no arguments.
    Serializes and rebuilds one indexed document through the lean ranking format.
    Gives nothing, or fails if any ranking field differs or body text is not empty after the round trip.
    """
    original = build_indexed_document({"set_id": "s1", "effective_time": "20250101", "indications_and_usage": ["hypertension pain"]}, frozenset({"T02"}))
    rebuilt = ranking_document_from_json(document_to_ranking_json(original))
    assert rebuilt.set_id == original.set_id
    assert rebuilt.tags == original.tags
    assert rebuilt.length == original.length
    assert rebuilt.term_frequencies == original.term_frequencies
    assert rebuilt.body_text == ""


def test_build_search_index_file_writes_ranking_and_shards(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Builds the index files from a two-label build directory.
    Gives nothing, or fails if the ranking file, either snippet shard, or the document count is wrong.
    """
    write_jsonl(tmp_path / "collection.jsonl", [{"set_id": "s1", "indications_and_usage": ["hypertension"]}, {"set_id": "s2", "indications_and_usage": ["headache"]}])
    write_jsonl(tmp_path / "tags.jsonl", [{"set_id": "s1", "evidence": []}, {"set_id": "s2", "evidence": []}])
    count = build_search_index_file(tmp_path)
    assert count == 2
    documents = load_ranking_documents(tmp_path)
    assert {document.set_id for document in documents} == {"s1", "s2"}
    assert all(document.body_text == "" for document in documents)
    assert "hypertension" in load_body_text(tmp_path, "s1")
    assert load_body_text(tmp_path, "missing") == ""


def test_attach_snippet_fills_in_the_real_snippet(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Builds the index files, ranks with no snippet, then attaches the real snippet to one hit.
    Gives nothing, or fails if the snippet does not contain the query term.
    """
    write_jsonl(tmp_path / "collection.jsonl", [{"set_id": "s1", "indications_and_usage": ["treats severe hypertension in adults"]}])
    write_jsonl(tmp_path / "tags.jsonl", [{"set_id": "s1", "evidence": []}])
    build_search_index_file(tmp_path)
    documents = load_ranking_documents(tmp_path)
    from rx_label_search.search.run import search

    hit = search("hypertension", (), "AND", documents)[0]
    assert hit.snippet == ""
    filled = attach_snippet(tmp_path, "hypertension", hit)
    assert "hypertension" in filled.snippet


def test_search_with_snippets_limits_before_reading_shards(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Runs search_with_snippets with a limit of one over two matching labels.
    Gives nothing, or fails if more than one hit comes back or its snippet is empty.
    """
    write_jsonl(tmp_path / "collection.jsonl", [{"set_id": "s1", "indications_and_usage": ["hypertension hypertension hypertension"]}, {"set_id": "s2", "indications_and_usage": ["hypertension"]}])
    write_jsonl(tmp_path / "tags.jsonl", [{"set_id": "s1", "evidence": []}, {"set_id": "s2", "evidence": []}])
    build_search_index_file(tmp_path)
    documents = load_ranking_documents(tmp_path)
    hits = search_with_snippets(tmp_path, "hypertension", (), "AND", documents, 1)
    assert len(hits) == 1
    assert hits[0].snippet != ""
