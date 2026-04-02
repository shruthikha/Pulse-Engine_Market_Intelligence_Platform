"""
THIS TEST FOLDER IS AI GENERATED AND A PLACEHOLDER. IT WILL BE IMPROVED AND IMPLEMENTED AS IT GOES ON MANUALLY
test_sentiment.py — Contract tests for score_sentiment() and _fallback_sentiment().

Both the VADER path and the keyword-fallback path are tested.
All tests must pass whether or not vaderSentiment is installed in the
test environment.
"""

from __future__ import annotations

import pytest

from conftest import score_sentiment, _fallback_sentiment

# All keys that every sentiment function MUST return.
MINIMUM_SENTIMENT_KEYS = frozenset({"compound", "pos", "neg", "neu"})

# Text fixtures — deterministic, no network.
_POSITIVE_TEXT = "stocks surge rally record high breakout boom strong growth"
_NEGATIVE_TEXT = "market crash plunge crisis recession fear selloff collapse"
_EMPTY_TEXT    = ""


# ── _fallback_sentiment (no mocking needed — pure keyword logic) ──────────────

class TestFallbackSentiment:
    def test_returns_dict_for_positive_text(self):
        result = _fallback_sentiment(_POSITIVE_TEXT)
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        result = _fallback_sentiment(_POSITIVE_TEXT)
        assert MINIMUM_SENTIMENT_KEYS.issubset(result.keys())

    def test_compound_invariant_in_range(self):
        """INVARIANT: compound always in [-1.0, 1.0]."""
        for text in (_POSITIVE_TEXT, _NEGATIVE_TEXT, _EMPTY_TEXT,
                     "the quick brown fox", "gold"):
            result = _fallback_sentiment(text)
            assert -1.0 <= result["compound"] <= 1.0, (
                "compound out of range for '{}': {}".format(text, result['compound'])
            )

    def test_positive_text_compound_gt_zero(self):
        result = _fallback_sentiment(_POSITIVE_TEXT)
        assert result["compound"] > 0

    def test_negative_text_compound_lt_zero(self):
        result = _fallback_sentiment(_NEGATIVE_TEXT)
        assert result["compound"] < 0

    def test_empty_string_does_not_raise(self):
        result = _fallback_sentiment(_EMPTY_TEXT)
        assert isinstance(result, dict)
        assert MINIMUM_SENTIMENT_KEYS.issubset(result.keys())

    def test_empty_string_compound_is_zero(self):
        """Empty input → no pos or neg words → compound == 0.0."""
        assert _fallback_sentiment(_EMPTY_TEXT)["compound"] == pytest.approx(0.0)

    def test_mixed_text_compound_in_range(self):
        mixed = "gold crash rally fear surge crisis boom collapse"
        result = _fallback_sentiment(mixed)
        assert -1.0 <= result["compound"] <= 1.0


# ── score_sentiment — VADER path (mocked so CI works without vaderSentiment) ──

class TestScoreSentimentVaderPath:
    """
    Monkeypatches VADER_AVAILABLE=True and injects a controlled mock analyzer.
    Tests the function's wiring to VADER, not VADER itself.
    """

    def test_required_keys_present(self, mocker):
        mocker.patch("app.VADER_AVAILABLE", True)
        mock_vader = mocker.MagicMock()
        mock_vader.polarity_scores.return_value = {
            "compound": 0.5, "pos": 0.3, "neg": 0.1, "neu": 0.6
        }
        mocker.patch("app._vader", mock_vader)
        result = score_sentiment(_POSITIVE_TEXT)
        assert MINIMUM_SENTIMENT_KEYS.issubset(result.keys())

    def test_compound_returned_from_vader(self, mocker):
        mocker.patch("app.VADER_AVAILABLE", True)
        mock_vader = mocker.MagicMock()
        mock_vader.polarity_scores.return_value = {
            "compound": 0.75, "pos": 0.5, "neg": 0.0, "neu": 0.5
        }
        mocker.patch("app._vader", mock_vader)
        result = score_sentiment("anything")
        assert result["compound"] == pytest.approx(0.75)

    def test_compound_invariant_in_range(self, mocker):
        """INVARIANT: compound always in [-1.0, 1.0] — even from VADER path."""
        mocker.patch("app.VADER_AVAILABLE", True)
        mock_vader = mocker.MagicMock()
        mock_vader.polarity_scores.return_value = {
            "compound": -0.9, "pos": 0.0, "neg": 0.9, "neu": 0.1
        }
        mocker.patch("app._vader", mock_vader)
        result = score_sentiment(_NEGATIVE_TEXT)
        assert -1.0 <= result["compound"] <= 1.0

    def test_empty_string_does_not_raise(self, mocker):
        mocker.patch("app.VADER_AVAILABLE", True)
        mock_vader = mocker.MagicMock()
        mock_vader.polarity_scores.return_value = {
            "compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0
        }
        mocker.patch("app._vader", mock_vader)
        result = score_sentiment(_EMPTY_TEXT)
        assert MINIMUM_SENTIMENT_KEYS.issubset(result.keys())


# ── score_sentiment — fallback path (VADER_AVAILABLE = False) ─────────────────

class TestScoreSentimentFallbackPath:
    """
    Monkeypatches VADER_AVAILABLE=False to force the keyword-counting fallback.
    Result structure must be identical to the VADER path.
    """

    def test_required_keys_present(self, mocker):
        mocker.patch("app.VADER_AVAILABLE", False)
        result = score_sentiment(_POSITIVE_TEXT)
        assert MINIMUM_SENTIMENT_KEYS.issubset(result.keys())

    def test_compound_invariant_in_range(self, mocker):
        mocker.patch("app.VADER_AVAILABLE", False)
        for text in (_POSITIVE_TEXT, _NEGATIVE_TEXT, _EMPTY_TEXT):
            result = score_sentiment(text)
            assert -1.0 <= result["compound"] <= 1.0

    def test_positive_text_compound_gt_zero(self, mocker):
        mocker.patch("app.VADER_AVAILABLE", False)
        result = score_sentiment(_POSITIVE_TEXT)
        assert result["compound"] > 0

    def test_negative_text_compound_lt_zero(self, mocker):
        mocker.patch("app.VADER_AVAILABLE", False)
        result = score_sentiment(_NEGATIVE_TEXT)
        assert result["compound"] < 0

    def test_empty_string_does_not_raise(self, mocker):
        mocker.patch("app.VADER_AVAILABLE", False)
        result = score_sentiment(_EMPTY_TEXT)
        assert isinstance(result, dict)
        assert MINIMUM_SENTIMENT_KEYS.issubset(result.keys())
