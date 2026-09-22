"""Tests for term confusion counts and derived scores."""

from __future__ import annotations

from rx_label_search.evaluate.tag_metrics import TermMetrics, all_term_metrics, term_confusion


def test_term_confusion_counts_all_four_outcomes() -> None:
    """
    Takes no arguments.
    Scores one term across four gold cells, one of each outcome.
    Gives nothing, or fails if any count is wrong.
    """
    cells = (("s1", "T06", True), ("s2", "T06", False), ("s3", "T06", True), ("s4", "T06", False))
    predicted = {"s1": frozenset({"T06"}), "s2": frozenset({"T06"}), "s3": frozenset(), "s4": frozenset()}
    metrics = term_confusion("T06", cells, predicted)
    assert (metrics.true_positive, metrics.false_positive, metrics.false_negative, metrics.true_negative) == (1, 1, 1, 1)


def test_term_confusion_ignores_other_terms_and_missing_set_id() -> None:
    """
    Takes no arguments.
    Scores a term against cells naming a different term and a set id absent from predicted.
    Gives nothing, or fails if a count leaks in or the missing set id crashes.
    """
    cells = (("s1", "T14", True), ("s2", "T06", True))
    metrics = term_confusion("T06", cells, {})
    assert metrics.true_positive == 0
    assert metrics.false_negative == 1


def test_precision_recall_f1_edge_cases() -> None:
    """
    Takes no arguments.
    Computes scores when the tagger assigned nothing and when the gold set has no positives.
    Gives nothing, or fails if any score is not 0.0 in the empty case.
    """
    no_predictions = TermMetrics("T06", 0, 0, 3, 0)
    assert no_predictions.precision == 0.0
    assert no_predictions.recall == 0.0
    assert no_predictions.f1 == 0.0
    no_gold_positives = TermMetrics("T06", 0, 2, 0, 5)
    assert no_gold_positives.recall == 0.0


def test_precision_recall_f1_typical_case() -> None:
    """
    Takes no arguments.
    Computes scores for a typical confusion count.
    Gives nothing, or fails if any score is wrong.
    """
    metrics = TermMetrics("T06", 8, 2, 2, 10)
    assert metrics.precision == 0.8
    assert metrics.recall == 0.8
    assert round(metrics.f1, 3) == 0.8


def test_all_term_metrics_preserves_order_and_handles_empty_gold() -> None:
    """
    Takes no arguments.
    Scores two terms with no gold cells at all.
    Gives nothing, or fails if the order is wrong or any count is nonzero.
    """
    results = all_term_metrics(("T01", "T02"), (), {})
    assert [m.term_id for m in results] == ["T01", "T02"]
    assert all(m.true_positive == 0 for m in results)
