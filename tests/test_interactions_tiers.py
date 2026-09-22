"""Tests for heuristic tier assignment."""

from __future__ import annotations

from rx_label_search.interactions.tiers import (
    TIER_BOXED_WARNING,
    TIER_CONTRAINDICATED,
    TIER_WARNING,
    highest_tier,
    tier_for_field,
    tier_name,
)


def test_tier_for_field_maps_each_section() -> None:
    """
    Takes no arguments.
    Reads the tier for contraindications, boxed_warning, warnings, and an unmapped field.
    Gives nothing, or fails if any mapping is wrong.
    """
    assert tier_for_field("contraindications") == TIER_CONTRAINDICATED
    assert tier_for_field("boxed_warning") == TIER_BOXED_WARNING
    assert tier_for_field("warnings") == TIER_WARNING
    assert tier_for_field("drug_interactions") == 4
    assert tier_for_field("mechanism_of_action") is None


def test_tier_name_known_and_unknown() -> None:
    """
    Takes no arguments.
    Reads the name of a known tier, None, and an unmapped number.
    Gives nothing, or fails if any result is wrong.
    """
    assert tier_name(TIER_CONTRAINDICATED) == "Contraindicated"
    assert tier_name(None) == "Unknown"
    assert tier_name(99) == "Unknown"


def test_highest_tier_picks_the_lowest_number() -> None:
    """
    Takes no arguments.
    Finds the highest-priority tier among a mix of tiers and among all None.
    Gives nothing, or fails if either result is wrong.
    """
    assert highest_tier((3, 1, 2)) == 1
    assert highest_tier((None, None)) is None
    assert highest_tier(()) is None
