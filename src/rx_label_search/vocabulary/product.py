"""Rules for T08 Single Active Ingredient and T09 Brand Name Product."""

from __future__ import annotations

from rx_label_search.records import Label, TermEvidence
from rx_label_search.text.fields import openfda_values
from rx_label_search.vocabulary.terms import RULE_VERSION

ANDA_PREFIX = "ANDA"


def tag_t08_single_active_ingredient(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Checks whether openfda.substance_name lists exactly one entry.
    Gives evidence naming the field and the entry, or None when there is not exactly one.
    """
    substances = openfda_values(label, "substance_name")
    if len(substances) != 1:
        return None
    return TermEvidence("T08", "openfda.substance_name", substances[0], RULE_VERSION)


def is_anda_product(application_numbers: tuple[str, ...]) -> bool:
    """
    Takes the openfda.application_number values.
    Checks whether any of them starts with the ANDA generic-approval prefix.
    Gives True when one does, False when none do or the list is empty.
    """
    return any(number.upper().startswith(ANDA_PREFIX) for number in application_numbers)


def brand_repeats_generic(brand_names: tuple[str, ...], generic_names: tuple[str, ...]) -> bool:
    """
    Takes the openfda.brand_name and openfda.generic_name values.
    Checks whether every brand name matches some generic name, ignoring case.
    Gives True when every brand name is also a generic name, False otherwise or when there is no brand name.
    """
    if not brand_names:
        return True
    lowered_generics = {name.lower() for name in generic_names}
    return all(name.lower() in lowered_generics for name in brand_names)


def tag_t09_brand_name_product(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Checks whether its brand name differs from its generic name, skipping ANDA products.
    Gives evidence naming the fields and both names, or None when there is no brand name, it repeats the generic name, or the product is an ANDA.
    """
    brand_names = openfda_values(label, "brand_name")
    generic_names = openfda_values(label, "generic_name")
    application_numbers = openfda_values(label, "application_number")
    if is_anda_product(application_numbers) or brand_repeats_generic(brand_names, generic_names):
        return None
    sentence = f"brand_name={', '.join(brand_names)}; generic_name={', '.join(generic_names)}"
    return TermEvidence("T09", "openfda.brand_name", sentence, RULE_VERSION)
