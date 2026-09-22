"""Tests for sentence splitting and search."""

from __future__ import annotations

import re

from rx_label_search.text.sentences import (
    collapse_whitespace,
    first_sentence_matching,
    protect_abbreviations,
    restore_abbreviations,
    sentences_matching,
    split_sentences,
)


def test_split_sentences_basic_and_abbreviation() -> None:
    """
    Takes no arguments.
    Splits text with a normal boundary and an e.g. abbreviation.
    Gives nothing, or fails if the abbreviation splits or the count is wrong.
    """
    text = "Use with caution, e.g. in the elderly. Serotonin syndrome has been reported. See section 7."
    sentences = split_sentences(text)
    assert sentences == (
        "Use with caution, e.g. in the elderly.",
        "Serotonin syndrome has been reported.",
        "See section 7.",
    )


def test_split_sentences_empty_and_whitespace() -> None:
    """
    Takes no arguments.
    Splits blank text and collapses whitespace.
    Gives nothing, or fails if either result is wrong.
    """
    assert split_sentences("   ") == ()
    assert collapse_whitespace(" a \n b ") == "a b"


def test_protect_and_restore_round_trip() -> None:
    """
    Takes no arguments.
    Protects an abbreviation and restores it.
    Gives nothing, or fails if the text changed.
    """
    original = "See Fig. 2 for details."
    assert restore_abbreviations(protect_abbreviations(original, ("fig.",))) == original


def test_sentences_matching_and_first() -> None:
    """
    Takes no arguments.
    Searches sentences for a pattern that matches one of them and one that matches none.
    Gives nothing, or fails if the wrong sentences are returned.
    """
    sentences = ("No risk here.", "QT prolongation was observed.", "Done.")
    pattern = re.compile(r"qt prolongation", re.IGNORECASE)
    assert sentences_matching(sentences, pattern) == ("QT prolongation was observed.",)
    assert first_sentence_matching(sentences, pattern) == "QT prolongation was observed."
    assert first_sentence_matching(sentences, re.compile("zzz")) is None
    assert sentences_matching((), pattern) == ()
