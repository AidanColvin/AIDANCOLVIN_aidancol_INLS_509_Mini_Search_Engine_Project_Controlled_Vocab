"""Pure precision, recall, F1, and confusion counts for the tagger against a gold set."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class TermMetrics:
    """One term's confusion counts and derived scores against the gold set."""

    term_id: str
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int

    @property
    def precision(self) -> float:
        """
        Takes no arguments.
        Divides true positives by every label the tagger assigned this term to.
        Gives the precision, 0.0 when the tagger assigned it to nothing.
        """
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        """
        Takes no arguments.
        Divides true positives by every label the gold set assigned this term to.
        Gives the recall, 0.0 when the gold set assigned it to nothing.
        """
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else 0.0

    @property
    def f1(self) -> float:
        """
        Takes no arguments.
        Computes the harmonic mean of precision and recall.
        Gives the F1 score, 0.0 when both precision and recall are 0.0.
        """
        total = self.precision + self.recall
        return 2 * self.precision * self.recall / total if total else 0.0


def term_confusion(term_id: str, gold_cells: tuple[tuple[str, str, bool], ...], predicted: Mapping[str, frozenset[str]]) -> TermMetrics:
    """
    Takes a term id, the filled gold cells, and the tagger's predicted term ids per set id.
    Counts true and false positives and negatives for that term across the gold cells naming it.
    Gives the TermMetrics, with every count 0 when no gold cell names the term.
    """
    true_positive = false_positive = false_negative = true_negative = 0
    for set_id, cell_term, gold_value in gold_cells:
        if cell_term != term_id:
            continue
        predicted_positive = term_id in predicted.get(set_id, frozenset())
        if predicted_positive and gold_value:
            true_positive += 1
        elif predicted_positive and not gold_value:
            false_positive += 1
        elif not predicted_positive and gold_value:
            false_negative += 1
        else:
            true_negative += 1
    return TermMetrics(term_id, true_positive, false_positive, false_negative, true_negative)


def all_term_metrics(term_ids: tuple[str, ...], gold_cells: tuple[tuple[str, str, bool], ...], predicted: Mapping[str, frozenset[str]]) -> tuple[TermMetrics, ...]:
    """
    Takes every term id, the filled gold cells, and the tagger's predicted term ids per set id.
    Computes each term's confusion counts.
    Gives the tuple of TermMetrics in the given term order.
    """
    return tuple(term_confusion(term_id, gold_cells, predicted) for term_id in term_ids)
