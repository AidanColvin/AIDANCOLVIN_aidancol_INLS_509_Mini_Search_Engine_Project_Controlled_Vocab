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


RUN_ON_STRENGTH = re.compile(rf"^(?:{_NUMBER}(?:/{_NUMBER})*)\s*(?:{_UNIT})(?:/\w+)?$|^(?:{_UNIT})(?:/\w+)?$", re.IGNORECASE)
RUN_ON_NUMBER = re.compile(rf"^{_NUMBER}(?:/{_NUMBER})*$")
RUN_ON_NAME_START = re.compile(r"^[A-Za-z][A-Za-z\-']*$")
RUN_ON_LOOKAHEAD = 6
DOSING_WORDS: frozenset[str] = frozenset(
    "once twice three four times time daily day days a an per every each hours hour hrs hr h q qd bid tid qid qhs prn po as needed necessary "
    "at bedtime night morning evening afternoon in the with without before after food meals meal breakfast lunch dinner supper on those "
    "max maximum up to no more than may repeat not exceed doses dose tablet tablets tab tabs capsule capsules cap caps pill pills patch patches "
    "spray sprays puff puffs drop drops nostril nostrils eye eyes ear ears weekly week weeks continuous episode for and or by mouth orally oral "
    "iv im subcutaneous transdermal sublingual nasal inhaled topical er xr xl sr ir dr cd la ds otc generic x of one two".split()
)


def is_strength_token(tokens: list[str], index: int) -> bool:
    """
    Takes a list's whitespace tokens and a position.
    Checks whether a strength starts there: "20mg", "20 mg", "10/325 mg", or "25 mcg/h".
    Gives True when it does.
    """
    token = tokens[index]
    if RUN_ON_STRENGTH.match(token) and any(ch.isdigit() for ch in token):
        return True
    return bool(RUN_ON_NUMBER.match(token)) and index + 1 < len(tokens) and bool(RUN_ON_STRENGTH.match(tokens[index + 1]))


def split_run_on(entry: str) -> tuple[str, ...]:
    """
    Takes one entry that may hold several medications typed without separators, such as "Adderall 30 mg Valium 20 mg oxycodone 5 mg".
    Starts a new entry at a word that follows a strength, is not a dosing word, and is itself followed by a strength within six words before any "=", so a direction like "as needed for chest pain" never splits a line.
    Gives the entries, the entry alone when nothing splits it.
    """
    tokens = entry.split()
    pieces: list[list[str]] = [[]]
    seen_strength = False
    for index, token in enumerate(tokens):
        word = token.strip("(),.;:").lower()
        starts_new = (
            seen_strength
            and RUN_ON_NAME_START.match(token.rstrip(",.;:")) is not None
            and word not in DOSING_WORDS
            and RUN_ON_STRENGTH.match(token) is None
            and any(is_strength_token(tokens, ahead) for ahead in range(index + 1, min(len(tokens), index + 1 + RUN_ON_LOOKAHEAD)) if "=" not in tokens[index + 1 : ahead + 1])
        )
        if starts_new:
            pieces.append([])
            seen_strength = False
        pieces[-1].append(token)
        if is_strength_token(tokens, index):
            seen_strength = True
    return tuple(" ".join(piece) for piece in pieces if piece)


def split_entries(text: str) -> tuple[str, ...]:
    """
    Takes a free-text medication list.
    Splits it at commas, semicolons, and new lines, after removing thousands-separator commas inside numbers, then splits any entry that runs several dosed medications together.
    Gives the tuple of non-empty trimmed entries, empty for blank input.
    """
    parts = (part.strip() for part in ENTRY_SEPARATORS.split(drop_thousands_separators(text)) if part.strip())
    return tuple(piece for part in parts for piece in split_run_on(part))


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


