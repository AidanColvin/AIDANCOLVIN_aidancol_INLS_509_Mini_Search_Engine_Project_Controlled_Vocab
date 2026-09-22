"""Tests for the gold-template, gold-label, and evaluation jobs, isolated to a temp directory."""

from __future__ import annotations

from pathlib import Path

import pytest

from rx_label_search.evaluate.run import add_gold_label, predicted_terms_by_set_id, run_tag_evaluation, write_placeholder_gold
from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.write_jsonl import write_jsonl


def make_build_dir(tmp_path: Path) -> Path:
    """
    Takes a temporary directory fixture.
    Writes a two-label tags.jsonl file into it.
    Gives the build directory path.
    """
    rows = [
        {"set_id": "s1", "evidence": [{"term_id": "T06", "field_name": "f", "sentence": "s", "rule_version": "v"}]},
        {"set_id": "s2", "evidence": []},
    ]
    write_jsonl(tmp_path / "tags.jsonl", rows)
    return tmp_path


def test_write_placeholder_gold_covers_the_requested_sample(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Writes a placeholder gold template for both tagged labels.
    Gives nothing, or fails if either set id or the placeholder rationale is missing.
    """
    build_dir = make_build_dir(tmp_path)
    output = write_placeholder_gold(build_dir, 10, tmp_path / "gold.json")
    document = read_json(output)
    assert set(document["labels"]) == {"s1", "s2"}
    assert document["labels"]["s1"]["T06"]["rationale"].startswith("PLACEHOLDER")


def test_predicted_terms_by_set_id_reads_tags(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Reads predicted terms from the two-label tags file.
    Gives nothing, or fails if either label's term set is wrong.
    """
    build_dir = make_build_dir(tmp_path)
    predicted = predicted_terms_by_set_id(build_dir)
    assert predicted == {"s1": frozenset({"T06"}), "s2": frozenset()}


def test_predicted_terms_by_set_id_missing_file(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture with no tags file.
    Reads predicted terms.
    Gives nothing, or fails if the result is not empty.
    """
    assert predicted_terms_by_set_id(tmp_path) == {}


def test_add_gold_label_then_evaluate_runs_end_to_end(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Writes a placeholder gold template, records one real label, then evaluates it against the tags.
    Gives nothing, or fails if the report does not show a perfect true positive for T06.
    """
    build_dir = make_build_dir(tmp_path)
    gold_path = write_placeholder_gold(build_dir, 10, tmp_path / "gold.json")
    add_gold_label(gold_path, "s1", "T06", True, "gabapentin's label ties creatinine clearance to a lower dose")
    report = run_tag_evaluation(build_dir, gold_path, tmp_path / "report.md")
    assert "| T06 | 1 | 0 | 0 |" in report
    assert (tmp_path / "report.json").is_file()


def test_run_tag_evaluation_rejects_invalid_gold_file(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Runs evaluation against a gold file with a bad schema version.
    Gives nothing, or fails if ValueError is not raised.
    """
    build_dir = make_build_dir(tmp_path)
    from rx_label_search.storage.write_json import write_json

    bad_path = tmp_path / "bad_gold.json"
    write_json(bad_path, {"schema_version": 99, "labels": {}})
    with pytest.raises(ValueError):
        run_tag_evaluation(build_dir, bad_path, tmp_path / "report.md")
