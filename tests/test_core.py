"""
test_core.py — Sanity and invariant tests for pure functions.

Goal: each function runs without crashing and its output is sane.
Not testing exact values — testing that outputs are usable.

Imports from app (the backward-compat shim) to verify the shim itself works,
and directly from the src modules to verify the canonical path.
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

# Backward-compat shim imports — these must keep working
from app.analysis import (
    _compute_rsi,
    _compute_roc,
    compute_momentum_metrics,
    compute_price_metrics,
    compute_signal_score,
    score_sentiment,
    deduplicate_articles,
)

from src.errors import DataFetchError
from src.news import fetch_news_articles
from src.price import fetch_price_history

# Canonical imports — new code should use these
from src.price import _compute_rsi as _src_rsi, _compute_roc as _src_roc
from src.sentiment import score_sentiment as src_score_sentiment
from src.news import deduplicate_articles as src_dedup
from src.signals import compute_signal_score as src_signal_score


# ── RSI ───────────────────────────────────────────────────────────────────────

def test_rsi_always_in_range(price_series_rising, price_series_falling, price_series_flat):
    """INVARIANT: RSI must always be between 0 and 100, no matter what."""
    for series in [price_series_rising, price_series_falling, price_series_flat]:
        result = _compute_rsi(series)
        assert 0.0 <= result <= 100.0


def test_rsi_direction(price_series_rising, price_series_falling):
    """Rising series → RSI above 50. Falling → RSI below 50."""
    assert _compute_rsi(price_series_rising) > 50
    assert _compute_rsi(price_series_falling) < 50


def test_src_rsi_matches_shim(price_series_rising):
    """src.price._compute_rsi must return the same result as the shim."""
    assert _src_rsi(price_series_rising) == _compute_rsi(price_series_rising)


# ── ROC ───────────────────────────────────────────────────────────────────────

def test_roc_sign(price_series_rising, price_series_falling):
    """ROC should be positive for an uptrend and negative for a downtrend."""
    assert _compute_roc(price_series_rising) > 0
    assert _compute_roc(price_series_falling) < 0


def test_src_roc_matches_shim(price_series_rising):
    """src.price._compute_roc must return the same result as the shim."""
    assert _src_roc(price_series_rising) == _compute_roc(price_series_rising)


# ── Momentum metrics ──────────────────────────────────────────────────────────

def test_momentum_metrics_runs(ohlcv_df, price_series_rising):
    """compute_momentum_metrics should return a dict with an 'rsi' key."""
    result = compute_momentum_metrics(ohlcv_df(price_series_rising))
    assert isinstance(result, dict)
    assert "rsi" in result


# ── Price metrics ─────────────────────────────────────────────────────────────

def test_price_metrics_runs(ohlcv_df, price_series_rising):
    """compute_price_metrics should return a dict with a usable latest_price."""
    result = compute_price_metrics(ohlcv_df(price_series_rising))
    assert isinstance(result, dict)
    assert result.get("latest_price") is not None
    assert result["latest_price"] > 0


# ── Signal score ──────────────────────────────────────────────────────────────

def test_signal_score_in_range(synthetic_metrics, synthetic_momentum):
    """INVARIANT: score must always be clamped to [-10, 10]."""
    result = compute_signal_score(synthetic_metrics, synthetic_momentum, [])
    assert -10.0 <= result["score"] <= 10.0


def test_src_signal_score_in_range(synthetic_metrics, synthetic_momentum):
    """Same invariant via the canonical src.signals import."""
    result = src_signal_score(synthetic_metrics, synthetic_momentum, [])
    assert -10.0 <= result["score"] <= 10.0


# ── Sentiment ─────────────────────────────────────────────────────────────────

def test_sentiment_compound_in_range():
    """INVARIANT: sentiment compound must always be in [-1, 1]."""
    result = score_sentiment("markets are crashing hard, major losses everywhere")
    assert -1.0 <= result["compound"] <= 1.0


def test_src_sentiment_compound_in_range():
    """Same invariant via the canonical src.sentiment import."""
    result = src_score_sentiment("markets are crashing hard, major losses everywhere")
    assert -1.0 <= result["compound"] <= 1.0


# ── Deduplication ─────────────────────────────────────────────────────────────

def test_dedup_reduces_or_preserves_count(synthetic_articles):
    """Dedup should never produce more articles than it received."""
    result = deduplicate_articles(synthetic_articles)
    assert 0 < len(result) <= len(synthetic_articles)


def test_src_dedup_reduces_or_preserves_count(synthetic_articles):
    """Same invariant via the canonical src.news import."""
    result = src_dedup(synthetic_articles)
    assert 0 < len(result) <= len(synthetic_articles)


# ── Fetch resilience ────────────────────────────────────────────────────────

def test_fetch_price_history_returns_none_for_empty_data(mocker):
    """Empty responses should stay empty rather than becoming fetch errors."""
    mocker.patch("src.price.MAX_RETRIES", 1)
    mocker.patch("src.price.time.sleep", return_value=None)
    mocker.patch("src.price.yf.download", return_value=pd.DataFrame())
    ticker_mock = mocker.Mock()
    ticker_mock.history.return_value = pd.DataFrame()
    mocker.patch("src.price.yf.Ticker", return_value=ticker_mock)

    result = fetch_price_history("TEST", days=1)
    assert result is None


def test_fetch_price_history_raises_on_fetch_failure(mocker):
    """Transport failures should raise a fetch error after retries."""
    mocker.patch("src.price.MAX_RETRIES", 1)
    mocker.patch("src.price.time.sleep", return_value=None)
    mocker.patch("src.price.yf.download", side_effect=RuntimeError("boom"))
    ticker_mock = mocker.Mock()
    ticker_mock.history.side_effect = RuntimeError("boom")
    mocker.patch("src.price.yf.Ticker", return_value=ticker_mock)

    with pytest.raises(DataFetchError):
        fetch_price_history("TEST", days=1)


def test_fetch_news_articles_uses_explicit_timeout(mocker):
    """RSS fetches should be bounded by an explicit timeout."""
    mocker.patch("src.news.NEWS_FEEDS", [("Test Feed", "https://example.com/feed")])
    mocker.patch("src.news.MAX_WORKERS", 1)

    response = mocker.MagicMock()
    response.read.return_value = b"<rss />"
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    urlopen_mock = mocker.patch("src.news.urllib.request.urlopen", return_value=response)
    mocker.patch(
        "src.news.feedparser.parse",
        return_value=SimpleNamespace(entries=[]),
    )

    fetch_news_articles()
    assert urlopen_mock.call_args.kwargs["timeout"] > 0
