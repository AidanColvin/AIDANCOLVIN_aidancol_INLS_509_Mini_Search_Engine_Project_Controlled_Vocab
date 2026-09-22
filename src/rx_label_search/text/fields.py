"""Pure access to label fields and conversion of raw records into Label records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rx_label_search.records import Label

MAIN_TEXT_FIELDS = (
    "indications_and_usage",
    "adverse_reactions",
    "warnings_and_cautions",
    "warnings",
    "boxed_warning",
    "contraindications",
    "drug_interactions",
)
WARNING_FIELDS = ("boxed_warning", "warnings_and_cautions", "warnings", "precautions", "drug_interactions", "contraindications")


def field_values(record: Mapping[str, Any], name: str) -> tuple[str, ...]:
    """
    Takes a raw label record or its openfda block and a field name.
    Reads the field and keeps only its string entries.
    Gives a tuple of strings, empty when the field is missing or not a list of strings.
    """
    value = record.get(name)
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, list):
        return ()
    return tuple(entry for entry in value if isinstance(entry, str))


def field_text(record: Mapping[str, Any], name: str) -> str:
    """
    Takes a raw label record and a field name.
    Joins the field's string entries with single spaces.
    Gives the joined text, empty when the field is missing.
    """
    return " ".join(field_values(record, name)).strip()


def text_fields_of(record: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """
    Takes a raw label record.
    Collects every top-level field whose value is a list of strings, skipping openfda.
    Gives a mapping from field name to its string entries, empty when there are none.
    """
    collected: dict[str, tuple[str, ...]] = {}
    for name, value in record.items():
        if name == "openfda" or not isinstance(value, list):
            continue
        strings = tuple(entry for entry in value if isinstance(entry, str))
        if strings:
            collected[name] = strings
    return collected


def openfda_fields_of(record: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """
    Takes a raw label record.
    Collects every openfda entry whose value is a list of strings.
    Gives a mapping from openfda key to its strings, empty when openfda is missing.
    """
    block = record.get("openfda")
    if not isinstance(block, Mapping):
        return {}
    return {name: field_values(block, name) for name in block if field_values(block, name)}


def label_from_record(record: Mapping[str, Any]) -> Label:
    """
    Takes a raw openFDA label record.
    Converts it into a frozen Label record with immutable field tuples.
    Gives the Label, with empty strings for missing identifiers.
    """
    return Label(
        label_id=str(record.get("id", "")),
        set_id=str(record.get("set_id", "")),
        version=str(record.get("version", "")),
        effective_time=str(record.get("effective_time", "")),
        text_fields=text_fields_of(record),
        openfda=openfda_fields_of(record),
    )


def label_text(label: Label, name: str) -> str:
    """
    Takes a Label and a text field name.
    Joins that field's entries with single spaces.
    Gives the joined text, empty when the label lacks the field.
    """
    return " ".join(label.text_fields.get(name, ())).strip()


def openfda_values(label: Label, name: str) -> tuple[str, ...]:
    """
    Takes a Label and an openfda key.
    Reads the key's string values.
    Gives the tuple of values, empty when the key is missing.
    """
    return label.openfda.get(name, ())


def display_brand_name(label: Label) -> str:
    """
    Takes a Label.
    Reads the first openfda brand name.
    Gives the name, or an empty string when the label has none.
    """
    names = openfda_values(label, "brand_name")
    return names[0] if names else ""


def display_generic_name(label: Label) -> str:
    """
    Takes a Label.
    Reads the first openfda generic name.
    Gives the name, or an empty string when the label has none.
    """
    names = openfda_values(label, "generic_name")
    return names[0] if names else ""
