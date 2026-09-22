"""Tests for T03, including its negative and established cases."""

from __future__ import annotations

from rx_label_search.records import Label
from rx_label_search.vocabulary.population import tag_t03_pediatric_indication


def test_t03_assigns_on_established_pediatric_use() -> None:
    """
    Takes no arguments.
    Checks a label stating safety and effectiveness were established in pediatric patients.
    Gives nothing, or fails if no evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"pediatric_use": ("Safety and effectiveness have been established in pediatric patients ages 6 to 17 years.",)}, {})
    assert tag_t03_pediatric_indication(label) is not None


def test_t03_omits_on_not_established() -> None:
    """
    Takes no arguments.
    Checks a label stating safety and effectiveness have not been established in pediatric patients.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"pediatric_use": ("Safety and effectiveness in pediatric patients have not been established.",)}, {})
    assert tag_t03_pediatric_indication(label) is None


def test_t03_omits_on_age_exclusion_only() -> None:
    """
    Takes no arguments.
    Checks a label that only excludes an age group without establishing use.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"pediatric_use": ("Safety and effectiveness in patients younger than 12 years have not been established.",)}, {})
    assert tag_t03_pediatric_indication(label) is None


def test_t03_omits_on_contraindicated_in_children() -> None:
    """
    Takes no arguments.
    Checks a label that contraindicates use in children.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"pediatric_use": ("This drug is contraindicated in children under 2 years of age.",)}, {})
    assert tag_t03_pediatric_indication(label) is None


def test_t03_checks_indications_and_usage_too() -> None:
    """
    Takes no arguments.
    Checks a label whose indications_and_usage names a pediatric indication.
    Gives nothing, or fails if no evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"indications_and_usage": ("This drug is indicated for the treatment of ADHD in pediatric patients 6 years and older.",)}, {})
    assert tag_t03_pediatric_indication(label) is not None


def test_t03_empty_label() -> None:
    """
    Takes no arguments.
    Checks a label with neither field.
    Gives nothing, or fails if evidence is returned.
    """
    assert tag_t03_pediatric_indication(Label("i", "s", "1", "20250101", {}, {})) is None
