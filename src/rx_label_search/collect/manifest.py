"""Pure helpers that read the openFDA download manifest structure."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rx_label_search.records import Partition


def label_section(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Takes the decoded openFDA download manifest.
    Looks up the drug label section under results, drug, label.
    Gives that section, or raises KeyError when the manifest lacks it.
    """
    return manifest["results"]["drug"]["label"]


def partition_from_entry(entry: Mapping[str, Any]) -> Partition:
    """
    Takes one partition entry from the manifest, whose size_mb is a string.
    Converts the entry into a Partition record.
    Gives the record, or raises KeyError or ValueError on a malformed entry.
    """
    return Partition(
        url=str(entry["file"]),
        display_name=str(entry["display_name"]),
        size_mb=float(entry["size_mb"]),
        records=int(entry["records"]),
    )


def label_partitions(manifest: Mapping[str, Any]) -> tuple[Partition, ...]:
    """
    Takes the decoded openFDA download manifest.
    Converts every drug label partition entry into a Partition record, in manifest order.
    Gives the tuple of records, empty when the label section lists no partitions.
    """
    entries = label_section(manifest).get("partitions", [])
    return tuple(partition_from_entry(entry) for entry in entries)


def label_export_date(manifest: Mapping[str, Any]) -> str:
    """
    Takes the decoded openFDA download manifest.
    Reads the export_date of the drug label section.
    Gives the date string, or raises KeyError when it is missing.
    """
    return str(label_section(manifest)["export_date"])


def partition_filename(url: str) -> str:
    """
    Takes a partition download URL.
    Extracts the last path segment.
    Gives the file name, or raises ValueError when the URL has no path segment.
    """
    name = url.rstrip("/").rsplit("/", 1)[-1]
    if not name:
        raise ValueError(f"URL has no file name: {url}")
    return name
