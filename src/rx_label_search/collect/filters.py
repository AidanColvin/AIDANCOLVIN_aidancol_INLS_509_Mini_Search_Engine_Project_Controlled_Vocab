"""Pure scope filters from Part 1 applied to raw openFDA label records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rx_label_search.records import LabelSummary

HUMAN_PRESCRIPTION = "HUMAN PRESCRIPTION DRUG"
STAGE_TOTAL = "total_records"
STAGE_RX = "after_filter_1_human_prescription"
STAGE_OPENFDA = "after_filter_2_has_openfda"
STAGE_INGREDIENTS = "after_filter_2b_has_substance_name"
STAGE_DEDUPED = "after_filter_3_newest_per_ingredient_set"


def openfda_block(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Takes a raw label record.
    Reads its openfda object.
    Gives the openfda mapping, empty when the record has none.
    """
    block = record.get("openfda")
    if not isinstance(block, Mapping):
        return {}
    return block


def has_openfda(record: Mapping[str, Any]) -> bool:
    """
    Takes a raw label record.
    Checks whether the record carries a non-empty openfda object.
    Gives True when it does, False when the object is missing or empty.
    """
    return bool(openfda_block(record))


def string_values(block: Mapping[str, Any], key: str) -> tuple[str, ...]:
    """
    Takes a mapping and a key whose value should be a list of strings.
    Reads the value and keeps only its string entries.
    Gives a tuple of strings, empty when the key is missing or holds no strings.
    """
    value = block.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(entry for entry in value if isinstance(entry, str))


def is_human_prescription(record: Mapping[str, Any]) -> bool:
    """
    Takes a raw label record.
    Checks whether openfda.product_type names a human prescription drug.
    Gives True when it does, False otherwise.
    """
    return HUMAN_PRESCRIPTION in string_values(openfda_block(record), "product_type")


def ingredient_set(record: Mapping[str, Any]) -> tuple[str, ...]:
    """
    Takes a raw label record.
    Builds the sorted, de-duplicated, uppercased set of openfda.substance_name values.
    Gives the tuple of names, empty when the record lists no substances.
    """
    names = {name.strip().upper() for name in string_values(openfda_block(record), "substance_name")}
    return tuple(sorted(name for name in names if name))


def summarize_record(record: Mapping[str, Any]) -> LabelSummary:
    """
    Takes a raw label record that passed the openfda filter.
    Extracts the identifiers, dates, ingredient set, and names needed for de-duplication.
    Gives a LabelSummary, with empty tuples where a name field is missing.
    """
    block = openfda_block(record)
    return LabelSummary(
        label_id=str(record.get("id", "")),
        set_id=str(record.get("set_id", "")),
        version=str(record.get("version", "")),
        effective_time=str(record.get("effective_time", "")),
        ingredient_set=ingredient_set(record),
        brand_names=string_values(block, "brand_name"),
        generic_names=string_values(block, "generic_name"),
    )


def filter_stage(record: Mapping[str, Any]) -> str:
    """
    Takes a raw label record.
    Applies the scope filters in order and finds the last stage the record passes.
    Gives STAGE_TOTAL, STAGE_RX, STAGE_OPENFDA, or STAGE_INGREDIENTS as the furthest stage reached.
    """
    if not is_human_prescription(record):
        return STAGE_TOTAL
    if not has_openfda(record):
        return STAGE_RX
    if not ingredient_set(record):
        return STAGE_OPENFDA
    return STAGE_INGREDIENTS
