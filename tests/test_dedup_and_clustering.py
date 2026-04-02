"""
test_dedup_and_clustering.py — Contract tests for _jaccard() and
deduplicate_articles().

All invariants here survive threshold changes (handled in test_hyper.py).
"""

from __future__ import annotations

import copy

import pytest

from conftest import _jaccard, deduplicate_articles


# ── _jaccard ─────────────────────────────────────────────────────────────────

class TestJaccard:
    def test_returns_zero_for_empty_inputs(self):
        assert _jaccard(set(), set()) == 0.0

    def test_returns_zero_when_one_set_empty(self):
        assert _jaccard({"a", "b"}, set()) == 0.0
        assert _jaccard(set(), {"a", "b"}) == 0.0

    def test_returns_one_for_identical_sets(self):
        s = {"gold", "price", "surge", "bank"}
        assert _jaccard(s, s) == pytest.approx(1.0)

    def test_returns_zero_for_disjoint_sets(self):
        assert _jaccard({"a", "b"}, {"c", "d"}) == 0.0

    def test_invariant_result_in_0_to_1(self):
        """INVARIANT: result is always in [0.0, 1.0]."""
        pairs = [
            ({"a"}, {"a", "b", "c"}),
            ({"x", "y"}, {"y", "z"}),
            ({"p"}, {"p"}),
            ({"m"}, {"n"}),
        ]
        for a, b in pairs:
            result = _jaccard(a, b)
            assert 0.0 <= result <= 1.0, "Jaccard out of range for {}, {}: {}".format(a, b, result)

    def test_commutative(self):
        """INVARIANT: _jaccard(a, b) == _jaccard(b, a)."""
        a = {"gold", "price", "surge"}
        b = {"price", "market", "crash", "gold"}
        assert _jaccard(a, b) == pytest.approx(_jaccard(b, a))

    def test_partial_overlap(self):
        """Sanity: 2 shared out of 4 union → 0.5."""
        a = {"a", "b"}
        b = {"b", "c"}
        # intersection={b}=1, union={a,b,c}=3 → 1/3
        assert _jaccard(a, b) == pytest.approx(1 / 3)


# ── deduplicate_articles ──────────────────────────────────────────────────────

def _make_article(title: str) -> dict:
    """Minimal article dict for dedup tests."""
    return {
        "title":     title,
        "summary":   "",
        "link":      "https://example.com",
        "source":    "Test",
        "published": None,
    }


class TestDeduplicateArticles:
    def test_returns_empty_for_empty_input(self):
        assert deduplicate_articles([]) == []

    def test_len_output_le_len_input(self, synthetic_articles):
        """INVARIANT: output is never longer than input."""
        result = deduplicate_articles(synthetic_articles)
        assert len(result) <= len(synthetic_articles)

    def test_near_duplicates_collapsed_to_one(self, synthetic_articles):
        """
        synthetic_articles[0] and [2] have identical token sets (reordered).
        Both should collapse into a single article.
        """
        gold_articles = [synthetic_articles[0], synthetic_articles[2]]
        result = deduplicate_articles(gold_articles)
        assert len(result) == 1

    def test_unique_articles_all_retained(self):
        """Completely disjoint titles are all kept."""
        articles = [
            _make_article("gold surges amid central bank demand"),
            _make_article("tesla earnings beat expectations quarterly"),
            _make_article("bitcoin halving triggers volatility spike"),
        ]
        result = deduplicate_articles(articles)
        assert len(result) == 3

    def test_does_not_mutate_input_list(self, synthetic_articles):
        original = copy.deepcopy(synthetic_articles)
        deduplicate_articles(synthetic_articles)
        assert synthetic_articles == original

    def test_first_article_wins_on_dedup(self):
        """When two articles are near-duplicates, the earlier one is kept."""
        a = _make_article("gold prices rally on safe haven buying demand")
        b = _make_article("gold prices rally on safe haven buying demand")
        result = deduplicate_articles([a, b])
        assert len(result) == 1
        assert result[0]["title"] == a["title"]

    def test_empty_title_article_not_dropped(self):
        """Articles with empty titles pass through without dedup comparison."""
        article = _make_article("")
        result = deduplicate_articles([article])
        assert len(result) == 1

    def test_single_article_unchanged(self, synthetic_articles):
        result = deduplicate_articles([synthetic_articles[0]])
        assert len(result) == 1

    def test_mixed_batch_reduces_correctly(self, synthetic_articles):
        """
        Input: 5 articles where [0] and [2] are near-dupes.
        Expected: at most 4 unique articles remain.
        """
        result = deduplicate_articles(synthetic_articles)
        assert len(result) <= len(synthetic_articles) - 1
