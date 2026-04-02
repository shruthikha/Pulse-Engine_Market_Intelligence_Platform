"""
THIS TEST FOLDER IS AI GENERATED AND A PLACEHOLDER. IT WILL BE IMPROVED AND IMPLEMENTED AS IT GOES ON MANUALLY.
conftest.py — Import facade + all shared fixtures.

IMPORT FACADE
─────────────
When issue #4 lands and app.py is split into focused modules, update ONLY
the try/except block below. Every test file imports from conftest, so a
single change here propagates everywhere.
"""

from __future__ import annotations

import datetime as dt
import os

import pandas as pd
import pytest

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT FACADE
# Never import directly from app/storage/etc. in test files — import here.
# ═══════════════════════════════════════════════════════════════════════════

try:
    # Current monolithic structure
    from app import (
        compute_price_metrics,
        _classify_trend,
        compute_momentum_metrics,
        _compute_rsi,
        _compute_roc,
        deduplicate_articles,
        _jaccard,
        _normalize_title,
        score_sentiment,
        _fallback_sentiment,
        correlate_news,
        compute_signal_score,
        _detect_contradictions,
        build_explanation,
        analyse_asset,
        run_full_scan,
        fetch_news_articles,
        fetch_price_history,
        VADER_AVAILABLE,
    )
except ImportError:
    # Post-refactor structure — fill in module paths when #4 lands, then
    # remove the `raise` on the final line.
    # noqa comments silence IDE "module not found" / "protected member" warnings;
    # these imports only execute after app.py is split (never in current codebase).
    from price import compute_price_metrics, _classify_trend  # type: ignore  # noqa
    from momentum import compute_momentum_metrics, _compute_rsi, _compute_roc  # type: ignore  # noqa
    from dedup import deduplicate_articles, _jaccard, _normalize_title  # type: ignore  # noqa
    from sentiment import score_sentiment, _fallback_sentiment, VADER_AVAILABLE  # type: ignore  # noqa
    from news import correlate_news, fetch_news_articles  # type: ignore  # noqa
    from signals import compute_signal_score, _detect_contradictions  # type: ignore  # noqa
    from explanation import build_explanation  # type: ignore  # noqa
    from pipeline import analyse_asset, run_full_scan, fetch_price_history  # type: ignore  # noqa
    raise  # remove this line once all post-refactor import paths are filled in

import storage  # imported as a module so monkeypatch works on its attributes

# The module where fetch_price_history / fetch_news_articles are *called from*.
# When app.py is split, update this one string; all mock fixtures update automatically.
APP_MODULE = "app"


# ═══════════════════════════════════════════════════════════════════════════
# PRICE SERIES FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def price_series_flat():
    """40 identical values of 100.0 — RSI→50.0, ROC→0.0, trend→sideways."""
    return pd.Series([100.0] * 40)


@pytest.fixture
def price_series_rising():
    """40 values linearly increasing from 100.0 to 139.0 — RSI→100, ROC>0, trend→uptrend."""
    return pd.Series([100.0 + i for i in range(40)])


@pytest.fixture
def price_series_falling():
    """40 values linearly decreasing from 139.0 to 100.0 — RSI→0, ROC<0, trend→downtrend."""
    return pd.Series([139.0 - i for i in range(40)])


@pytest.fixture
def price_series_short():
    """5 values — exercises every 'not enough data' guard path."""
    return pd.Series([100.0, 101.0, 102.0, 101.0, 103.0])


# ═══════════════════════════════════════════════════════════════════════════
# OHLCV DATAFRAME FACTORY
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def ohlcv_df():
    """
    Factory fixture: call ohlcv_df(price_series) to get a yfinance-shaped
    DataFrame with Open, High, Low, Close, Volume columns.
    Close column equals the input series exactly.
    """
    def _make(price_series: pd.Series) -> pd.DataFrame:
        vals = price_series.values
        return pd.DataFrame(
            {
                "Open":   vals,
                "High":   vals * 1.005,
                "Low":    vals * 0.995,
                "Close":  vals,
                "Volume": [1000000] * len(vals),
            },
            index=price_series.index,
        )
    return _make