PAREN_NAME = re.compile(r"^\s*(?P<brand>[^()=]*?)\s*\((?P<inner>[^()=]+)\)\s*(?P<rest>.*)$", re.DOTALL)
STATED_TOTAL = re.compile(r"\s=\s*(?P<total>.*)$", re.DOTALL)
NAME_QUALIFIERS = re.compile(
    r"\b(?:otc|generic|er|ir|sr|xl|xr|dr|ec|cd|la|ds|odt|sublingual|nasal|transdermal|oral|topical|inhaled|iv|im|subcutaneous|patch)\b",
    re.IGNORECASE,
)
RELEASE_WORDS: dict[str, str] = {
    "er": "extended-release", "xr": "extended-release", "xl": "extended-release", "sr": "sustained-release",
    "cd": "extended-release", "la": "extended-release", "dr": "delayed-release", "ec": "delayed-release", "ir": "immediate-release",
}
RELEASE_FORM = re.compile(r"\b(er|xr|xl|sr|cd|la|dr|ec|ir)\b", re.IGNORECASE)
ROUTE_WORDS = re.compile(r"\b(iv|im|subcutaneous|transdermal|sublingual|nasal|inhaled|topical)\b", re.IGNORECASE)
ROUTE_NAMES: dict[str, str] = {
    "iv": "intravenous", "im": "intramuscular", "subcutaneous": "subcutaneous", "transdermal": "transdermal",
    "sublingual": "sublingual", "nasal": "nasal", "inhaled": "inhaled", "topical": "topical",
}
_DAY = r"(?:mon|tues?|wed|thu(?:rs?)?|fri|sat|sun)(?:day)?"
SPECIFIC_DAYS = re.compile(rf"\b(?:on\s+)?{_DAY}(?:\s*(?:/|,|and)\s*{_DAY})+\b", re.IGNORECASE)
DAY_TOKEN = re.compile(_DAY, re.IGNORECASE)
AS_NEEDED = re.compile(r"\b(?:as\s+needed|prn|as\s+necessary)\b", re.IGNORECASE)
MAX_AMOUNT_PER_DAY = re.compile(rf"\b(?:max(?:imum)?|not\s+to\s+exceed|up\s+to)\s+({_NUMBER})\s*(mg|mcg|g)\s*(?:/|per|a)\s*day\b", re.IGNORECASE)
MAX_UNITS_PER_DAY = re.compile(
    r"\b(?:max(?:imum)?|not\s+to\s+exceed|up\s+to)\s+(\d+)\s*(doses?|tablets?|tabs?|capsules?|caps?|sprays?|puffs?|patch(?:es)?)\s*(?:/|per|a)\s*day\b",
    re.IGNORECASE,
)
NO_MORE_THAN = re.compile(r"\bno\s+more\s+than\s+(once|twice|\d+\s*times?)\s*(?:daily|a\s+day|per\s+day)\b", re.IGNORECASE)
MAY_REPEAT = re.compile(r"\bmay\s+repeat(?:\s+(once|twice))?\b", re.IGNORECASE)
PER_EPISODE = re.compile(r"\bup\s+to\s+(\d+)\s*(?:tablets?|doses?|sprays?)\s+in\s+\d+\s*minutes\b", re.IGNORECASE)
APPLICATION_COUNT = re.compile(r"\b(\d+|one|two|three|four)\s*(sprays?|puffs?|inhalations?|actuations?|drops?)\b", re.IGNORECASE)
BOTH_SIDES = re.compile(r"\b(?:in\s+)?each\s+(?:nostril|eye|ear)\b", re.IGNORECASE)


def split_stated_total(text: str) -> tuple[str, str | None]:
    """
    Takes one medication entry, which may end with the prescriber's own arithmetic such as "= 10 mg/day".
    Splits off everything after an equals sign so its numbers are never read as the strength or frequency.
    Gives the entry before the equals sign and the stated total text, or the entry unchanged and None when it has no equals sign.
    """
    match = STATED_TOTAL.search(text)
    if match is None:
        return text, None
    return text[: match.start()], match.group("total").strip() or None


def split_brand_and_generic(text: str) -> tuple[str | None, str | None, str]:
    """
    Takes one medication entry such as "Zyprexa (olanzapine) 10 mg once daily" or "sertraline (generic) 50 mg".
    Reads the name before the parentheses as the brand and the name inside them as the generic; "(generic)" means the name before it is itself the generic.
    Gives the brand, the generic text as written inside the parentheses, and the rest of the entry, with None names when the entry has no leading parenthesized name.
    """
    match = PAREN_NAME.match(text)
    if match is None or not match.group("brand").strip():
        return None, None, text
    brand = match.group("brand").strip()
    inner = match.group("inner").strip()
    if NAME_QUALIFIERS.sub("", inner).strip() == "":
        return None, f"{brand} {inner}", match.group("rest")
    return brand, inner, match.group("rest")


def generic_components(generic_text: str) -> tuple[str, ...]:
    """
    Takes the generic text from inside the parentheses, such as "hydrocodone/acetaminophen" or "lithium carbonate ER".
    Drops release-form, route, OTC, and "generic" words and splits a combination on "/".
    Gives the cleaned component names in the order written, empty when nothing remains.
    """
    parts = [" ".join(NAME_QUALIFIERS.sub(" ", part).split()) for part in generic_text.split("/")]
    return tuple(part for part in parts if part)


def generic_lookup_name(components: tuple[str, ...]) -> str:
    """
    Takes the cleaned component names of one generic.
    Joins them the way FDA labels name combinations, as "a and b" or "a, b and c".
    Gives the lookup name, empty when there are no components.
    """
    if len(components) <= 2:
        return " and ".join(components)
    return ", ".join(components[:-1]) + " and " + components[-1]


