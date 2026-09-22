"""Tests for T06 and T12 on fixtures and the avoid-only exclusion."""

from __future__ import annotations

from typing import Any

from rx_label_search.records import Label
from rx_label_search.text.fields import label_from_record
from rx_label_search.vocabulary.dosing import tag_t06_renal_dose_adjustment, tag_t12_hepatic_dose_adjustment


def test_t06_assigns_on_gabapentin_and_omits_on_oxycontin(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks the renal rule on gabapentin, which adjusts dose, and OxyContin, which does not.
    Gives nothing, or fails if either result is wrong.
    """
    assert tag_t06_renal_dose_adjustment(label_from_record(fixture_labels["gabapentin"])) is not None
    assert tag_t06_renal_dose_adjustment(label_from_record(fixture_labels["oxycontin"])) is None


def test_t12_assigns_on_oxycontin_and_venlafaxine(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks the hepatic rule on two labels that adjust dose for hepatic impairment.
    Gives nothing, or fails if either is missing.
    """
    assert tag_t12_hepatic_dose_adjustment(label_from_record(fixture_labels["oxycontin"])) is not None
    assert tag_t12_hepatic_dose_adjustment(label_from_record(fixture_labels["venlafaxine"])) is not None


def test_t06_omits_on_general_toxicity_warning_with_no_dose_change() -> None:
    """
    Takes no arguments.
    Checks a sentence that warns of kidney toxicity but gives no dose change.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"dosage_and_administration": ("This drug is known to be substantially excreted by the kidney, and toxic reactions may be more common in patients with impaired renal function.",)}, {})
    assert tag_t06_renal_dose_adjustment(label) is None


def test_t06_omits_on_no_dose_change_needed() -> None:
    """
    Takes no arguments.
    Checks a sentence that explicitly says no dose adjustment is needed.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"dosage_and_administration": ("No dose adjustment is needed in patients with renal impairment.",)}, {})
    assert tag_t06_renal_dose_adjustment(label) is None


def test_t06_omits_on_avoid_only_statement() -> None:
    """
    Takes no arguments.
    Checks a sentence that only says to avoid the drug below a kidney function level.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"precautions": ("Avoid use in patients with severe renal impairment.",)}, {})
    assert tag_t06_renal_dose_adjustment(label) is None


def test_t06_assigns_on_explicit_reduced_dose_sentence() -> None:
    """
    Takes no arguments.
    Checks a sentence that ties a creatinine clearance level to a specific reduced dose.
    Gives nothing, or fails if evidence is missing.
    """
    label = Label("i", "s", "1", "20250101", {"dosage_and_administration": ("In patients with creatinine clearance below 30 mL/min, reduce the dose to 5 mg once daily.",)}, {})
    assert tag_t06_renal_dose_adjustment(label) is not None


def test_t12_empty_label() -> None:
    """
    Takes no arguments.
    Checks a label with none of the three dosing fields.
    Gives nothing, or fails if evidence is returned.
    """
    assert tag_t12_hepatic_dose_adjustment(Label("i", "s", "1", "20250101", {}, {})) is None
