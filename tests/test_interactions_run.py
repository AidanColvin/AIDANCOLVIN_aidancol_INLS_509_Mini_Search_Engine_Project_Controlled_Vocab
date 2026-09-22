"""Tests for the checker data-build job, isolated to a temp directory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rx_label_search.interactions.run import build_checker_data, build_checker_record, label_schedule
from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.write_jsonl import write_jsonl


def test_label_schedule_reads_most_restrictive_named() -> None:
    """
    Takes no arguments.
    Reads the schedule from text naming Schedule IV and text naming none.
    Gives nothing, or fails if either result is wrong.
    """
    assert label_schedule("This is a Schedule IV controlled substance.") == "IV"
    assert label_schedule("This drug is not a controlled substance.") is None


def test_build_checker_record_reads_every_field() -> None:
    """
    Takes no arguments.
    Builds a checker record from a small raw record and two evidence rows.
    Gives nothing, or fails if any field is wrong.
    """
    record = {
        "set_id": "s1",
        "effective_time": "20250101",
        "controlled_substance": ["This is a Schedule II controlled substance."],
        "openfda": {"brand_name": ["Foo"], "generic_name": ["bar"], "substance_name": ["BAR"], "route": ["ORAL"], "pharm_class_epc": ["Test Class [EPC]"]},
    }
    evidence_rows: list[dict[str, Any]] = [{"term_id": "T07", "field_name": "controlled_substance", "sentence": "s", "rule_version": "v"}]
    checker_record = build_checker_record(record, evidence_rows)
    assert checker_record["set_id"] == "s1"
    assert checker_record["ingredient_set"] == ["BAR"]
    assert checker_record["schedule"] == "II"
    assert checker_record["pharm_class_epc"] == ["Test Class [EPC]"]
    assert checker_record["evidence"] == evidence_rows


def test_build_checker_data_writes_both_files(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Runs the checker data build job on a two-label build directory.
    Gives nothing, or fails if either output file is missing the expected entry.
    """
    write_jsonl(tmp_path / "collection.jsonl", [{"set_id": "s1", "openfda": {"substance_name": ["FOO"]}}])
    write_jsonl(tmp_path / "tags.jsonl", [{"set_id": "s1", "evidence": []}])
    from rx_label_search.storage.write_json import write_json

    write_json(tmp_path / "collection_summaries.json", [{"set_id": "s1", "ingredient_set": ["FOO"]}])
    summary = build_checker_data(tmp_path)
    assert summary["records"] == 1
    records = read_json(tmp_path / "checker_records.json")
    assert "s1" in records
    index = read_json(tmp_path / "ingredient_set_index.json")
    assert index["FOO"] == "s1"
