"""Pure information-retrieval metrics: precision@k, recall@k, MAP, and nDCG."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


def precision_at_k(ranked_ids: Sequence[str], relevant_ids: frozenset[str], k: int) -> float:
    """
    Takes the ranked result ids best first, the relevant ids, and the cutoff k.
    Divides the relevant ids among the top k results by k.
    Gives the precision, 0.0 when k is 0.
    """
    if k <= 0:
        return 0.0
    top_k = ranked_ids[:k]
    return sum(1 for result_id in top_k if result_id in relevant_ids) / k


def recall_at_k(ranked_ids: Sequence[str], relevant_ids: frozenset[str], k: int) -> float:
    """
    Takes the ranked result ids best first, the relevant ids, and the cutoff k.
    Divides the relevant ids found among the top k results by the total number of relevant ids.
    Gives the recall, 0.0 when there are no relevant ids.
    """
    if not relevant_ids:
        return 0.0
    top_k = ranked_ids[:k]
    return sum(1 for result_id in top_k if result_id in relevant_ids) / len(relevant_ids)


def average_precision(ranked_ids: Sequence[str], relevant_ids: frozenset[str]) -> float:
    """
    Takes the ranked result ids best first and the relevant ids.
    Averages the precision at each rank where a relevant id appears.
    Gives the average precision, 0.0 when there are no relevant ids.
    """
    if not relevant_ids:
        return 0.0
    found = 0
    precision_sum = 0.0
    for rank, result_id in enumerate(ranked_ids, start=1):
        if result_id in relevant_ids:
            found += 1
            precision_sum += found / rank
    return precision_sum / len(relevant_ids)


def mean_average_precision(all_ranked_ids: Sequence[Sequence[str]], all_relevant_ids: Sequence[frozenset[str]]) -> float:
    """
    Takes one ranked result list and one relevant-id set per query, in matching order.
    Averages each query's average precision.
    Gives the mean, 0.0 when there are no queries.
    """
    if not all_ranked_ids:
        return 0.0
    scores = [average_precision(ranked, relevant) for ranked, relevant in zip(all_ranked_ids, all_relevant_ids, strict=True)]
    return sum(scores) / len(scores)


def discounted_cumulative_gain(ranked_ids: Sequence[str], relevance: Mapping[str, float], k: int) -> float:
    """
    Takes the ranked result ids best first, a mapping from id to graded relevance, and the cutoff k.
    Sums each top-k result's relevance discounted by the log of its rank.
    Gives the DCG, 0.0 for an empty ranking.
    """
    total = 0.0
    for rank, result_id in enumerate(ranked_ids[:k], start=1):
        gain = relevance.get(result_id, 0.0)
        total += gain if rank == 1 else gain / math.log2(rank + 1)
    return total


def normalized_discounted_cumulative_gain(ranked_ids: Sequence[str], relevance: Mapping[str, float], k: int) -> float:
    """
    Takes the ranked result ids best first, a mapping from id to graded relevance, and the cutoff k.
    Divides the ranking's DCG by the DCG of the ideal ranking over the same relevance values.
    Gives the nDCG, 0.0 when the ideal DCG is 0.0.
    """
    ideal_order = sorted(relevance, key=lambda result_id: -relevance[result_id])
    ideal_dcg = discounted_cumulative_gain(ideal_order, relevance, k)
    if ideal_dcg == 0.0:
        return 0.0
    return discounted_cumulative_gain(ranked_ids, relevance, k) / ideal_dcg
