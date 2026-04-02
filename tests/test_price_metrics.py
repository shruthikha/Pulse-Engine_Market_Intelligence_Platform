"""
test_price_metrics.py — Contract tests for compute_price_metrics() and _classify_trend().

MINIMUM_REQUIRED_KEYS documents the stable output contract.
Tests assert structure and invariants, not exact float values.
"""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import compute_price_metrics, _classify_trend

# All keys that compute_price_metrics() MUST always return.
# New keys may be added freely; tests survive that because we use issubset.
MINIMUM_REQUIRED_KEYS = frozenset({
    "latest_price",
    "change_1d",
    "change_7d",
    "change_30d",
    "high_30d",
    "low_30d",
    "volatility",
    "trend",
})


# ── compute_price_metrics ────────────────────────────────────────────────────

class TestComputePriceMetricsGuards:
    def test_returns_empty_dict_for_none(self):
        assert compute_price_metrics(None) == {}

    def test_returns_empty_dict_for_empty_dataframe(self):
        assert compute_price_metrics(pd.DataFrame()) == {}


class TestComputePriceMetricsContract:
    def test_minimum_keys_present(self, ohlcv_df, price_series_rising):
        result = compute_price_metrics(ohlcv_df(price_series_rising))
        assert MINIMUM_REQUIRED_KEYS.issubset(result.keys())

    def test_latest_price_is_positive_float(self, ohlcv_df, price_series_rising):
        result = compute_price_metrics(ohlcv_df(price_series_rising))
        assert isinstance(result["latest_price"], float)
        assert result["latest_price"] > 0

    def test_latest_price_matches_last_close(self, ohlcv_df, price_series_rising):
        df = ohlcv_df(price_series_rising)
        result = compute_price_metrics(df)
        # round() precision matches the source (4 decimal places)
        assert result["latest_price"] == pytest.approx(float(df["Close"].iloc[-1]), rel=1e-4)

    def test_change_1d_is_none_for_single_row(self):
        """change_1d requires at least 2 rows (len(close) > 1)."""
        df = pd.DataFrame({"Close": [100.0]})
        result = compute_price_metrics(df)
        assert result["change_1d"] is None

    def test_change_values_are_floats_not_nan(self, ohlcv_df, price_series_rising):
        """All percentage change values, when not None, must be plain floats (no NaN)."""
        import math
        result = compute_price_metrics(ohlcv_df(price_series_rising))
        for key in ("change_1d", "change_7d", "change_30d"):
            val = result[key]
            if val is not None:
                assert isinstance(val, float), "{} should be float, got {}".format(key, type(val))
                assert not math.isnan(val), "{} should not be NaN".format(key)

    def test_change_1d_positive_for_rising_series(self, ohlcv_df, price_series_rising):
        result = compute_price_metrics(ohlcv_df(price_series_rising))
        assert result["change_1d"] is not None
        assert result["change_1d"] > 0

    def test_change_1d_negative_for_falling_series(self, ohlcv_df, price_series_falling):
        result = compute_price_metrics(ohlcv_df(price_series_falling))
        assert result["change_1d"] is not None
        assert result["change_1d"] < 0

    def test_volatility_is_zero_for_flat_series(self, ohlcv_df, price_series_flat):
        result = compute_price_metrics(ohlcv_df(price_series_flat))
        assert result["volatility"] == pytest.approx(0.0, abs=1e-6)

    def test_high_and_low_bracket_latest_price(self, ohlcv_df, price_series_rising):
        result = compute_price_metrics(ohlcv_df(price_series_rising))
        assert result["low_30d"] <= result["latest_price"] <= result["high_30d"]

    def test_returns_dict_for_short_series(self, ohlcv_df, price_series_short):
        """Does not raise or crash on short data; returns a dict."""
        result = compute_price_metrics(ohlcv_df(price_series_short))
        assert isinstance(result, dict)
        assert MINIMUM_REQUIRED_KEYS.issubset(result.keys())


# ── _classify_trend ──────────────────────────────────────────────────────────

class TestClassifyTrend:
    def test_uptrend_for_rising_series(self, price_series_rising):
        assert _classify_trend(price_series_rising) == "uptrend"

    def test_downtrend_for_falling_series(self, price_series_falling):
        assert _classify_trend(price_series_falling) == "downtrend"

    def test_sideways_for_flat_series(self, price_series_flat):
        assert _classify_trend(price_series_flat) == "sideways"

    def test_insufficient_data_for_short_series(self, price_series_short):
        """Series with fewer than 8 elements returns 'insufficient data'."""
        assert _classify_trend(price_series_short) == "insufficient data"

    def test_return_is_always_a_string(self, price_series_rising, price_series_falling,
                                       price_series_flat, price_series_short):
        """INVARIANT: return value is always str regardless of input."""
        for series in (price_series_rising, price_series_falling,
                       price_series_flat, price_series_short):
            assert isinstance(_classify_trend(series), str)

    def test_trend_label_is_one_of_known_values(self, price_series_rising):
        """Result must belong to the documented label set."""
        known = {"uptrend", "downtrend", "sideways", "insufficient data"}
        assert _classify_trend(price_series_rising) in known

    def test_trend_is_embedded_in_price_metrics(self, ohlcv_df, price_series_rising):
        """compute_price_metrics embeds _classify_trend result in its 'trend' key."""
        result = compute_price_metrics(ohlcv_df(price_series_rising))
        standalone = _classify_trend(price_series_rising)
        assert result["trend"] == standalone
