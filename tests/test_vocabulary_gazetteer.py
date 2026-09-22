"""Tests for the class gazetteer, including the footnote-marker bug fix."""

from __future__ import annotations

from pathlib import Path

from rx_label_search.storage.read_json import read_json
from rx_label_search.vocabulary.gazetteer import (
    build_class_gazetteer,
    classes_from_summaries,
    clean_name_piece,
    names_from_enzyme_table,
    strip_class_suffix,
    strip_footnote_markers,
)

ENZYME_TABLE = read_json(Path(__file__).resolve().parent.parent / "data" / "reference" / "fda_enzyme_table.json")


def test_strip_class_suffix() -> None:
    """
    Takes no arguments.
    Strips a known suffix and leaves a name with none unchanged.
    Gives nothing, or fails if either result is wrong.
    """
    assert strip_class_suffix("Atypical Antipsychotic [EPC]") == "Atypical Antipsychotic"
    assert strip_class_suffix("Plain Name") == "Plain Name"


def test_classes_from_summaries_reads_epc_and_moa() -> None:
    """
    Takes no arguments.
    Reads classes from two records, one with an openfda block and one without.
    Gives nothing, or fails if either class is missing or an empty record raises.
    """
    records = [{"openfda": {"pharm_class_epc": ["Atypical Antipsychotic [EPC]"], "pharm_class_moa": ["Serotonin Antagonist [MoA]"]}}, {}]
    names = classes_from_summaries(records)
    assert "atypical antipsychotic" in names
    assert "serotonin antagonist" in names
    assert classes_from_summaries([]) == frozenset()


def test_strip_footnote_markers_removes_letter_groups_but_keeps_abbreviations() -> None:
    """
    Takes no arguments.
    Strips a footnote-marker group and a doubled-comma footnote group, and keeps a real abbreviation in parens.
    Gives nothing, or fails if any case is handled wrong.
    """
    assert strip_footnote_markers("cyclosporine(a,b,d,,h,i)") == "cyclosporine"
    assert strip_footnote_markers("furafylline(a)") == "furafylline"
    assert strip_footnote_markers("bromosulfophthalein (BSP)") == "bromosulfophthalein (BSP)"


def test_clean_name_piece_drops_short_remnants() -> None:
    """
    Takes no arguments.
    Cleans a normal drug name and a bare footnote-letter remnant.
    Gives nothing, or fails if either result is wrong.
    """
    assert clean_name_piece(" Midazolam1 ") == "midazolam"
    assert clean_name_piece("b") == ""
    assert clean_name_piece("") == ""


def test_names_from_enzyme_table_has_no_footnote_only_entries() -> None:
    """
    Takes the real committed enzyme table.
    Builds its name gazetteer.
    Gives nothing, or fails if any entry is shorter than three characters.
    """
    names = names_from_enzyme_table(ENZYME_TABLE)
    assert names
    assert all(len(name) >= 3 for name in names)
    assert "midazolam" in names or any("midazolam" in name for name in names)


def test_build_class_gazetteer_merges_both_sources() -> None:
    """
    Takes the real committed enzyme table.
    Builds the merged gazetteer with one collection record.
    Gives nothing, or fails if either source's contribution is missing.
    """
    gazetteer = build_class_gazetteer([{"openfda": {"pharm_class_epc": ["Test Class [EPC]"]}}], ENZYME_TABLE)
    assert "test class" in gazetteer
    assert len(gazetteer) > 1


def test_drug_names_from_summaries_filters_short_names() -> None:
    """
    Takes no arguments.
    Reads drug names from a record with a long name and a short one.
    Gives nothing, or fails if the short name is kept or the long one is missing.
    """
    from rx_label_search.vocabulary.gazetteer import drug_names_from_summaries

    records = [{"openfda": {"generic_name": ["Febuxostat"], "substance_name": ["ABC"]}}]
    names = drug_names_from_summaries(records)
    assert "febuxostat" in names
    assert "abc" not in names


def test_build_class_gazetteer_includes_drug_names() -> None:
    """
    Takes the real committed enzyme table.
    Builds the merged gazetteer with one record naming a long generic name.
    Gives nothing, or fails if that name is missing from the result.
    """
    gazetteer = build_class_gazetteer([{"openfda": {"generic_name": ["Azathioprine"]}}], ENZYME_TABLE)
    assert "azathioprine" in gazetteer


def test_build_class_gazetteer_consumes_a_generator_only_once() -> None:
    """
    Takes the real committed enzyme table.
    Builds the gazetteer from a one-shot generator carrying both a class and a long drug name.
    Gives nothing, or fails if either name is missing, which would mean the generator was exhausted early.
    """
    from collections.abc import Iterator
    from typing import Any

    def one_shot() -> Iterator[dict[str, Any]]:
        """
        Takes no arguments.
        Yields one record with a class and a drug name.
        Gives an iterator of one record.
        """
        yield {"openfda": {"pharm_class_epc": ["Test Class [EPC]"], "generic_name": ["Azathioprine"]}}

    gazetteer = build_class_gazetteer(one_shot(), ENZYME_TABLE)
    assert "test class" in gazetteer
    assert "azathioprine" in gazetteer
