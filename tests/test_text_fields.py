"""Tests for label field access and Label construction."""

from __future__ import annotations

from typing import Any

from rx_label_search.text.fields import (
    display_brand_name,
    display_generic_name,
    field_text,
    field_values,
    label_from_record,
    label_text,
    openfda_values,
    text_fields_of,
)


def test_field_values_handles_missing_and_mixed() -> None:
    """
    Takes no arguments.
    Reads a missing field, a plain string field, and a mixed list.
    Gives nothing, or fails if any result is wrong.
    """
    assert field_values({}, "x") == ()
    assert field_values({"x": "one"}, "x") == ("one",)
    assert field_values({"x": ["a", 2, "b"]}, "x") == ("a", "b")
    assert field_text({"x": ["a", "b"]}, "x") == "a b"
    assert field_text({}, "x") == ""


def test_label_from_record_keeps_fields(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Converts the OxyContin fixture into a Label.
    Gives nothing, or fails if identifiers, text fields, or names are wrong.
    """
    label = label_from_record(fixture_labels["oxycontin"])
    assert label.set_id == "bfdfe235-d717-4855-a3c8-a13d26dadede"
    assert "Schedule II" in label_text(label, "controlled_substance")
    assert openfda_values(label, "route") == ("ORAL",)
    assert display_brand_name(label) == "OxyContin"
    assert display_generic_name(label) == "OXYCODONE HYDROCHLORIDE"
    assert label_text(label, "no_such_field") == ""


def test_text_fields_of_skips_openfda_and_empty() -> None:
    """
    Takes no arguments.
    Collects text fields from a record with openfda and a non-string list.
    Gives nothing, or fails if openfda or the empty list leaks through.
    """
    record = {"openfda": {"route": ["ORAL"]}, "warnings": ["w"], "nums": [1, 2]}
    assert text_fields_of(record) == {"warnings": ("w",)}
    label = label_from_record({})
    assert label.text_fields == {}
    assert display_brand_name(label) == ""
