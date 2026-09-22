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
    strip_trailing_directions,
)

# Every entry from results/report.md whose name text was broken by Bug 1
# ("1 time daily", singular, not recognized as a frequency phrase) or Bug 2
# (a trailing "as needed" / "at bedtime" qualifier left attached to the
# name after a correctly recognized frequency). Expected values are the
# clean name text after both fixes. The Albuterol and Fluticasone entries
# still carry their leftover administration count ("2 puffs", "2 sprays")
# because inhaler/spray dose forms are not one of the three trailing
# directions Section 7.1 names to strip; see reports/OPEN_QUESTIONS.md.
REPORT_MD_FAILING_EXAMPLES: dict[str, str] = {
    "Zolpidem 10 mg 1 time daily": "Zolpidem",
    "Lisinopril 10 mg 1 time daily": "Lisinopril",
    "Atorvastatin 20 mg 1 time daily": "Atorvastatin",
    "Sertraline 50 mg 1 time daily": "Sertraline",
    "Omeprazole 20 mg 1 time daily": "Omeprazole",
    "Amlodipine 5 mg 1 time daily": "Amlodipine",
    "Simvastatin 20 mg 1 time daily": "Simvastatin",
    "Losartan 50 mg 1 time daily": "Losartan",
    "Levothyroxine 50 mcg 1 time daily": "Levothyroxine",
    "Hydrochlorothiazide 25 mg 1 time daily": "Hydrochlorothiazide",
    "Metoprolol Succinate 50 mg 1 time daily": "Metoprolol Succinate",
    "Escitalopram 10 mg 1 time daily": "Escitalopram",
    "Pantoprazole 40 mg 1 time daily": "Pantoprazole",
    "Montelukast 10 mg 1 time daily": "Montelukast",
    "Rosuvastatin 10 mg 1 time daily": "Rosuvastatin",
    "Valsartan 80 mg 1 time daily": "Valsartan",
    "Pravastatin 20 mg 1 time daily": "Pravastatin",
    "Duloxetine 30 mg 1 time daily": "Duloxetine",
    "Albuterol 90 mcg 2 puffs as needed": "Albuterol 2 puffs",
    "Furosemide 20 mg 1 time daily": "Furosemide",
    "Spironolactone 25 mg 1 time daily": "Spironolactone",
    "Warfarin 5 mg 1 time daily": "Warfarin",
    "Digoxin 125 mcg 1 time daily": "Digoxin",
    "Bupropion XL 150 mg 1 time daily": "Bupropion XL",
    "Trazodone 50 mg 1 time daily at bedtime": "Trazodone",
    "Ibuprofen 600 mg 3 times daily as needed": "Ibuprofen",
    "Cyclobenzaprine 10 mg 3 times daily as needed": "Cyclobenzaprine",
    "Fluticasone 50 mcg 2 sprays daily": "Fluticasone 2 sprays",
    "Empagliflozin 10 mg 1 time daily": "Empagliflozin",
    "Telmisartan 40 mg 1 time daily": "Telmisartan",
    "Ezetimibe 10 mg 1 time daily": "Ezetimibe",
    "Venlafaxine ER 75 mg 1 time daily": "Venlafaxine ER",
    "Esomeprazole 40 mg 1 time daily": "Esomeprazole",
    "Meloxicam 15 mg 1 time daily": "Meloxicam",
    "Diltiazem ER 180 mg 1 time daily": "Diltiazem ER",
    "Allopurinol 100 mg 1 time daily": "Allopurinol",
    "Tamsulosin 0.4 mg 1 time daily": "Tamsulosin",
    "Acetaminophen 500 mg 4 times daily as needed": "Acetaminophen",
    "Sitagliptin 100 mg 1 time daily": "Sitagliptin",
    "Nifedipine ER 30 mg 1 time daily": "Nifedipine ER",
    "Lovastatin 20 mg 1 time daily": "Lovastatin",
    "Fluoxetine 20 mg 1 time daily": "Fluoxetine",
    "Famotidine 40 mg 1 time daily": "Famotidine",
    "Cetirizine 10 mg 1 time daily": "Cetirizine",
    "Ramipril 5 mg 1 time daily": "Ramipril",
    "Chlorthalidone 25 mg 1 time daily": "Chlorthalidone",
    "Pitavastatin 2 mg 1 time daily": "Pitavastatin",
    "Paroxetine 20 mg 1 time daily": "Paroxetine",
    "Dicyclomine 20 mg 4 times daily as needed": "Dicyclomine",
    "Loratadine 10 mg 1 time daily": "Loratadine",
}

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


def test_singular_one_time_daily_is_recognized() -> None:
    """
    Takes no arguments.
    Parses "1 time daily" (singular "time"), the numeral form results/report.md's Bug 1 describes.
    Gives nothing, or fails if the frequency is not read as once daily.
    """
    times, _, remaining = parse_frequency("1 time daily")
    assert times == 1.0
    assert "1 time" not in remaining


def test_strip_trailing_directions_removes_as_needed_prn_and_bedtime() -> None:
    """
    Takes no arguments.
    Strips "as needed", "as necessary", "PRN", and "at bedtime" from entry text.
    Gives nothing, or fails if a direction survives or unrelated text is touched.
    """
    assert strip_trailing_directions("Trazodone   at bedtime").strip() == "Trazodone"
    assert strip_trailing_directions("Ibuprofen   as needed").strip() == "Ibuprofen"
    assert strip_trailing_directions("Ibuprofen   as necessary").strip() == "Ibuprofen"
    assert strip_trailing_directions("Ibuprofen   PRN").strip() == "Ibuprofen"
    assert strip_trailing_directions("Lisinopril") == "Lisinopril"


def test_report_md_failing_examples_now_parse_to_a_clean_name() -> None:
    """
    Takes no arguments.
    Parses every entry results/report.md logged as unresolved because of Bug 1 or Bug 2.
    Gives nothing, or fails if any entry's name text still carries leftover dose or direction text.
    """
    for raw_text, expected_name in REPORT_MD_FAILING_EXAMPLES.items():
        entry = parse_entry(raw_text)
        assert entry.name_text == expected_name, raw_text


def test_dose_text_no_longer_leaks_into_the_matched_name() -> None:
    """
    Takes no arguments.
    Parses "Lisinopril 1 time daily", which results/report.md shows leaking "1 time" into the RxNorm query.
    Gives nothing, or fails if the parsed name still contains the dose fragment "1 time".
    """
    entry = parse_entry("Lisinopril 10 mg 1 time daily")
    assert entry.name_text == "Lisinopril"


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
