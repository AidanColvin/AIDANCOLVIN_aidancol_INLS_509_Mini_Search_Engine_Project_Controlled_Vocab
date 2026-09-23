"""Pure parsing of free-text medication lists into MedEntry records."""

from __future__ import annotations

import re

from rx_label_search.records import MedEntry

ENTRY_SEPARATORS = re.compile(r"[,;\n]+")
THOUSANDS_SEPARATOR = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
_NUMBER = r"\d+(?:\.\d+)?"
_UNIT = r"mcg/hr?|mg|mcg|g|ml|meq|units?|%"
STRENGTH = re.compile(rf"(?<![\w.])({_NUMBER})\s*({_UNIT})(?![a-z])", re.IGNORECASE)
COMBINATION_STRENGTH = re.compile(rf"(?<![\w.])({_NUMBER})\s*({_UNIT})?(?:\s*/\s*{_NUMBER}\s*(?:{_UNIT})?)+(?![a-z/])", re.IGNORECASE)
UNIT_WORD = re.compile(_UNIT, re.IGNORECASE)
UNIT_NAMES = {"mg": "mg", "mcg": "mcg", "g": "g", "ml": "mL", "meq": "mEq", "mcg/h": "mcg/h", "mcg/hr": "mcg/h", "unit": "units", "units": "units", "%": "%"}
CONTINUOUS_RATE_UNIT = "mcg/h"
WORD_COUNTS = {"once": 1.0, "twice": 2.0, "three times": 3.0, "four times": 4.0}
ABBREVIATION_COUNTS = {"qd": 1.0, "bid": 2.0, "tid": 3.0, "qid": 4.0, "qhs": 1.0}
DAILY_WORD = r"(?:a\s*|per\s*|/\s*)?(?:daily|day|d\b)"
FREQUENCY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bx\s*(\d+)\s*(?:times\s*)?" + DAILY_WORD, "times"),
    (r"\b(\d+)\s*(?:times|time|x)\s*" + DAILY_WORD, "times"),
    (r"\b(once|twice|three times|four times)\s*" + DAILY_WORD, "words"),
    (r"\b(qd|bid|tid|qid|qhs)\b", "abbrev"),
    (r"\b(?:every|q)\s*(\d+)\s*(?:hours|hrs|hr|h)\b", "hours"),
    (r"\bq(\d+)h\b", "hours"),
    (r"\bx\s*(daily|day)\b", "bare_x"),
    (r"\b(?:once\s+|twice\s+)?(weekly|every\s+week|each\s+week|once\s+a\s+week|q\s*week|q7d)\b", "weekly"),
    (r"\b(daily|once a day|every day)\b", "bare"),
)
_COMPILED = tuple((re.compile(pattern, re.IGNORECASE), kind) for pattern, kind in FREQUENCY_PATTERNS)
_TRAILING_JUNK = re.compile(r"^[\s\-–:.]+|[\s\-–:.]+$")
TRAILING_DIRECTIONS = re.compile(
    r"\b(?:as\s+needed(?:\s+for\b.*)?|as\s+necessary|prn|at\s+bedtime|at\s+night"
    r"|in\s+the\s+(?:morning|evening|afternoon)"
    r"|(?:with|before|after)\s+(?:the\s+|a\s+)?(?:evening\s+|morning\s+)?(?:food|meals?|breakfast|lunch|dinner|supper)"
    r"|on\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?)\b",
    re.IGNORECASE,
)
ADMINISTRATION_QUANTITY = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:puffs?|sprays?|inhalations?|actuations?|drops?)\b"
    r"|\b(?:in\s+)?each\s+(?:nostril|eye|ear)\b"
    r"|\bper\s+(?:spray|puff|tablet|capsule|dose|actuation|patch)\b",
    re.IGNORECASE,
)
DOSE_COUNT = re.compile(r"\b(\d+|one|two|three|four)\s*(?:tablets?|tabs?|capsules?|caps?|pills?|patch(?:es)?)\b", re.IGNORECASE)
COUNT_WORDS = {"one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0}


def drop_thousands_separators(text: str) -> str:
    """
    Takes a free-text medication list.
    Removes a comma that sits between a digit and exactly three more digits, as in "1,000 mg", so it is not taken as an entry separator.
    Gives the text with those commas removed, unchanged when it has none.
    """
    return THOUSANDS_SEPARATOR.sub("", text)


def split_entries(text: str) -> tuple[str, ...]:
    """
    Takes a free-text medication list.
    Splits it at commas, semicolons, and new lines, after removing thousands-separator commas inside numbers.
    Gives the tuple of non-empty trimmed entries, empty for blank input.
    """
    return tuple(part.strip() for part in ENTRY_SEPARATORS.split(drop_thousands_separators(text)) if part.strip())


def parse_combination_strength(text: str) -> tuple[float | None, str | None, str, tuple[str, ...]]:
    """
    Takes one medication entry.
    Finds a slash-joined combination strength such as "10/325 mg" or "0.25 mg/35 mcg" and removes the whole expression from the entry.
    Gives the first component's value, its unit (the expression's last unit when the first component has none), the remaining text, and a note, with None values and no note when the entry has no combination strength.
    """
    match = COMBINATION_STRENGTH.search(text)
    if match is None:
        return None, None, text, ()
    units = UNIT_WORD.findall(match.group(0))
    if not units:
        return None, None, text, ()
    unit = UNIT_NAMES[(match.group(2) or units[-1]).lower()]
    remaining = text[: match.start()] + " " + text[match.end() :]
    note = f'combination strength "{match.group(0).strip()}": daily total computed from the first number only'
    return float(match.group(1)), unit, remaining, (note,)


def parse_strength(text: str) -> tuple[float | None, str | None, str]:
    """
    Takes one medication entry.
    Finds the first number followed by a strength unit and removes it from the entry.
    Gives the value, the normalized unit, and the remaining text, with None values when no strength is present.
    """
    match = STRENGTH.search(text)
    if match is None:
        return None, None, text
    unit = UNIT_NAMES[match.group(2).lower()]
    remaining = text[: match.start()] + " " + text[match.end() :]
    return float(match.group(1)), unit, remaining


def frequency_value(kind: str, captured: str) -> float:
    """
    Takes the kind of frequency pattern that matched and its captured group.
    Converts the capture into times per day.
    Gives the times per day as a float.
    """
    if kind == "times":
        return float(captured)
    if kind == "words":
        return WORD_COUNTS[captured.lower()]
    if kind == "abbrev":
        return ABBREVIATION_COUNTS[captured.lower()]
    if kind == "hours":
        return 24.0 / float(captured)
    return 1.0


def frequency_note(kind: str, matched_text: str) -> tuple[str, ...]:
    """
    Takes the kind of frequency pattern that matched and the matched text.
    Writes a parse note when the frequency was inferred rather than stated as a count.
    Gives a tuple with one note, or an empty tuple when no note is needed.
    """
    if kind == "bare_x":
        return (f'frequency read as once daily from "{matched_text.strip()}"',)
    if kind == "bare":
        return (f'frequency read as once daily from "{matched_text.strip()}"',)
    if kind == "hours":
        return (f'times per day computed as 24 divided by the hours in "{matched_text.strip()}"',)
    if kind == "weekly":
        return (f'weekly dosing read from "{matched_text.strip()}"; daily total not computed',)
    return ()


def parse_frequency(text: str) -> tuple[float | None, tuple[str, ...], str]:
    """
    Takes one medication entry with its strength already removed.
    Finds the first frequency expression and removes it from the entry.
    Gives the times per day, any parse notes, and the remaining text, with None and a note when no frequency is found.
    """
    for pattern, kind in _COMPILED:
        match = pattern.search(text)
        if match is None:
            continue
        captured = match.group(1) if match.groups() else ""
        remaining = text[: match.start()] + " " + text[match.end() :]
        if kind == "weekly":
            return None, frequency_note(kind, match.group(0)), remaining
        return frequency_value(kind, captured), frequency_note(kind, match.group(0)), remaining
    return None, ("no frequency found; daily total not computed",), text


def strip_trailing_directions(text: str) -> str:
    """
    Takes the entry text left after strength and frequency were removed.
    Removes standalone dosing directions such as "as needed", "PRN", and "at bedtime".
    Gives the text with those directions removed, unchanged when none are present.
    """
    return TRAILING_DIRECTIONS.sub(" ", text)


def strip_administration_quantity(text: str) -> str:
    """
    Takes the entry text left after strength, frequency, and directions were removed.
    Removes a per-dose administration count such as "2 puffs", "2 sprays", or "3 drops", and site or per-unit phrases such as "each nostril" and "per spray".
    Gives the text with those phrases removed, unchanged when none is present.
    """
    return ADMINISTRATION_QUANTITY.sub(" ", text)


def parse_dose_count(text: str) -> tuple[float | None, str]:
    """
    Takes the entry text left after strength and frequency were removed.
    Finds a per-dose unit count such as "2 tablets", "one patch", or "3 caps" and removes it from the entry.
    Gives the count and the remaining text, or None and the unchanged text when no count is present.
    """
    match = DOSE_COUNT.search(text)
    if match is None:
        return None, text
    captured = match.group(1).lower()
    count = COUNT_WORDS[captured] if captured in COUNT_WORDS else float(captured)
    return count, text[: match.start()] + " " + text[match.end() :]


def clean_name_text(text: str) -> str:
    """
    Takes the entry text left after strength, frequency, and directions were removed.
    Collapses whitespace and strips leading or trailing punctuation.
    Gives the cleaned drug name text, empty when nothing remains.
    """
    collapsed = " ".join(text.split())
    return _TRAILING_JUNK.sub("", collapsed).strip()


def daily_total(strength_value: float | None, times_per_day: float | None) -> float | None:
    """
    Takes a strength value and times per day.
    Multiplies them.
    Gives the daily total, or None when either input is missing.
    """
    if strength_value is None or times_per_day is None:
        return None
    return strength_value * times_per_day


def entry_daily_total(strength_value: float | None, unit: str | None, dose_count: float | None, times_per_day: float | None) -> float | None:
    """
    Takes the unit strength, its unit, the per-dose unit count, and times per day.
    Multiplies the strength by the count (1 when absent) and the times per day, except that a continuous mcg/h rate is its own daily figure.
    Gives the daily total, or None when the strength or times per day is missing.
    """
    if unit == CONTINUOUS_RATE_UNIT:
        return strength_value
    scaled = daily_total(strength_value, times_per_day)
    if scaled is None or dose_count is None:
        return scaled
    return scaled * dose_count


def parse_entry(raw_text: str) -> MedEntry:
    """
    Takes one raw medication entry.
    Extracts the strength, the frequency, and the remaining name text.
    Gives a MedEntry, with an empty name and a note when no name text remains.
    """
    value, unit, after_strength, strength_notes = parse_combination_strength(raw_text)
    if value is None:
        value, unit, after_strength = parse_strength(raw_text)
    times, notes, after_frequency = parse_frequency(after_strength)
    notes = (*strength_notes, *notes)
    after_directions = strip_trailing_directions(after_frequency)
    dose_count, after_count = parse_dose_count(after_directions)
    after_quantity = strip_administration_quantity(after_count)
    name = clean_name_text(after_quantity)
    if not name:
        notes = (*notes, "no drug name found in entry")
    if value is None:
        notes = (*notes, "no strength found")
    if dose_count is not None:
        notes = (*notes, f"per-dose count of {dose_count:g} multiplied into the daily total")
    if unit == CONTINUOUS_RATE_UNIT and value is not None:
        notes = (*notes, "continuous rate; the daily total shows the rate itself")
    return MedEntry(
        raw_text=raw_text.strip(),
        name_text=name,
        strength_value=value,
        strength_unit=unit,
        times_per_day=times,
        daily_total=entry_daily_total(value, unit, dose_count, times),
        notes=notes,
    )


def parse_med_list(text: str) -> tuple[MedEntry, ...]:
    """
    Takes a free-text medication list of any length.
    Splits it into entries and parses each one.
    Gives the tuple of MedEntry records in input order, empty for blank input.
    """
    return tuple(parse_entry(entry) for entry in split_entries(text))