def release_form_of(*texts: str | None) -> str | None:
    """
    Takes the brand and generic texts of one entry.
    Finds a release-form abbreviation such as ER, XR, XL, SR, CD, LA, DR, or IR.
    Gives the spelled-out release form, or None when no abbreviation is present.
    """
    for text in texts:
        match = RELEASE_FORM.search(text or "")
        if match is not None:
            return RELEASE_WORDS[match.group(1).lower()]
    return None


def route_of(*texts: str | None) -> str | None:
    """
    Takes any texts of one entry.
    Finds a route word such as IV, subcutaneous, transdermal, sublingual, or nasal.
    Gives the spelled-out route, or None when no route word is present.
    """
    for text in texts:
        match = ROUTE_WORDS.search(text or "")
        if match is not None:
            return ROUTE_NAMES[match.group(1).lower()]
    return None


def parse_specific_days(text: str) -> tuple[float | None, str | None, str]:
    """
    Takes the dosing text of one entry.
    Finds a named-day schedule such as "Mon/Wed/Fri" and counts its days.
    Gives the days per week, the schedule as written, and the text with it removed, or None, None, and the unchanged text when there is none.
    """
    match = SPECIFIC_DAYS.search(text)
    if match is None:
        return None, None, text
    days = {token.lower()[:3] for token in DAY_TOKEN.findall(match.group(0))}
    written = match.group(0).strip()
    written = written[3:].strip() if written.lower().startswith("on ") else written
    return float(len(days)), written, text[: match.start()] + " " + text[match.end() :]


def application_count(text: str) -> tuple[float | None, str]:
    """
    Takes the dosing text of one entry.
    Reads a per-dose spray, puff, or drop count, doubled when the dose goes in each nostril, eye, or ear.
    Gives the count and the text with those words removed, or None and the unchanged text when there is no count.
    """
    match = APPLICATION_COUNT.search(text)
    if match is None:
        return None, text
    captured = match.group(1).lower()
    count = COUNT_WORDS[captured] if captured in COUNT_WORDS else float(captured)
    remaining = text[: match.start()] + " " + text[match.end() :]
    if BOTH_SIDES.search(remaining):
        count *= 2
        remaining = BOTH_SIDES.sub(" ", remaining)
    return count, remaining


def as_needed_limits(text: str, strength_value: float | None, strength_unit: str | None) -> tuple[float | None, float | None, tuple[str, ...]]:
    """
    Takes the dosing text of one entry, its unit strength, and its unit.
    Reads the most the prescription allows in a day: "max 200 mg/day", "max 6 tablets/day", "no more than once daily", or "may repeat once".
    Gives the maximum daily amount in the strength's unit (or None), the maximum dosing units per day (or None), and notes saying which limit was read.
    """
    amount = MAX_AMOUNT_PER_DAY.search(text)
    if amount is not None and strength_unit is not None:
        value = float(amount.group(1))
        scale = UNIT_SCALE_TO_MG.get(amount.group(2).lower(), 1.0) / UNIT_SCALE_TO_MG.get(strength_unit.lower(), 1.0)
        return value * scale, None, (f'daily maximum read from "{amount.group(0).strip()}"',)
    units = MAX_UNITS_PER_DAY.search(text)
    if units is not None:
        return None, float(units.group(1)), (f'daily maximum read from "{units.group(0).strip()}"',)
    no_more = NO_MORE_THAN.search(text)
    if no_more is not None:
        word = no_more.group(1).lower()
        count = WORD_COUNTS.get(word) or float(re.findall(r"\d+", word)[0])
        return None, count, (f'daily maximum read from "{no_more.group(0).strip()}"',)
    repeat = MAY_REPEAT.search(text)
    if repeat is not None and strength_value is not None:
        repeats = {"once": 1.0, "twice": 2.0}.get((repeat.group(1) or "once").lower(), 1.0)
        return None, 1.0 + repeats, (f'daily maximum read from "{repeat.group(0).strip()}": the first dose plus {repeats:g} repeat',)
    return None, None, ()


UNIT_SCALE_TO_MG: dict[str, float] = {"mg": 1.0, "mcg": 0.001, "g": 1000.0}


