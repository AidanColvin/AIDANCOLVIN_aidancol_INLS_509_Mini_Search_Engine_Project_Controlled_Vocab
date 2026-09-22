"""Pure parsing of free-text medication lists into MedEntry records."""

from __future__ import annotations

import re

from rx_label_search.records import MedEntry

ENTRY_SEPARATORS = re.compile(r"[,;\n]+")
STRENGTH = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?|%)(?![a-z])", re.IGNORECASE)
UNIT_NAMES = {"mg": "mg", "mcg": "mcg", "g": "g", "ml": "mL", "unit": "units", "units": "units", "%": "%"}
WORD_COUNTS = {"once": 1.0, "twice": 2.0, "three times": 3.0, "four times": 4.0}
ABBREVIATION_COUNTS = {"qd": 1.0, "bid": 2.0, "tid": 3.0, "qid": 4.0, "qhs": 1.0}
DAILY_WORD = r"(?:a\s*|per\s*|/\s*)?(?:daily|day|d\b)"
FREQUENCY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bx\s*(\d+)\s*(?:times\s*)?" + DAILY_WORD, "times"),
    (r"\b(\d+)\s*(?:times|x)\s*" + DAILY_WORD, "times"),
    (r"\b(once|twice|three times|four times)\s*" + DAILY_WORD, "words"),
    (r"\b(qd|bid|tid|qid|qhs)\b", "abbrev"),
    (r"\b(?:every|q)\s*(\d+)\s*(?:hours|hrs|hr|h)\b", "hours"),
    (r"\bq(\d+)h\b", "hours"),
    (r"\bx\s*(daily|day)\b", "bare_x"),
    (r"\b(daily|once a day|every day)\b", "bare"),
)
_COMPILED = tuple((re.compile(pattern, re.IGNORECASE), kind) for pattern, kind in FREQUENCY_PATTERNS)
_TRAILING_JUNK = re.compile(r"^[\s\-–:.]+|[\s\-–:.]+$")


def split_entries(text: str) -> tuple[str, ...]:
    """
    Takes a free-text medication list.
    Splits it at commas, semicolons, and new lines.
    Gives the tuple of non-empty trimmed entries, empty for blank input.
    """
    return tuple(part.strip() for part in ENTRY_SEPARATORS.split(text) if part.strip())


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
        return frequency_value(kind, captured), frequency_note(kind, match.group(0)), remaining
    return None, ("no frequency found; daily total not computed",), text


def clean_name_text(text: str) -> str:
    """
    Takes the entry text left after strength and frequency were removed.
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


def parse_entry(raw_text: str) -> MedEntry:
    """
    Takes one raw medication entry.
    Extracts the strength, the frequency, and the remaining name text.
    Gives a MedEntry, with an empty name and a note when no name text remains.
    """
    value, unit, after_strength = parse_strength(raw_text)
    times, notes, after_frequency = parse_frequency(after_strength)
    name = clean_name_text(after_frequency)
    if not name:
        notes = (*notes, "no drug name found in entry")
    if value is None:
        notes = (*notes, "no strength found")
    return MedEntry(
        raw_text=raw_text.strip(),
        name_text=name,
        strength_value=value,
        strength_unit=unit,
        times_per_day=times,
        daily_total=daily_total(value, times),
        notes=notes,
    )


def parse_med_list(text: str) -> tuple[MedEntry, ...]:
    """
    Takes a free-text medication list of any length.
    Splits it into entries and parses each one.
    Gives the tuple of MedEntry records in input order, empty for blank input.
    """
    return tuple(parse_entry(entry) for entry in split_entries(text))
