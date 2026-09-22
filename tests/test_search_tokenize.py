"""Tests for the tokenizer."""

from __future__ import annotations

from rx_label_search.search.tokenize import tokenize


def test_tokenize_lowercases_strips_punctuation_and_keeps_numbers() -> None:
    """
    Takes no arguments.
    Tokenizes text with mixed case, punctuation, and a number.
    Gives nothing, or fails if the tokens are wrong.
    """
    assert tokenize("Renal Dose, Adjustment! 30 mg/day.") == ("renal", "dose", "adjustment", "30", "mg", "day")


def test_tokenize_empty_text() -> None:
    """
    Takes no arguments.
    Tokenizes an empty string.
    Gives nothing, or fails if the result is not empty.
    """
    assert tokenize("") == ()
