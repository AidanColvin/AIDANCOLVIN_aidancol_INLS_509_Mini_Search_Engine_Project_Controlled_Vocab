"""Tests for the medication list parser, including the Section 3.1 acceptance input."""

from __future__ import annotations

from rx_label_search.normalize.med_line_parser import (
    clean_name_text,
    daily_total,
    parse_entry,
    parse_frequency,
    parse_med_list,
    parse_strength,
    split_entries,
)

TEST_INPUT = (
    "10 mg Zyprexa X 1 daily , 20 mg adderall X 3 daily , 10 mg ambien X daily , trazdone 50 mg X 1 daily , "
    "desvenlafaxine 50 mg X 1 daily , Flexril 10 mg X 3 times daily , Lyrica 100 mg X 3 daily"
)


def test_acceptance_input_parses_seven_entries() -> None:
    """
    Takes no arguments.
    Parses the exact medication list from the build prompt.
    Gives nothing, or fails if any name, strength, frequency, or daily total differs from Section 3.6.
    """
    entries = parse_med_list(TEST_INPUT)
    assert len(entries) == 7
    expected = [
        ("Zyprexa", 10.0, "mg", 1.0, 10.0),
        ("adderall", 20.0, "mg", 3.0, 60.0),
        ("ambien", 10.0, "mg", 1.0, 10.0),
        ("trazdone", 50.0, "mg", 1.0, 50.0),
        ("desvenlafaxine", 50.0, "mg", 1.0, 50.0),
        ("Flexril", 10.0, "mg", 3.0, 30.0),
        ("Lyrica", 100.0, "mg", 3.0, 300.0),
    ]
    got = [(e.name_text, e.strength_value, e.strength_unit, e.times_per_day, e.daily_total) for e in entries]
    assert got == expected


def test_ambien_entry_carries_the_x_daily_note() -> None:
    """
    Takes no arguments.
    Parses the Ambien entry whose frequency is only "X daily".
    Gives nothing, or fails if the once-daily note is missing or another entry has it.
    """
    entries = parse_med_list(TEST_INPUT)
    assert any("once daily" in note for note in entries[2].notes)
    assert entries[0].notes == ()


def test_split_entries_handles_separators_and_blank() -> None:
    """
    Takes no arguments.
    Splits a list using commas, semicolons, and new lines, and an empty string.
    Gives nothing, or fails if the pieces are wrong.
    """
    assert split_entries("a, b; c\nd,,") == ("a", "b", "c", "d")
    assert split_entries("") == ()
    assert parse_med_list("  ") == ()


def test_parse_strength_units_and_decimals() -> None:
    """
    Takes no arguments.
    Parses decimal, microgram, milliliter, unit, and percent strengths and a line without one.
    Gives nothing, or fails if any value or unit is wrong.
    """
    assert parse_strength("0.5 mg x")[:2] == (0.5, "mg")
    assert parse_strength("levothyroxine 88mcg")[:2] == (88.0, "mcg")
    assert parse_strength("5 mL twice daily")[:2] == (5.0, "mL")
    assert parse_strength("10 units qhs")[:2] == (10.0, "units")
    assert parse_strength("cream 1% bid")[:2] == (1.0, "%")
    assert parse_strength("aspirin daily") == (None, None, "aspirin daily")


def test_parse_frequency_forms() -> None:
    """
    Takes no arguments.
    Parses every frequency form the specification lists.
    Gives nothing, or fails if any times-per-day value is wrong.
    """
    cases = {
        "x 2 daily": 2.0,
        "X 3 times daily": 3.0,
        "3 times daily": 3.0,
        "twice daily": 2.0,
        "three times a day": 3.0,
        "four times daily": 4.0,
        "once daily": 1.0,
        "daily": 1.0,
        "qd": 1.0,
        "bid": 2.0,
        "tid": 3.0,
        "qid": 4.0,
        "qhs": 1.0,
        "every 8 hours": 3.0,
        "q12h": 2.0,
        "every 6 hrs": 4.0,
    }
    for text, expected in cases.items():
        times, _, _ = parse_frequency(text)
        assert times == expected, text


def test_parse_frequency_missing_gives_note() -> None:
    """
    Takes no arguments.
    Parses text with no frequency expression.
    Gives nothing, or fails if times is not None or the note is missing.
    """
    times, notes, remaining = parse_frequency("aspirin")
    assert times is None
    assert notes
    assert remaining == "aspirin"


def test_unparseable_entry_is_kept_with_notes() -> None:
    """
    Takes no arguments.
    Parses an entry that has neither strength nor frequency and one with only a dose.
    Gives nothing, or fails if the entry is dropped or the notes do not explain the gaps.
    """
    entry = parse_entry("??")
    assert entry.name_text == "??"
    assert entry.daily_total is None
    assert any("no frequency" in note for note in entry.notes)
    assert any("no strength" in note for note in entry.notes)
    dose_only = parse_entry("10 mg")
    assert dose_only.name_text == ""
    assert any("no drug name" in note for note in dose_only.notes)


def test_clean_name_and_daily_total_edge_cases() -> None:
    """
    Takes no arguments.
    Cleans punctuation around a name and multiplies with missing values.
    Gives nothing, or fails if either helper mishandles the empty case.
    """
    assert clean_name_text(" - Lyrica : ") == "Lyrica"
    assert clean_name_text("") == ""
    assert daily_total(None, 2.0) is None
    assert daily_total(2.0, None) is None
    assert daily_total(2.0, 3.0) == 6.0
