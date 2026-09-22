"""Rules for T01 Boxed Warning and T04 High-Frequency Adverse Effect."""

from __future__ import annotations

import re

from rx_label_search.records import Label, TermEvidence
from rx_label_search.text.fields import label_text
from rx_label_search.text.html_tables import parse_tables
from rx_label_search.text.negation import is_negated
from rx_label_search.text.sentences import split_sentences
from rx_label_search.vocabulary.terms import RULE_VERSION

HIGH_FREQUENCY_THRESHOLD = 10.0
_PLACEBO_HEADER = re.compile(r"placebo|vehicle|\bcontrol\b", re.IGNORECASE)
_PERCENT_IN_TEXT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_LAST_PAREN_NUMBER = re.compile(r"\((\d+(?:\.\d+)?)\s*%?\)")


def tag_t01_boxed_warning(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Checks whether its boxed_warning field carries any text.
    Gives evidence naming the field and the first sentence, or None when the field is empty.
    """
    text = label_text(label, "boxed_warning")
    if not text:
        return None
    sentences = split_sentences(text)
    sentence = sentences[0] if sentences else text
    return TermEvidence("T01", "boxed_warning", sentence, RULE_VERSION)


def drug_group_columns(header: tuple[str, ...]) -> tuple[int, ...]:
    """
    Takes the header row of an adverse reactions table.
    Finds every column after the first whose header names a drug group rather than placebo.
    Gives the tuple of column indexes, empty when the header has fewer than two columns.
    """
    if len(header) < 2:
        return ()
    return tuple(i for i in range(1, len(header)) if header[i].strip() and not _PLACEBO_HEADER.search(header[i]))


def cell_percentage(cell: str) -> float | None:
    """
    Takes one table cell's text.
    Reads a percentage from a trailing parenthesized number or a percent sign.
    Gives the percentage, or None when the cell has no recognizable number.
    """
    paren_matches = _LAST_PAREN_NUMBER.findall(cell)
    if paren_matches:
        return float(paren_matches[-1])
    percent_matches = _PERCENT_IN_TEXT.findall(cell)
    if percent_matches:
        return float(percent_matches[-1])
    return None


def table_high_frequency_reaction(html: str, threshold: float) -> tuple[str, str] | None:
    """
    Takes one adverse-reactions table HTML string and the percent threshold.
    Reads the header row, finds the drug-group columns, and looks for a reaction at or above the threshold.
    Gives (reaction name, cell text) for the first match, or None when no drug-group column is identified or none reaches it.
    """
    for table in parse_tables(html):
        if not table:
            continue
        header, rows = table[0], table[1:]
        columns = drug_group_columns(header)
        if not columns:
            continue
        for row in rows:
            if len(row) != len(header) or not row[0].strip():
                continue
            for column in columns:
                percentage = cell_percentage(row[column])
                if percentage is not None and percentage >= threshold:
                    return row[0].strip(), f"{header[column].strip()}: {row[column].strip()}"
    return None


def prose_high_frequency_sentence(text: str, threshold: float) -> str | None:
    """
    Takes the adverse_reactions prose text and the percent threshold.
    Finds a sentence whose first percentage, read as the drug group's rate when placebo is also mentioned, meets the threshold.
    Gives that sentence, or None when no sentence qualifies.
    """
    for sentence in split_sentences(text):
        if is_negated(sentence):
            continue
        percentages = [float(value) for value in _PERCENT_IN_TEXT.findall(sentence)]
        if not percentages:
            continue
        drug_rate = percentages[0]
        if drug_rate >= threshold:
            return sentence
    return None


def tag_t04_high_frequency_adverse_effect(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Looks for a drug-group adverse reaction rate at or above ten percent in the adverse reaction table or prose.
    Gives evidence naming the field and the matched reaction, or None when no drug-group rate reaches the threshold.
    """
    for table_html in label.text_fields.get("adverse_reactions_table", ()):
        found = table_high_frequency_reaction(table_html, HIGH_FREQUENCY_THRESHOLD)
        if found is not None:
            reaction, cell = found
            return TermEvidence("T04", "adverse_reactions_table", f"{reaction}: {cell}", RULE_VERSION)
    prose = label_text(label, "adverse_reactions")
    sentence = prose_high_frequency_sentence(prose, HIGH_FREQUENCY_THRESHOLD) if prose else None
    if sentence is not None:
        return TermEvidence("T04", "adverse_reactions", sentence, RULE_VERSION)
    return None
