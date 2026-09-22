"""Tests for T07 and T10, including the schedule discrimination and negation cases."""

from __future__ import annotations

from typing import Any

from rx_label_search.records import Label
from rx_label_search.text.fields import label_from_record
from rx_label_search.vocabulary.dea import (
    SCHEDULE_PATTERNS,
    tag_t07_controlled_substance,
    tag_t10_schedule_ii_controlled_substance,
)


def test_t07_and_t10_on_oxycontin_and_lyrica(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks a Schedule II label and a Schedule V label.
    Gives nothing, or fails if T10 fires on the Schedule V label or T07 is missing from either.
    """
    oxycontin = label_from_record(fixture_labels["oxycontin"])
    lyrica = label_from_record(fixture_labels["pregabalin_lyrica"])
    assert tag_t07_controlled_substance(oxycontin) is not None
    assert tag_t10_schedule_ii_controlled_substance(oxycontin) is not None
    assert tag_t07_controlled_substance(lyrica) is not None
    assert tag_t10_schedule_ii_controlled_substance(lyrica) is None


def test_t07_omits_when_not_scheduled() -> None:
    """
    Takes no arguments.
    Checks a sentence that explicitly says the drug is not a controlled substance.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"controlled_substance": ("Varenicline is not a controlled substance.",)}, {})
    assert tag_t07_controlled_substance(label) is None


def test_schedule_iii_does_not_match_schedule_ii_pattern() -> None:
    """
    Takes no arguments.
    Checks the Schedule II regex against Schedule III and C-III text.
    Gives nothing, or fails if either false-matches.
    """
    assert not SCHEDULE_PATTERNS["II"].search("This drug is a Schedule III controlled substance.")
    assert not SCHEDULE_PATTERNS["II"].search("Classified as C-III.")
    assert SCHEDULE_PATTERNS["II"].search("Classified as C-II.")


def test_t07_missing_field() -> None:
    """
    Takes no arguments.
    Checks a label with no controlled_substance field.
    Gives nothing, or fails if evidence is returned.
    """
    assert tag_t07_controlled_substance(Label("i", "s", "1", "20250101", {}, {})) is None
    assert tag_t10_schedule_ii_controlled_substance(Label("i", "s", "1", "20250101", {}, {})) is None