# ═══════════════════════════════════════════════════════════════════════════
# ARTICLE FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def synthetic_articles():
    """
    5 articles with the exact key shape that fetch_news_articles() returns:
      title, summary, link, source, published

    Layout:
      [0]  Gold article 1 (keywords: gold, bullion)
      [1]  Gold article 2 (different wording, same topic)
      [2]  Near-duplicate of [0]: identical token set, reordered → Jaccard = 1.0
      [3]  Clearly negative article (crash, plunge, crisis)
      [4]  Clearly positive article (surge, rally, record high)
    """
    now = dt.datetime.now(dt.timezone.utc)
    return [
        {
            "title":     "gold bullion prices surge on central bank demand",
            "summary":   "Gold bullion hits new highs as central banks drive buying.",
            "link":      "https://example.com/1",
            "source":    "Reuters Business",
            "published": now - dt.timedelta(hours=2),
        },
        {
            "title":     "central bank gold buying lifts bullion to record highs",
            "summary":   "Bullion advances as central banks increase gold reserves.",
            "link":      "https://example.com/2",
            "source":    "CNBC Top News",
            "published": now - dt.timedelta(hours=4),
        },
        {
            # Reordered tokens from article[0] → Jaccard == 1.0 >= DEDUP_SIMILARITY_THRESHOLD (0.65)
            "title":     "central bank demand surge on gold bullion prices",
            "summary":   "Central bank demand continues to push gold bullion prices higher.",
            "link":      "https://example.com/3",
            "source":    "BBC Business",
            "published": now - dt.timedelta(hours=5),
        },
        {
            "title":     "market crash plunge crisis recession fear selloff collapse",
            "summary":   "Markets in freefall as recession fears trigger massive crash and panic.",
            "link":      "https://example.com/4",
            "source":    "MarketWatch",
            "published": now - dt.timedelta(hours=6),
        },
        {
            "title":     "stocks surge rally record high breakout boom strong growth",
            "summary":   "Equity markets surge to record highs in a historic bullish rally.",
            "link":      "https://example.com/5",
            "source":    "Reuters Business",
            "published": now - dt.timedelta(hours=8),
        },
    ]


# ═══════════════════════════════════════════════════════════════════════════
# SYNTHETIC RESULT SHAPE FIXTURES
# These mirror the exact return shapes of production functions.
# If a function's return shape changes, update the fixture — and only here.
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def synthetic_metrics():
    """Realistic dict matching compute_price_metrics() return shape exactly."""
    return {
        "latest_price": 1850.50,
        "change_1d":    1.25,
        "change_7d":    3.40,
        "change_30d":   8.20,
        "high_30d":     1900.00,
        "low_30d":      1780.00,
        "volatility":   0.85,
        "trend":        "uptrend",
    }


@pytest.fixture
def synthetic_momentum():
    """Realistic dict matching compute_momentum_metrics() return shape exactly."""
    return {
        "rsi":            58.5,
        "roc_10d":        4.2,
        "trend_strength": 2.1,
        "momentum_accel": 0.3,
    }


@pytest.fixture
def synthetic_signal():
    """
    Dict matching compute_signal_score() return shape exactly.
    score=4.5 → label='Bullish' per config.SIGNAL_THRESHOLDS (>=3.0, <6.0).
    """
    return {
        "score":          4.5,
        "label":          "Bullish",
        "components":     {
            "trend": 2.0, "momentum": 1.5, "rsi": 0.5,
            "sentiment": 0.5, "trend_strength": 0.0, "context": 0.0,
        },
        "raw_components": {
            "trend": 2.0, "momentum": 1.5, "rsi": 0.5,
            "sentiment": 0.5, "trend_strength": 0.0, "context": 0.0,
        },
        "category": "Commodities",
    }


# ═══════════════════════════════════════════════════════════════════════════
# STORAGE FIXTURE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def storage_dir(tmp_path, monkeypatch):
    """
    Redirect all storage I/O to a fresh tmp_path for this test.

    Monkeypatches storage._storage_path (the only path constant derived at
    import time from STORAGE_DIR) so no real disk directory is ever created
    or read during tests.
    """
    monkeypatch.setattr(storage, "_storage_path", tmp_path)
    yield tmp_path


# ═══════════════════════════════════════════════════════════════════════════
# MOCK NETWORK FIXTURES
# Patch at APP_MODULE — update that one string when issue #4 lands.
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_price_history(mocker, ohlcv_df, price_series_rising):
    """Pre-built mock for fetch_price_history returning a valid 40-row OHLCV DataFrame."""
    df = ohlcv_df(price_series_rising)
    return mocker.patch(APP_MODULE + ".fetch_price_history", return_value=df)


@pytest.fixture
def mock_news_articles(mocker, synthetic_articles):
    """Pre-built mock for fetch_news_articles returning synthetic_articles."""
    return mocker.patch(APP_MODULE + ".fetch_news_articles", return_value=synthetic_articles)


@pytest.fixture
def mock_market_context(mocker):
    """Pre-built mock for analyse_market_context returning None (no context)."""
    return mocker.patch(APP_MODULE + ".analyse_market_context", return_value=None)


# ═══════════════════════════════════════════════════════════════════════════
# HYPER FLAG
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def hyper_enabled():
    """True only when HYPER_TESTS=1 is set in the environment."""
    return os.getenv("HYPER_TESTS") == "1"
