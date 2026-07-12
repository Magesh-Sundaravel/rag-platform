"""Reciprocal Rank Fusion: combine multiple ranked-id lists into one score."""

import uuid

DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    rankings: list[list[uuid.UUID]], k: int = DEFAULT_RRF_K
) -> dict[uuid.UUID, float]:
    """Fuse ranked lists with Reciprocal Rank Fusion.

    Each id in each ranking contributes ``1 / (k + rank)`` (1-indexed rank)
    to its total score; ids absent from a list simply don't get that
    list's contribution. Pure function — no I/O, no ties to storage.

    Args:
        rankings: One or more best-first lists of chunk ids. An id may
            appear in more than one list.
        k: RRF damping constant (60 is the standard default).

    Returns:
        A mapping from id to fused score, unsorted.
    """
    scores: dict[uuid.UUID, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return scores
