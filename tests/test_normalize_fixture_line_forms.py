"""Tests for the prescription line forms the interaction-screen fixture types: thousands separators, combination strengths, mEq and mcg/h units, per-dose counts, weekly dosing, and meal, weekday, and site directions."""

from __future__ import annotations

import pytest

from rx_label_search.normalize.med_line_parser import (
    drop_thousands_separators,
    entry_daily_total,
    parse_combination_strength,
    parse_dose_count,
    parse_entry,
    parse_frequency,
    parse_med_list,
    parse_strength,
    split_entries,
)

FIXTURE_LINES: dict[str, str] = {
    "Coumadin 5 mg once daily on Monday": "Coumadin",
    "Xarelto 20 mg once daily with the evening meal": "Xarelto",
    "Latuda 80 mg once daily with food": "Latuda",
    "Multaq 400 mg twice daily with meals": "Multaq",
    "Vyvanse 70 mg once daily in the morning": "Vyvanse",
    "Nitrostat 0.4 mg as needed for chest pain": "Nitrostat",
    "Flonase 50 mcg per spray 2 sprays each nostril once daily": "Flonase",
    "Bactrim DS 800/160 mg twice daily": "Bactrim DS",
    "Sinemet 25/100 mg three times daily": "Sinemet",
    "Symbyax 6/25 mg once daily": "Symbyax",
    "Sprintec 0.25 mg/35 mcg once daily": "Sprintec",
    "Klor-Con 20 mEq once daily": "Klor-Con",
    "Trexall 15 mg once weekly": "Trexall",
    "Duragesic 25 mcg/h one patch every 72 hours": "Duragesic",
    "Tylenol 500 mg 2 tablets three times daily": "Tylenol",
    "Zosyn 3.375 g every 6 hours": "Zosyn",
    "Lantus 40 units once daily at bedtime": "Lantus",
    "Lyrica 100 mg tid": "Lyrica",
    "Albuterol 90 mcg 2 puffs as needed": "Albuterol",
}


def test_thousands_separator_comma_is_not_an_entry_separator() -> None:
    """
    Takes no arguments.
    Splits a list where "1,000 mg" carries a thousands-separator comma next to a real comma separator.
    Gives nothing, or fails if the number is split in two or the real separator is lost.
    """
    assert drop_thousands_separators("Glucophage 1,000 mg") == "Glucophage 1000 mg"
    assert drop_thousands_separators("Warfarin 5 mg,2.5 mg") == "Warfarin 5 mg,2.5 mg"
    assert split_entries("Glucophage 1,000 mg twice daily, Zoloft 50 mg") == ("Glucophage 1000 mg twice daily", "Zoloft 50 mg")
    entries = parse_med_list("Vancocin 1,000 mg every 12 hours")
    assert len(entries) == 1
    assert (entries[0].name_text, entries[0].strength_value, entries[0].daily_total) == ("Vancocin", 1000.0, 2000.0)


def test_combination_strength_is_removed_whole_and_keeps_the_first_number() -> None:
    """
    Takes no arguments.
    Parses slash-joined strengths with the unit at the end, a unit per component, and three components.
    Gives nothing, or fails if any first value, unit, or leftover text is wrong, or if a plain strength or a bare fraction is taken as a combination.
    """
    value, unit, remaining, notes = parse_combination_strength("Norco 10/325 mg qid")
    assert (value, unit, remaining.split()) == (10.0, "mg", ["Norco", "qid"])
    assert notes and "10/325 mg" in notes[0]
    assert parse_combination_strength("Sprintec 0.25 mg/35 mcg once daily")[:2] == (0.25, "mg")
    assert parse_combination_strength("Fioricet 50/325/40 mg")[:2] == (50.0, "mg")
    assert parse_combination_strength("Lyrica 100 mg tid") == (None, None, "Lyrica 100 mg tid", ())
    assert parse_combination_strength("Xanax 1/2 tablet") == (None, None, "Xanax 1/2 tablet", ())


