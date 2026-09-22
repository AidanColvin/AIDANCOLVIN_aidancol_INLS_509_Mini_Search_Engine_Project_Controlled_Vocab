"""Tests for the pure manifest helpers."""

from __future__ import annotations

import pytest

from rx_label_search.collect.manifest import (
    label_export_date,
    label_partitions,
    partition_filename,
    partition_from_entry,
)

SAMPLE = {
    "results": {
        "drug": {
            "label": {
                "export_date": "2026-09-18",
                "total_records": 3,
                "partitions": [
                    {"display_name": "/drug/label (part 1 of 1)", "file": "https://x/y/drug-label-0001-of-0001.json.zip", "size_mb": "1.5", "records": 3}
                ],
            }
        }
    }
}


def test_partition_from_entry_casts_types() -> None:
    """
    Takes no arguments.
    Converts a manifest entry whose size is a string.
    Gives nothing, or fails if the fields were not cast.
    """
    record = partition_from_entry(SAMPLE["results"]["drug"]["label"]["partitions"][0])
    assert record.size_mb == 1.5
    assert record.records == 3
    assert record.url.endswith(".json.zip")


def test_label_partitions_lists_all() -> None:
    """
    Takes no arguments.
    Reads the partitions from the sample manifest.
    Gives nothing, or fails if the count is wrong.
    """
    assert len(label_partitions(SAMPLE)) == 1


def test_label_partitions_empty_when_missing() -> None:
    """
    Takes no arguments.
    Reads partitions from a label section with none listed.
    Gives nothing, or fails if the result is not empty.
    """
    assert label_partitions({"results": {"drug": {"label": {}}}}) == ()


def test_label_export_date() -> None:
    """
    Takes no arguments.
    Reads the export date from the sample manifest.
    Gives nothing, or fails if the date is wrong.
    """
    assert label_export_date(SAMPLE) == "2026-09-18"


def test_partition_filename_and_empty() -> None:
    """
    Takes no arguments.
    Extracts a file name from a URL and rejects a URL with no segment.
    Gives nothing, or fails if either behavior is wrong.
    """
    assert partition_filename("https://a/b/c.zip") == "c.zip"
    with pytest.raises(ValueError):
        partition_filename("")
