"""Tests for T08 and T09, including the ANDA and name-repeats-generic exclusions."""

from __future__ import annotations

from typing import Any

from rx_label_search.records import Label
from rx_label_search.text.fields import label_from_record
from rx_label_search.vocabulary.product import (
    brand_repeats_generic,
    is_anda_product,
    tag_t08_single_active_ingredient,
    tag_t09_brand_name_product,
)


def test_t08_on_entresto_and_oxycontin(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks a two-ingredient product and a one-ingredient product.
    Gives nothing, or fails if either result is wrong.
    """
    assert tag_t08_single_active_ingredient(label_from_record(fixture_labels["entresto"])) is None
    assert tag_t08_single_active_ingredient(label_from_record(fixture_labels["oxycontin"])) is not None


def test_t09_on_entresto_and_adderall_anda(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks Entresto, an NDA brand product, and the Adderall IR fixture, an ANDA product.
    Gives nothing, or fails if T09 fires on the ANDA product or is missing from Entresto.
    """
    assert tag_t09_brand_name_product(label_from_record(fixture_labels["entresto"])) is not None
    assert tag_t09_brand_name_product(label_from_record(fixture_labels["adderall"])) is None


def test_is_anda_product() -> None:
    """
    Takes no arguments.
    Checks an ANDA number, an NDA number, and an empty list.
    Gives nothing, or fails if any result is wrong.
    """
    assert is_anda_product(("ANDA040422",))
    assert not is_anda_product(("NDA022272",))
    assert not is_anda_product(())


def test_brand_repeats_generic() -> None:
    """
    Takes no arguments.
    Checks a brand that repeats the generic name, one that differs, and no brand name at all.
    Gives nothing, or fails if any result is wrong.
    """
    assert brand_repeats_generic(("Gabapentin",), ("GABAPENTIN",))
    assert not brand_repeats_generic(("OxyContin",), ("OXYCODONE HYDROCHLORIDE",))
    assert brand_repeats_generic((), ("GABAPENTIN",))


def test_t09_omits_when_brand_repeats_generic() -> None:
    """
    Takes no arguments.
    Checks a label whose brand name matches its generic name exactly.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {}, {"brand_name": ("Gabapentin",), "generic_name": ("GABAPENTIN",)})
    assert tag_t09_brand_name_product(label) is None
