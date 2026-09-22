"""Tests for negation cue detection."""

from __future__ import annotations

from rx_label_search.text.negation import is_negated, is_negated_near, negation_cue


def test_negated_sentences_are_detected() -> None:
    """
    Takes no arguments.
    Checks the two example sentences from the safety rules and a plain warning.
    Gives nothing, or fails if a negated sentence passes or a warning is flagged.
    """
    assert is_negated("No clinically significant interaction was observed.")
    assert is_negated("No dose adjustment is needed in patients with renal impairment.")
    assert is_negated("Varenicline is not a controlled substance.")
    assert not is_negated("Serotonin syndrome has been reported with concomitant use.")


def test_negation_cue_and_window() -> None:
    """
    Takes no arguments.
    Reads the cue text and checks the positional window.
    Gives nothing, or fails if the cue or window logic is wrong.
    """
    sentence = "There was no evidence of QT prolongation in the thorough QT study."
    assert negation_cue(sentence) == "no evidence of"
    assert is_negated_near(sentence, sentence.index("QT"))
    assert not is_negated_near("Fatal QT prolongation occurred.", 6)
    assert negation_cue("") is None
