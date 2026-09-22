"""Tests for gold-set template construction, validation, and editing."""

from __future__ import annotations

from rx_label_search.evaluate.gold import (
    GOLD_SCHEMA_VERSION,
    PLACEHOLDER_RATIONALE,
    build_gold_template,
    gold_cells,
    set_gold_label,
    validate_gold_document,
)
from rx_label_search.vocabulary.terms import TERMS_BY_ID


def test_build_gold_template_has_every_term_for_every_set_id() -> None:
    """
    Takes no arguments.
    Builds a template for two set ids.
    Gives nothing, or fails if either set id lacks all 17 terms or the rationale is wrong.
    """
    template = build_gold_template(("s1", "s2"), "FAKE")
    assert set(template["labels"]) == {"s1", "s2"}
    assert set(template["labels"]["s1"]) == set(TERMS_BY_ID)
    assert all(cell["rationale"] == "FAKE" and cell["gold"] is False for cell in template["labels"]["s1"].values())


def test_build_gold_template_empty_set_ids() -> None:
    """
    Takes no arguments.
    Builds a template with no set ids.
    Gives nothing, or fails if labels is not empty.
    """
    assert build_gold_template((), "x")["labels"] == {}


def test_validate_gold_document_catches_bad_version_term_and_value() -> None:
    """
    Takes no arguments.
    Validates a document with a wrong version, an unknown term, and a non-boolean gold value.
    Gives nothing, or fails if any problem is missed.
    """
    document = {"schema_version": 2, "labels": {"s1": {"T99": {"gold": "yes"}, "T01": {"gold": "no"}}}}
    problems = validate_gold_document(document)
    assert any("schema_version" in p for p in problems)
    assert any("T99" in p for p in problems)
    assert any("T01" in p for p in problems)


def test_validate_gold_document_accepts_well_formed_document() -> None:
    """
    Takes no arguments.
    Validates a correctly shaped document.
    Gives nothing, or fails if any problem is reported.
    """
    document = {"schema_version": GOLD_SCHEMA_VERSION, "labels": {"s1": {"T01": {"gold": True, "rationale": "r"}}}}
    assert validate_gold_document(document) == ()


def test_set_gold_label_does_not_mutate_and_preserves_other_cells() -> None:
    """
    Takes no arguments.
    Sets one cell of a template built for two set ids.
    Gives nothing, or fails if the original template changed or another cell was disturbed.
    """
    template = build_gold_template(("s1",), "FAKE")
    updated = set_gold_label(template, "s1", "T06", True, "real reason")
    assert template["labels"]["s1"]["T06"]["gold"] is False
    assert updated["labels"]["s1"]["T06"] == {"gold": True, "rationale": "real reason"}
    assert updated["labels"]["s1"]["T01"]["rationale"] == "FAKE"


def test_set_gold_label_creates_new_set_id() -> None:
    """
    Takes no arguments.
    Sets a cell for a set id not present in the starting document.
    Gives nothing, or fails if the new set id is missing.
    """
    updated = set_gold_label({"schema_version": 1, "labels": {}}, "new-set", "T01", True, "r")
    assert updated["labels"]["new-set"]["T01"]["gold"] is True


def test_gold_cells_skips_placeholder_rationale() -> None:
    """
    Takes no arguments.
    Reads gold cells from a template where one cell was filled in and the rest are placeholders.
    Gives nothing, or fails if the placeholder cells appear or the filled cell is missing.
    """
    template = build_gold_template(("s1",), PLACEHOLDER_RATIONALE)
    filled = set_gold_label(template, "s1", "T06", True, "real reason")
    cells = gold_cells(filled)
    assert cells == (("s1", "T06", True),)


def test_gold_cells_empty_document() -> None:
    """
    Takes no arguments.
    Reads gold cells from a document with no labels.
    Gives nothing, or fails if the result is not empty.
    """
    assert gold_cells({"schema_version": 1, "labels": {}}) == ()
