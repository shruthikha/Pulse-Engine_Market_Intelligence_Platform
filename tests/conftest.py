"""
conftest.py — Import facade + shared fixtures.

IMPORT FACADE
─────────────
When app.py is split into focused modules (issue #4), update ONLY the
try/except block below. Every test file imports from conftest, so one
change propagates everywhere — no test file needs touching.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT FACADE
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
        score_sentiment,
        compute_signal_score,
        _detect_contradictions,
        analyse_asset,
        run_full_scan,
        fetch_price_history,
        fetch_news_articles,
    )
except ImportError:
    # Post-refactor paths — fill in when issue #4 lands, then remove `raise`.
    from price import compute_price_metrics, _classify_trend          # type: ignore  # noqa
    from momentum import compute_momentum_metrics, _compute_rsi, _compute_roc  # type: ignore  # noqa
    from dedup import deduplicate_articles, _jaccard                  # type: ignore  # noqa
    from sentiment import score_sentiment                              # type: ignore  # noqa
    from signals import compute_signal_score, _detect_contradictions  # type: ignore  # noqa
    from pipeline import analyse_asset, run_full_scan, fetch_price_history  # type: ignore  # noqa
    from news import fetch_news_articles                              # type: ignore  # noqa
    raise  # remove this line once all post-refactor import paths are filled in

import storage  # imported as module so monkeypatch works on its attributes

# Patch target for network calls — update this one string when issue #4 lands.
APP_MODULE = "app"


# ═══════════════════════════════════════════════════════════════════════════
# PRICE SERIES FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def price_series_flat():
    """40 identical values — RSI≈50, ROC≈0, trend→sideways."""
    return pd.Series([100.0] * 40)


@pytest.fixture
def price_series_rising():
    """40 strictly increasing values — RSI→100, ROC>0, trend→uptrend."""
    return pd.Series([100.0 + i for i in range(40)])


@pytest.fixture
def price_series_falling():
    """40 strictly decreasing values — RSI→0, ROC<0, trend→downtrend."""
    return pd.Series([139.0 - i for i in range(40)])


# ═══════════════════════════════════════════════════════════════════════════
# OHLCV DATAFRAME FACTORY
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def ohlcv_df():
    """Factory: ohlcv_df(series) → yfinance-shaped DataFrame."""
    def _make(series: pd.Series) -> pd.DataFrame:
        v = series.values
        return pd.DataFrame(
            {"Open": v, "High": v * 1.005, "Low": v * 0.995, "Close": v,
             "Volume": [1000000] * len(v)},
            index=series.index,
        )
    return _make


# ═══════════════════════════════════════════════════════════════════════════
# ARTICLE FIXTURE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def synthetic_articles():
    """5 articles: 2 gold, 1 near-duplicate, 1 negative, 1 positive."""
    now = dt.datetime.now(dt.timezone.utc)
    return [
        {"title": "gold bullion prices surge on central bank demand",
         "summary": "Gold hits new highs.", "link": "https://example.com/1",
         "source": "Reuters Business", "published": now - dt.timedelta(hours=2)},
        {"title": "central bank gold buying lifts bullion to record highs",
         "summary": "Bullion advances.", "link": "https://example.com/2",
         "source": "CNBC Top News", "published": now - dt.timedelta(hours=4)},
        {"title": "central bank demand surge on gold bullion prices",  # near-duplicate of [0]
         "summary": "Central bank demand pushes gold higher.", "link": "https://example.com/3",
         "source": "BBC Business", "published": now - dt.timedelta(hours=5)},
        {"title": "market crash plunge crisis recession fear selloff",
         "summary": "Markets in freefall.", "link": "https://example.com/4",
         "source": "MarketWatch", "published": now - dt.timedelta(hours=6)},
        {"title": "stocks surge rally record high breakout boom growth",
         "summary": "Equity markets surge to record highs.", "link": "https://example.com/5",
         "source": "Reuters Business", "published": now - dt.timedelta(hours=8)},
    ]


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL INPUT FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def synthetic_metrics():
    """Realistic compute_price_metrics()-shaped dict."""
    return {
        "latest_price": 1850.50, "change_1d": 1.25, "change_7d": 3.40,
        "change_30d": 8.20, "high_30d": 1900.00, "low_30d": 1780.00,
        "volatility": 0.85, "trend": "uptrend",
    }


@pytest.fixture
def synthetic_momentum():
    """Realistic compute_momentum_metrics()-shaped dict."""
    return {"rsi": 58.5, "roc_10d": 4.2, "trend_strength": 2.1, "momentum_accel": 0.3}


# ═══════════════════════════════════════════════════════════════════════════
# STORAGE ISOLATION
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def storage_dir(tmp_path, monkeypatch):
    """Redirect all storage I/O to a temp directory — no real disk writes."""
    monkeypatch.setattr(storage, "_storage_path", tmp_path)
    yield tmp_path


# ═══════════════════════════════════════════════════════════════════════════
# NETWORK MOCKS
# Update APP_MODULE above when issue #4 lands — these update automatically.
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_price_history(mocker, ohlcv_df, price_series_rising):
    return mocker.patch(APP_MODULE + ".fetch_price_history",
                        return_value=ohlcv_df(price_series_rising))


@pytest.fixture
def mock_news_articles(mocker, synthetic_articles):
    return mocker.patch(APP_MODULE + ".fetch_news_articles",
                        return_value=synthetic_articles)


@pytest.fixture
def mock_market_context(mocker):
    return mocker.patch(APP_MODULE + ".analyse_market_context", return_value=None)
