"""Rules for T07 Controlled Substance and T10 Schedule II Controlled Substance."""

from __future__ import annotations

import re

from rx_label_search.records import Label, TermEvidence
from rx_label_search.text.fields import label_text
from rx_label_search.text.negation import is_negated
from rx_label_search.text.sentences import split_sentences
from rx_label_search.vocabulary.terms import RULE_VERSION

SCHEDULE_PATTERNS: dict[str, re.Pattern[str]] = {
    "II": re.compile(r"\bschedule\s+ii\b|\bc-?ii\b", re.IGNORECASE),
    "III": re.compile(r"\bschedule\s+iii\b|\bc-?iii\b", re.IGNORECASE),
    "IV": re.compile(r"\bschedule\s+iv\b|\bc-?iv\b", re.IGNORECASE),
    "V": re.compile(r"\bschedule\s+v\b|\bc-?v\b", re.IGNORECASE),
}


def scheduled_sentence(text: str, pattern: re.Pattern[str]) -> str | None:
    """
    Takes the controlled_substance field text and a schedule pattern.
    Finds a non-negated sentence that names that schedule.
    Gives the sentence, or None when no sentence names it without negation.
    """
    for sentence in split_sentences(text):
        if pattern.search(sentence) and not is_negated(sentence):
            return sentence
    return None


def tag_t07_controlled_substance(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Searches controlled_substance for a sentence naming DEA Schedule II, III, IV, or V.
    Gives evidence naming the field and the sentence, or None when no schedule is named.
    """
    text = label_text(label, "controlled_substance")
    if not text:
        return None
    for pattern in SCHEDULE_PATTERNS.values():
        sentence = scheduled_sentence(text, pattern)
        if sentence is not None:
            return TermEvidence("T07", "controlled_substance", sentence, RULE_VERSION)
    return None


def tag_t10_schedule_ii_controlled_substance(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Searches controlled_substance for a sentence naming DEA Schedule II specifically.
    Gives evidence naming the field and the sentence, or None when Schedule II is not named.
    """
    text = label_text(label, "controlled_substance")
    if not text:
        return None
    sentence = scheduled_sentence(text, SCHEDULE_PATTERNS["II"])
    if sentence is None:
        return None
    return TermEvidence("T10", "controlled_substance", sentence, RULE_VERSION)
