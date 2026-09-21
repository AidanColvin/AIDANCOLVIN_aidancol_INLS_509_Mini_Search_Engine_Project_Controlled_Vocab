"""Pure assembly of collection statistics."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from rx_label_search.collect.filters import (
    STAGE_DEDUPED,
    STAGE_INGREDIENTS,
    STAGE_OPENFDA,
    STAGE_RX,
    STAGE_TOTAL,
    filter_stage,
)
from rx_label_search.collect.filters import summarize_record
from rx_label_search.records import LabelSummary

STAGE_ORDER = (STAGE_TOTAL, STAGE_RX, STAGE_OPENFDA, STAGE_INGREDIENTS, STAGE_DEDUPED)


def scan_records(records: Iterable[Mapping[str, Any]]) -> tuple[Counter[str], list[LabelSummary]]:
    """
    Takes an iterable of raw label records.
    Counts the furthest filter stage each record reaches and summarizes the records that pass every filter.
    Gives the stage counter and the list of summaries, both empty for no records.
    """
    reached: Counter[str] = Counter()
    summaries: list[LabelSummary] = []
    for record in records:
        stage = filter_stage(record)
        reached[stage] += 1
        if stage == STAGE_INGREDIENTS:
            summaries.append(summarize_record(record))
    return reached, summaries


def cumulative_counts(reached: Mapping[str, int], deduped: int) -> dict[str, int]:
    """
    Takes a counter of the furthest stage each record reached and the de-duplicated count.
    Converts it into the number of records remaining after each filter in order.
    Gives a mapping from stage name to remaining count, with zeros for stages never reached.
    """
    ordered = (STAGE_TOTAL, STAGE_RX, STAGE_OPENFDA, STAGE_INGREDIENTS)
    remaining: dict[str, int] = {}
    for index, stage in enumerate(ordered):
        remaining[stage] = sum(reached.get(later, 0) for later in ordered[index:])
    remaining[STAGE_DEDUPED] = deduped
    return remaining


def build_stats(
    remaining: Mapping[str, int],
    export_date: str,
    build_date: str,
    partition_count: int,
) -> dict[str, Any]:
    """
    Takes the remaining counts per stage, the openFDA export date, the build date, and the partition count.
    Assembles the collection statistics document.
    Gives a JSON-ready dictionary.
    """
    return {
        "openfda_export_date": export_date,
        "build_date": build_date,
        "partitions": partition_count,
        "counts": {stage: int(remaining.get(stage, 0)) for stage in STAGE_ORDER},
    }