def parse_entry(raw_text: str) -> MedEntry:
    """
    Takes one raw medication entry, in any common form, including "Brand (generic) dose frequency = total".
    Extracts the brand and generic, the strength (every component of a combination), the frequency or named-day schedule, as-needed limits, and the remaining name text; the stated total after "=" is kept as written, never parsed as a dose.
    Gives a MedEntry, with an empty name and a note when no name text remains.
    """
    before_total, stated_total = split_stated_total(raw_text)
    brand, generic_text, dosing_text = split_brand_and_generic(before_total)
    components = generic_components(generic_text) if generic_text else ()
    value, unit, after_strength, strength_notes = parse_combination_strength(dosing_text)
    component_strengths: tuple[tuple[float, str], ...] = ()
    if value is not None:
        component_strengths = combination_components(dosing_text)
    else:
        value, unit, after_strength = parse_strength(dosing_text)
    if len(components) > 1 and len(component_strengths) == len(components):
        strength_notes = (f"combination strength read per component: {', '.join(f'{name} {amount:g} {each_unit}' for name, (amount, each_unit) in zip(components, component_strengths))}",)
    days_per_week, schedule_text, after_days = parse_specific_days(after_strength)
    times, notes, after_frequency = parse_frequency(after_days)
    if days_per_week is not None:
        times = 1.0 if times is None else times
        notes = (f"taken on {schedule_text} only: {days_per_week:g} days a week",)
    elif times is None and any("weekly" in note for note in notes):
        days_per_week = 1.0
        schedule_text = "once weekly"
    as_needed = AS_NEEDED.search(dosing_text) is not None
    max_amount, max_units, limit_notes = as_needed_limits(dosing_text, value, unit)
    per_episode = PER_EPISODE.search(dosing_text)
    notes = (*strength_notes, *notes, *limit_notes)
    after_directions = strip_trailing_directions(PER_EPISODE.sub(" ", after_frequency))
    applications, after_applications = application_count(after_directions)
    dose_count, after_count = parse_dose_count(after_applications)
    dose_count = applications if dose_count is None else dose_count
    after_quantity = strip_administration_quantity(after_count)
    if max_units is not None:
        per_dose = dose_count or 1.0
        times = max_units / per_dose
    if as_needed and times is None and per_episode is not None:
        notes = (*notes, f'as-needed use of up to {per_episode.group(1)} per episode; no daily total')
    leftover = clean_name_text(NAME_QUALIFIERS.sub(" ", after_quantity)) if generic_text else clean_name_text(after_quantity)
    name = generic_lookup_name(components) if components else (clean_name_text(brand or "") if brand else leftover)
    if not generic_text:
        name = leftover
    if not name:
        notes = (*notes, "no drug name found in entry")
    if value is None:
        notes = (*notes, "no strength found")
    if dose_count is not None:
        notes = (*notes, f"per-dose count of {dose_count:g} multiplied into the daily total")
    if unit == CONTINUOUS_RATE_UNIT and value is not None:
        notes = (*notes, "continuous rate; the daily total shows the rate itself")
    total = entry_daily_total(value, unit, dose_count, times)
    if max_amount is not None:
        total = max_amount
        times = times if times is not None else (max_amount / (value * (dose_count or 1.0)) if value else None)
    return MedEntry(
        raw_text=raw_text.strip(),
        name_text=name,
        strength_value=value,
        strength_unit=unit,
        times_per_day=times,
        daily_total=total,
        notes=notes,
        brand_text=brand,
        components=components,
        component_strengths=component_strengths if len(component_strengths) == len(components) and len(components) > 1 else (),
        dose_count=dose_count,
        days_per_week=days_per_week,
        schedule_text=schedule_text,
        as_needed=as_needed,
        stated_total=stated_total,
        release_form=release_form_of(brand, generic_text, dosing_text),
        route=route_of(generic_text, dosing_text),
    )


def combination_components(text: str) -> tuple[tuple[float, str], ...]:
    """
    Takes an entry holding a slash-joined combination strength such as "10/325 mg" or "0.25 mg/35 mcg".
    Reads every component's number and gives each the unit written after it, or the expression's last unit when none is written.
    Gives the (value, unit) pairs in order, empty when the entry has no combination strength.
    """
    match = COMBINATION_STRENGTH.search(text)
    if match is None:
        return ()
    pieces = re.findall(rf"({_NUMBER})\s*({_UNIT})?", match.group(0), re.IGNORECASE)
    units = [UNIT_NAMES[piece_unit.lower()] if piece_unit else None for _, piece_unit in pieces]
    fallback = next((each for each in reversed(units) if each), None)
    if fallback is None:
        return ()
    return tuple((float(number), each or fallback) for (number, _), each in zip(pieces, units))


def parse_med_list(text: str) -> tuple[MedEntry, ...]:
    """
    Takes a free-text medication list of any length.
    Splits it into entries and parses each one.
    Gives the tuple of MedEntry records in input order, empty for blank input.
    """
    return tuple(parse_entry(entry) for entry in split_entries(text))
