"""Pure selection of the newest label per active-ingredient set."""

from __future__ import annotations

from collections.abc import Iterable

from rx_label_search.records import LabelSummary


def version_number(version: str) -> int:
    """
    Takes a label version string.
    Converts it to an integer for ordering.
    Gives the integer, or 0 when the string is not a plain number.
    """
    return int(version) if version.isdigit() else 0


def recency_key(summary: LabelSummary) -> tuple[str, int, str]:
    """
    Takes a label summary.
    Builds the ordering key of effective time, then numeric version, then id.
    Gives the tuple, where a larger tuple means a newer label.
    """
    return (summary.effective_time, version_number(summary.version), summary.label_id)


def newest_per_ingredient_set(summaries: Iterable[LabelSummary]) -> dict[tuple[str, ...], LabelSummary]:
    """
    Takes label summaries that all carry a non-empty ingredient set.
    Keeps, for each ingredient set, the summary with the largest recency key.
    Gives a mapping from ingredient set to its newest summary, empty for no input.
    """
    newest: dict[tuple[str, ...], LabelSummary] = {}
    for summary in summaries:
        current = newest.get(summary.ingredient_set)
        if current is None or recency_key(summary) > recency_key(current):
            newest[summary.ingredient_set] = summary
    return newest


def winner_ids(newest: dict[tuple[str, ...], LabelSummary]) -> frozenset[str]:
    """
    Takes the mapping of ingredient set to newest summary.
    Collects the label ids of the winners.
    Gives a frozenset of ids, empty when the mapping is empty.
    """
    return frozenset(summary.label_id for summary in newest.values())
