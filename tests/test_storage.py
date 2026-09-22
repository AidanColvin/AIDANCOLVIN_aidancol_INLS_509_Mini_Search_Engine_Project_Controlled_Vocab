"""Tests for the JSON and JSON Lines storage helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.read_jsonl import iter_jsonl, read_jsonl
from rx_label_search.storage.write_json import ensure_parent_dir, write_json
from rx_label_search.storage.write_jsonl import write_jsonl


def test_write_then_read_json_round_trips(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Writes a nested value as JSON and reads it back.
    Gives nothing, or fails if the value changed.
    """
    target = tmp_path / "nested" / "data.json"
    value = {"a": [1, 2, {"b": "text"}], "c": None}
    assert write_json(target, value) == target
    assert read_json(target) == value


def test_write_json_leaves_no_temp_file(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Writes a value and lists the directory afterwards.
    Gives nothing, or fails if a temporary file remains.
    """
    target = tmp_path / "data.json"
    write_json(target, {"x": 1})
    assert sorted(entry.name for entry in tmp_path.iterdir()) == ["data.json"]


def test_read_json_missing_file_raises(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Reads a path that does not exist.
    Gives nothing, or fails if FileNotFoundError is not raised.
    """
    with pytest.raises(FileNotFoundError):
        read_json(tmp_path / "missing.json")


def test_ensure_parent_dir_creates_directory(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Ensures the parent of a nested path exists.
    Gives nothing, or fails if the parent directory was not created.
    """
    target = tmp_path / "a" / "b" / "c.json"
    assert ensure_parent_dir(target) == target
    assert target.parent.is_dir()


def test_write_then_read_jsonl_round_trips(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Writes three rows as JSON Lines and reads them back.
    Gives nothing, or fails if the rows or the count changed.
    """
    target = tmp_path / "rows.jsonl"
    rows = [{"n": 1}, {"n": 2}, {"n": 3}]
    assert write_jsonl(target, rows) == 3
    assert read_jsonl(target) == rows


def test_write_jsonl_empty_iterable(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Writes an empty iterable as JSON Lines.
    Gives nothing, or fails if the count is not zero or the file is not empty.
    """
    target = tmp_path / "empty.jsonl"
    assert write_jsonl(target, []) == 0
    assert read_jsonl(target) == []


def test_iter_jsonl_skips_blank_lines(tmp_path: Path) -> None:
    """
    Takes a temporary directory fixture.
    Reads a file that has blank lines between records.
    Gives nothing, or fails if the blank lines were not skipped.
    """
    target = tmp_path / "gaps.jsonl"
    target.write_text('{"n": 1}\n\n   \n{"n": 2}\n', encoding="utf-8")
    assert list(iter_jsonl(target)) == [{"n": 1}, {"n": 2}]
