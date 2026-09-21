"""Tests for the scope filters against fixture labels and edge cases."""

from __future__ import annotations

from typing import Any

from rx_label_search.collect.filters import (
    STAGE_INGREDIENTS,
    STAGE_OPENFDA,
    STAGE_RX,
    STAGE_TOTAL,
    filter_stage,
    has_openfda,
    ingredient_set,
    is_human_prescription,
    string_values,
    summarize_record,
)


def test_fixtures_pass_every_filter(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Runs every fixture through the filter stages.
    Gives nothing, or fails if any fixture does not reach the last stage.
    """
    for name, record in fixture_labels.items():
        assert filter_stage(record) == STAGE_INGREDIENTS, name


def test_adderall_ingredient_set_is_sorted_and_four_salts(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Builds the ingredient set of the Adderall fixture.
    Gives nothing, or fails if it is not the four sorted salt names.
    """
    assert ingredient_set(fixture_labels["adderall"]) == (
        "AMPHETAMINE ASPARTATE MONOHYDRATE",
        "AMPHETAMINE SULFATE",
        "DEXTROAMPHETAMINE SACCHARATE",
        "DEXTROAMPHETAMINE SULFATE",
    )


def test_empty_openfda_fails_filter() -> None:
    """
    Takes no arguments.
    Checks records with a missing, empty, and non-prescription openfda block.
    Gives nothing, or fails if any of them passes the wrong stage.
    """
    assert not has_openfda({})
    assert not has_openfda({"openfda": {}})
    assert filter_stage({"openfda": {}}) == STAGE_TOTAL
    assert filter_stage({"openfda": {"product_type": ["HUMAN OTC DRUG"]}}) == STAGE_TOTAL
    assert filter_stage({"openfda": {"product_type": ["HUMAN PRESCRIPTION DRUG"]}}) == STAGE_OPENFDA
    assert is_human_prescription({"openfda": {"product_type": ["HUMAN PRESCRIPTION DRUG"]}})


def test_filter_stage_rx_without_openfda_is_unreachable() -> None:
    """
    Takes no arguments.
    Confirms the second stage constant exists for reporting even though filter 1 already needs openfda.
    Gives nothing, or fails if the constant names collide.
    """
    assert STAGE_RX != STAGE_TOTAL


def test_string_values_ignores_non_strings() -> None:
    """
    Takes no arguments.
    Reads a field that mixes strings with other types and one that is missing.
    Gives nothing, or fails if non-strings leak through or the missing case is not empty.
    """
    assert string_values({"k": ["a", 1, None, "b"]}, "k") == ("a", "b")
    assert string_values({}, "k") == ()


def test_summarize_record_reads_names(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Summarizes the Zyprexa fixture.
    Gives nothing, or fails if the brand names or ingredient set are wrong.
    """
    summary = summarize_record(fixture_labels["olanzapine_zyprexa"])
    assert "Zyprexa" in summary.brand_names
    assert summary.ingredient_set == ("OLANZAPINE",)
    assert summary.set_id == "b418946a-1ab4-4d89-a012-d94fc361a3c4"
