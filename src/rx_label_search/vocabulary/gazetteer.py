"""Pure construction of the class-name gazetteer T17 needs, read only from data."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

_CLASS_FIELDS = ("pharm_class_epc", "pharm_class_moa")
_NAME_FIELDS = ("generic_name", "substance_name")
_MIN_GAZETTEER_NAME_LENGTH = 3
_MIN_DRUG_NAME_LENGTH = 5
_FOOTNOTE_PARENS = re.compile(r"\(([^()]*)\)")
_CLASS_SUFFIX = re.compile(r"\s*\[[A-Za-z/]+\]\s*$")


def strip_class_suffix(name: str) -> str:
    """
    Takes one openfda pharmacologic class string.
    Removes a trailing bracketed abbreviation such as " [EPC]" or " [MoA]", whatever its casing.
    Gives the plain class name, unchanged when it has no such suffix.
    """
    return _CLASS_SUFFIX.sub("", name)


def classes_from_openfda_block(block: Mapping[str, Any]) -> frozenset[str]:
    """
    Takes one label's openfda block.
    Collects its lowercase pharmacologic class names from pharm_class_epc and pharm_class_moa.
    Gives the frozenset of names, empty when the block carries neither field.
    """
    names: set[str] = set()
    for field_name in _CLASS_FIELDS:
        for value in block.get(field_name) or ():
            stripped = strip_class_suffix(str(value)).strip().lower()
            if stripped:
                names.add(stripped)
    return frozenset(names)


def classes_from_summaries(records: Iterable[Mapping[str, Any]]) -> frozenset[str]:
    """
    Takes raw label records or their openfda blocks.
    Collects every lowercase pharmacologic class name from pharm_class_epc and pharm_class_moa.
    Gives the frozenset of names, empty when no record carries either field.
    """
    names: set[str] = set()
    for record in records:
        names |= classes_from_openfda_block(record.get("openfda", record))
    return frozenset(names)


def strip_footnote_markers(cell: str) -> str:
    """
    Takes one enzyme-table cell's text.
    Removes any parenthesized group whose comma-separated tokens are all single letters, such as footnote markers.
    Gives the cell text with only those footnote groups removed, real parenthetical content such as abbreviations kept.
    """

    def replace_if_footnote(match: re.Match[str]) -> str:
        """
        Takes a regex match of one parenthesized group.
        Checks whether every non-empty comma-separated token inside is a single letter.
        Gives an empty string for a footnote group, the original text otherwise.
        """
        tokens = [token.strip() for token in match.group(1).split(",")]
        if all(len(token) <= 1 for token in tokens if token):
            return ""
        return match.group(0)

    return _FOOTNOTE_PARENS.sub(replace_if_footnote, cell)


def clean_name_piece(piece: str) -> str:
    """
    Takes one comma-separated piece of an enzyme-table cell, with footnote parentheses already removed.
    Lowercases it, strips leading and trailing punctuation and superscript markers, and drops short remnants.
    Gives the cleaned name, empty when nothing long enough remains.
    """
    cleaned = piece.strip(" .").lower()
    cleaned = "".join(char for char in cleaned if not char.isdigit() and char not in "^*")
    cleaned = cleaned.strip(" .()")
    return cleaned if len(cleaned) >= _MIN_GAZETTEER_NAME_LENGTH else ""


def names_from_enzyme_table(enzyme_table: Mapping[str, Any]) -> frozenset[str]:
    """
    Takes the decoded FDA enzyme table reference file.
    Collects every inhibitor, inducer, and substrate name across its tables, dropping footnote markers.
    Gives the frozenset of lowercase names, empty when the table has no matching columns.
    """
    names: set[str] = set()
    name_columns = {"Inhibitor", "Inducer", "Sensitive index substrates unless otherwise noted", "Strong index inhibitors", "Moderate index inhibitors", "Strong inducers", "Moderate inducers"}
    for table in enzyme_table.get("tables", ()):
        for row in table.get("rows", ()):
            for column, cell in row.items():
                if column not in name_columns or not cell:
                    continue
                without_footnotes = strip_footnote_markers(cell)
                for piece in without_footnotes.replace("\n", ",").split(","):
                    cleaned = clean_name_piece(piece)
                    if cleaned:
                        names.add(cleaned)
    return frozenset(names)


def drug_names_from_openfda_block(block: Mapping[str, Any]) -> frozenset[str]:
    """
    Takes one label's openfda block.
    Collects its lowercase generic and substance names that are at least five characters long.
    Gives the frozenset of names, empty when the block carries neither field.
    """
    names: set[str] = set()
    for field_name in _NAME_FIELDS:
        for value in block.get(field_name) or ():
            cleaned = str(value).strip().lower()
            if len(cleaned) >= _MIN_DRUG_NAME_LENGTH:
                names.add(cleaned)
    return frozenset(names)


def drug_names_from_summaries(records: Iterable[Mapping[str, Any]]) -> frozenset[str]:
    """
    Takes raw label records or their openfda blocks.
    Collects every lowercase generic and substance name at least five characters long.
    Gives the frozenset of names, empty when no record carries either field.
    """
    names: set[str] = set()
    for record in records:
        names |= drug_names_from_openfda_block(record.get("openfda", record))
    return frozenset(names)


def build_class_gazetteer(records: Iterable[Mapping[str, Any]], enzyme_table: Mapping[str, Any]) -> frozenset[str]:
    """
    Takes the collection's raw label records, each visited exactly once, and the decoded FDA enzyme table.
    Combines the collection's own pharmacologic classes and drug names with the enzyme table's names.
    Gives the merged frozenset of lowercase class and drug names.
    """
    names: set[str] = set()
    for record in records:
        block = record.get("openfda", record)
        names |= classes_from_openfda_block(block)
        names |= drug_names_from_openfda_block(block)
    return frozenset(names) | names_from_enzyme_table(enzyme_table)
