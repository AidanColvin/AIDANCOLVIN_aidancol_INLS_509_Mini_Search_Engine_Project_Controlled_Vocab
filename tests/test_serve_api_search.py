"""Tests for the search API's pure request/response logic."""

from __future__ import annotations

from pathlib import Path

from rx_label_search.serve.api_search import available_terms, build_search_response, load_build_date, parse_search_params
from rx_label_search.storage.write_json import write_json
from rx_label_search.storage.write_jsonl import write_jsonl


def test_parse_search_params_defaults_and_bounds() -> None:
    """
    Takes no arguments.
    Parses an empty params dict, an invalid operator, an invalid limit, and an over-large limit.
    Gives nothing, or fails if any default or bound is wrong.
    """
    assert parse_search_params({}) == ("", (), "AND", 10)
    assert parse_search_params({"operator": ["XOR"]})[2] == "AND"
    assert parse_search_params({"limit": ["not a number"]})[3] == 10
    assert parse_search_params({"limit": ["9999"]})[3] == 50


def test_parse_search_params_reads_repeated_terms() -> None:
    """
    Takes no arguments.
    Parses params carrying two term values.
    Gives nothing, or fails if both are not read in order.
    """
    assert parse_search_params({"term": ["T01", "T02"]})[1] == ("T01", "T02")


def test_available_terms_lists_all_seventeen() -> None:
    """
    Takes no arguments.
    Reads the available terms list.
    Gives nothing, or fails if the count is wrong or any entry lacks a name.
    """
    terms = available_terms()
    assert len(terms) == 17
    assert all(term["name"] for term in terms)


def test_load_build_date_missing_and_present(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Reads the build date before and after a stats file exists.
    Gives nothing, or fails if either result is wrong.
    """
    assert load_build_date(tmp_path) == "unknown"
    write_json(tmp_path / "collection_stats.json", {"build_date": "2026-09-21"})
    assert load_build_date(tmp_path) == "2026-09-21"


def test_build_search_response_end_to_end(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Builds a small index and runs a search response through it.
    Gives nothing, or fails if the response shape or the one expected hit is wrong.
    """
    from rx_label_search.search.run import build_search_index_file

    write_jsonl(tmp_path / "collection.jsonl", [{"set_id": "s1", "indications_and_usage": ["treats hypertension"]}])
    write_jsonl(tmp_path / "tags.jsonl", [{"set_id": "s1", "evidence": []}])
    build_search_index_file(tmp_path)
    response = build_search_response(tmp_path, {"q": ["hypertension"]}, "2026-09-21")
    assert response["build_date"] == "2026-09-21"
    assert len(response["hits"]) == 1
    assert response["hits"][0]["set_id"] == "s1"
