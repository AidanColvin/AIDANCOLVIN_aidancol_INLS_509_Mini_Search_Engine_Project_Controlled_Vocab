"""Tests for stage counting and stats assembly."""

from __future__ import annotations

from collections import Counter
from typing import Any

from rx_label_search.collect.filters import STAGE_DEDUPED, STAGE_INGREDIENTS, STAGE_OPENFDA, STAGE_RX, STAGE_TOTAL
from rx_label_search.collect.stats import build_stats, cumulative_counts, scan_records


def test_scan_records_counts_and_summarizes(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Scans the fixtures plus two records that fail early.
    Gives nothing, or fails if the counts or summary count are wrong.
    """
    records = [*fixture_labels.values(), {}, {"openfda": {"product_type": ["HUMAN PRESCRIPTION DRUG"]}}]
    reached, summaries = scan_records(records)
    assert reached[STAGE_INGREDIENTS] == len(fixture_labels)
    assert reached[STAGE_TOTAL] == 1
    assert reached[STAGE_OPENFDA] == 1
    assert len(summaries) == len(fixture_labels)


def test_scan_records_empty() -> None:
    """
    Takes no arguments.
    Scans no records.
    Gives nothing, or fails if anything is counted.
    """
    reached, summaries = scan_records([])
    assert reached == Counter()
    assert summaries == []


def test_cumulative_counts_are_monotone() -> None:
    """
    Takes no arguments.
    Converts furthest-stage counts into remaining counts.
    Gives nothing, or fails if the remaining counts do not shrink stage by stage.
    """
    reached = Counter({STAGE_TOTAL: 5, STAGE_RX: 0, STAGE_OPENFDA: 2, STAGE_INGREDIENTS: 3})
    remaining = cumulative_counts(reached, 2)
    assert remaining == {STAGE_TOTAL: 10, STAGE_RX: 5, STAGE_OPENFDA: 5, STAGE_INGREDIENTS: 3, STAGE_DEDUPED: 2}


def test_build_stats_shape() -> None:
    """
    Takes no arguments.
    Assembles a stats document from remaining counts.
    Gives nothing, or fails if the keys or values are wrong.
    """
    stats = build_stats({STAGE_TOTAL: 1}, "2026-09-18", "2026-09-21", 14)
    assert stats["openfda_export_date"] == "2026-09-18"
    assert stats["counts"][STAGE_TOTAL] == 1
    assert stats["counts"][STAGE_DEDUPED] == 0
    assert stats["partitions"] == 14
