"""Tests for the check API's pure request/response logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from rx_label_search.serve.api_check import MAX_MEDICATION_TEXT_CHARS, MedicationTextTooLong, build_check_response, parse_check_body
from rx_label_search.storage.write_json import write_json
from rx_label_search.storage.write_jsonl import write_jsonl


def test_parse_check_body_defaults() -> None:
    """
    Takes no arguments.
    Parses an empty body and a body with use_rxnorm false.
    Gives nothing, or fails if either default is wrong.
    """
    assert parse_check_body({}) == ("", True)
    assert parse_check_body({"medications": "aspirin", "use_rxnorm": False}) == ("aspirin", False)


def test_parse_check_body_raises_instead_of_silently_truncating() -> None:
    """
    Takes no arguments.
    Parses a medication text one character over the maximum length.
    Gives nothing, or fails if the text is truncated instead of raising MedicationTextTooLong.
    """
    with pytest.raises(MedicationTextTooLong):
        parse_check_body({"medications": "a" * (MAX_MEDICATION_TEXT_CHARS + 1)})
    parse_check_body({"medications": "a" * MAX_MEDICATION_TEXT_CHARS})


def test_build_check_response_is_stateless_and_uses_the_build_date(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Builds the minimal lookup files and runs a check response with RxNorm disabled.
    Gives nothing, or fails if the notice does not carry the build date or the report shape is wrong.
    """
    write_json(tmp_path / "collection_stats.json", {"build_date": "2026-09-21"})
    write_json(tmp_path / "name_dictionary.json", {})
    write_json(tmp_path / "collection_summaries.json", [])
    write_json(tmp_path / "ingredient_set_index.json", {})
    write_json(tmp_path / "checker_records.json", {})
    write_jsonl(tmp_path / "tags.jsonl", [])
    response = build_check_response(tmp_path, {"medications": "", "use_rxnorm": False})
    assert response["build_date"] == "2026-09-21"
    assert "2026-09-21" in response["notice"]
    assert response["medication_table"] == []
