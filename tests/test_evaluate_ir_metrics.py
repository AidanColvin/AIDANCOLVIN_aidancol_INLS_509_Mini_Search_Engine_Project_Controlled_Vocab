"""Tests for precision@k, recall@k, MAP, and nDCG."""

from __future__ import annotations

from rx_label_search.evaluate.ir_metrics import (
    average_precision,
    discounted_cumulative_gain,
    mean_average_precision,
    normalized_discounted_cumulative_gain,
    precision_at_k,
    recall_at_k,
)


def test_precision_at_k_typical_and_zero_k() -> None:
    """
    Takes no arguments.
    Scores precision at k for a mixed ranking and at k equal to zero.
    Gives nothing, or fails if either result is wrong.
    """
    assert precision_at_k(["a", "b", "c", "d"], frozenset({"a", "c"}), 4) == 0.5
    assert precision_at_k(["a", "b"], frozenset({"a"}), 0) == 0.0


def test_recall_at_k_typical_and_no_relevant() -> None:
    """
    Takes no arguments.
    Scores recall at k for a partial match and for no relevant ids at all.
    Gives nothing, or fails if either result is wrong.
    """
    assert recall_at_k(["a", "b", "c"], frozenset({"a", "c", "z"}), 2) == 1 / 3
    assert recall_at_k(["a", "b"], frozenset(), 2) == 0.0


def test_average_precision_orders_relevant_results_first() -> None:
    """
    Takes no arguments.
    Scores average precision for two relevant ids at the front and scattered further back.
    Gives nothing, or fails if the front-loaded ranking does not score higher.
    """
    relevant = frozenset({"a", "c"})
    front = average_precision(["a", "c", "b", "d"], relevant)
    scattered = average_precision(["b", "a", "d", "c"], relevant)
    assert front > scattered
    assert average_precision(["b"], frozenset()) == 0.0


def test_mean_average_precision_averages_across_queries() -> None:
    """
    Takes no arguments.
    Scores MAP for two queries with different average precision.
    Gives nothing, or fails if the mean is not the arithmetic average.
    """
    ap1 = average_precision(["a", "b"], frozenset({"a"}))
    ap2 = average_precision(["b", "a"], frozenset({"a"}))
    result = mean_average_precision([["a", "b"], ["b", "a"]], [frozenset({"a"}), frozenset({"a"})])
    assert round(result, 6) == round((ap1 + ap2) / 2, 6)
    assert mean_average_precision([], []) == 0.0


def test_dcg_gives_more_weight_to_earlier_ranks() -> None:
    """
    Takes no arguments.
    Scores DCG for the same relevant id at rank one and at rank three.
    Gives nothing, or fails if the earlier rank does not score higher.
    """
    relevance = {"a": 1.0}
    early = discounted_cumulative_gain(["a", "x", "y"], relevance, 3)
    late = discounted_cumulative_gain(["x", "y", "a"], relevance, 3)
    assert early > late
    assert discounted_cumulative_gain([], relevance, 3) == 0.0


def test_ndcg_is_one_for_the_ideal_ranking() -> None:
    """
    Takes no arguments.
    Scores nDCG for the ideal order and a shuffled order of the same graded relevance.
    Gives nothing, or fails if the ideal order does not score 1.0 or the shuffled order does not score lower.
    """
    relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
    assert normalized_discounted_cumulative_gain(["a", "b", "c"], relevance, 3) == 1.0
    assert normalized_discounted_cumulative_gain(["c", "b", "a"], relevance, 3) < 1.0


def test_ndcg_zero_ideal_dcg() -> None:
    """
    Takes no arguments.
    Scores nDCG when every relevance value is zero.
    Gives nothing, or fails if the result is not 0.0.
    """
    assert normalized_discounted_cumulative_gain(["a"], {"a": 0.0}, 1) == 0.0