def test_milliequivalent_and_continuous_rate_units_are_strengths() -> None:
    """
    Takes no arguments.
    Parses mEq, mcg/h, and mcg/hr strengths.
    Gives nothing, or fails if any value or normalized unit is wrong.
    """
    assert parse_strength("Klor-Con 20 mEq once daily")[:2] == (20.0, "mEq")
    assert parse_strength("Duragesic 25 mcg/h")[:2] == (25.0, "mcg/h")
    assert parse_strength("fentanyl 50 mcg/hr")[:2] == (50.0, "mcg/h")


def test_dose_count_is_removed_and_multiplied_into_the_daily_total() -> None:
    """
    Takes no arguments.
    Parses per-dose tablet, patch, and capsule counts as digits and words, then a whole line with a count.
    Gives nothing, or fails if the count is left in the name or the daily total ignores it.
    """
    assert parse_dose_count("Tylenol   2 tablets")[0] == 2.0
    assert parse_dose_count("Duragesic   one patch")[0] == 1.0
    assert parse_dose_count("Omega   3 caps")[0] == 3.0
    assert parse_dose_count("Lisinopril") == (None, "Lisinopril")
    entry = parse_entry("Tylenol 500 mg 2 tablets three times daily")
    assert (entry.name_text, entry.strength_value, entry.times_per_day, entry.daily_total) == ("Tylenol", 500.0, 3.0, 3000.0)
    assert any("per-dose count of 2" in note for note in entry.notes)
    assert parse_entry("Advil 200 mg 2 tablets twice daily").daily_total == 800.0
    assert entry_daily_total(None, "mg", 2.0, 3.0) is None
    assert entry_daily_total(10.0, "mg", None, 3.0) == 30.0


def test_weekly_dosing_gives_no_daily_total_and_a_note() -> None:
    """
    Takes no arguments.
    Parses "once weekly" and "every week" frequencies.
    Gives nothing, or fails if a daily total is computed, the note is missing, or the phrase leaks into the name.
    """
    times, notes, remaining = parse_frequency("Trexall once weekly")
    assert times is None
    assert any("weekly" in note for note in notes)
    assert remaining.split() == ["Trexall"]
    entry = parse_entry("Ozempic 1 mg once weekly")
    assert (entry.name_text, entry.strength_value, entry.daily_total) == ("Ozempic", 1.0, None)
    assert parse_frequency("methotrexate every week")[0] is None


def test_continuous_rate_daily_total_is_the_rate_itself() -> None:
    """
    Takes no arguments.
    Parses a transdermal patch line written as a mcg/h rate with a patch count and a 72-hour interval.
    Gives nothing, or fails if the daily total is scaled by the interval instead of staying at the rate.
    """
    entry = parse_entry("Duragesic 25 mcg/h one patch every 72 hours")
    assert (entry.name_text, entry.strength_value, entry.strength_unit, entry.daily_total) == ("Duragesic", 25.0, "mcg/h", 25.0)
    assert any("continuous rate" in note for note in entry.notes)


@pytest.mark.parametrize(("raw_text", "expected_name"), sorted(FIXTURE_LINES.items()))
def test_fixture_line_forms_parse_to_a_clean_name(raw_text: str, expected_name: str) -> None:
    """
    Takes one fixture-style line and the name it should reduce to.
    Parses the line with every direction, count, unit, and combination-strength rule applied.
    Gives nothing, or fails if the name text still carries dose, direction, or site text.
    """
    assert parse_entry(raw_text).name_text == expected_name


def test_existing_behaviors_are_unchanged() -> None:
    """
    Takes no arguments.
    Parses lines from the earlier acceptance set that carry no new forms.
    Gives nothing, or fails if their names, totals, or the puff-count stripping changed.
    """
    lyrica = parse_entry("Lyrica 100 mg tid")
    assert (lyrica.name_text, lyrica.daily_total) == ("Lyrica", 300.0)
    albuterol = parse_entry("Albuterol 90 mcg 2 puffs as needed")
    assert (albuterol.name_text, albuterol.daily_total) == ("Albuterol", None)
    assert parse_entry("Trazodone 50 mg 1 time daily at bedtime").name_text == "Trazodone"
