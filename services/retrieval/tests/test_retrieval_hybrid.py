"""Unit tests for Reciprocal Rank Fusion (pure, no database)."""

import uuid

from retrieval.hybrid import reciprocal_rank_fusion

A, B, C = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def test_empty_rankings_produce_no_scores() -> None:
    assert reciprocal_rank_fusion([]) == {}
    assert reciprocal_rank_fusion([[], []]) == {}


def test_single_ranking_preserves_order() -> None:
    scores = reciprocal_rank_fusion([[A, B, C]])
    assert scores[A] > scores[B] > scores[C]


def test_agreement_across_lists_boosts_score() -> None:
    scores = reciprocal_rank_fusion([[A, B], [B, A]])
    # B is 2nd in list 1 and 1st in list 2; A is 1st then 2nd -> symmetric tie.
    assert scores[A] == scores[B]

    scores = reciprocal_rank_fusion([[A, B, C], [A, C, B]])
    # A is first in both lists, so it should outrank items only in one list.
    assert scores[A] > scores[B]
    assert scores[A] > scores[C]


def test_item_only_in_one_list_still_scored() -> None:
    scores = reciprocal_rank_fusion([[A], [B, C]])
    assert set(scores) == {A, B, C}


def test_custom_k_changes_score_but_not_order() -> None:
    default_scores = reciprocal_rank_fusion([[A, B, C]])
    tight_scores = reciprocal_rank_fusion([[A, B, C]], k=1)
    assert default_scores[A] != tight_scores[A]
    assert tight_scores[A] > tight_scores[B] > tight_scores[C]
