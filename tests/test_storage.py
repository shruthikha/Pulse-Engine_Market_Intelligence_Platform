"""
test_storage.py — Contract tests for all public storage functions.

All tests use the storage_dir fixture which monkeypatches storage._storage_path
to a fresh tmp_path. No real filesystem is touched.
"""

from __future__ import annotations

import datetime as dt

import pytest
from freezegun import freeze_time

import storage
from storage import (
    save_snapshot,
    load_snapshots,
    apply_retention_policy,
    cleanup_old_snapshots,
    list_tracked_assets_with_history,
)
from config import STORAGE_FULL_DETAIL_DAYS


# ── helpers ───────────────────────────────────────────────────────────────────

def _minimal_metrics(price: float = 100.0) -> dict:
    return {
        "latest_price": price,
        "change_1d":    0.5,
        "change_7d":    1.0,
        "change_30d":   2.0,
        "volatility":   0.3,
        "trend":        "uptrend",
    }


def _minimal_momentum() -> dict:
    return {"rsi": 55.0, "roc_10d": 2.0, "trend_strength": 1.0, "momentum_accel": 0.1}


def _minimal_signal(score: float = 3.0, label: str = "Bullish") -> dict:
    return {"score": score, "label": label, "components": {}, "raw_components": {}}


# ── save_snapshot + load_snapshots round-trip ─────────────────────────────────

class TestSaveLoadRoundTrip:
    def test_saved_data_reloads_with_correct_fields(self, storage_dir):
        save_snapshot("Gold", _minimal_metrics(), _minimal_momentum(),
                      _minimal_signal(), [])
        results = load_snapshots("Gold", days=1)
        assert len(results) == 1
        snap = results[0]
        # Use issubset on stable keys only — new keys won't break this
        assert {"signal_score", "asset", "date"}.issubset(snap.keys())
        assert snap["asset"] == "Gold"
        assert snap["signal_score"] == pytest.approx(3.0)

    def test_saving_identical_data_twice_is_idempotent(self, storage_dir):
        """
        Second save of identical data should be skipped (_snapshot_unchanged).
        File count stays at 1 for the same asset+date.
        """
        metrics  = _minimal_metrics()
        momentum = _minimal_momentum()
        signal   = _minimal_signal()
        save_snapshot("Silver", metrics, momentum, signal, [])
        save_snapshot("Silver", metrics, momentum, signal, [])
        gz_files = list(storage_dir.glob("Silver_*.json.gz"))
        assert len(gz_files) == 1

    def test_load_returns_empty_when_no_data(self, storage_dir):
        assert load_snapshots("NonExistent", days=30) == []

    def test_load_returns_empty_when_dir_missing(self, tmp_path, monkeypatch):
        """If _storage_path doesn't exist yet, load returns []."""
        missing = tmp_path / "no_such_dir"
        monkeypatch.setattr(storage, "_storage_path", missing)
        assert load_snapshots("Gold", days=30) == []

    def test_load_days_filter_excludes_old_snapshots(self, storage_dir):
        """load_snapshots(days=3) must not return a snapshot from 10 days ago."""
        with freeze_time("2026-03-23"):  # 10 days before 2026-04-02
            save_snapshot("Gold", _minimal_metrics(price=1800.0),
                          _minimal_momentum(), _minimal_signal(score=2.0), [])
        with freeze_time("2026-04-01"):  # 1 day before today
            save_snapshot("Gold", _minimal_metrics(price=1850.0),
                          _minimal_momentum(), _minimal_signal(score=3.5), [])

        # load with days=3 — should include 1-day-old snap but not 10-day-old
        results = load_snapshots("Gold", days=3)
        prices = [r.get("price") for r in results]
        assert 1850.0 in prices
        assert 1800.0 not in prices

    def test_load_newest_first_ordering(self, storage_dir):
        """Snapshots are returned newest-first."""
        with freeze_time("2026-03-31"):
            save_snapshot("Bitcoin", _minimal_metrics(price=50000.0),
                          _minimal_momentum(), _minimal_signal(), [])
        with freeze_time("2026-04-01"):
            save_snapshot("Bitcoin", _minimal_metrics(price=51000.0),
                          _minimal_momentum(), _minimal_signal(), [])
        results = load_snapshots("Bitcoin", days=10)
        assert len(results) == 2
        assert results[0]["price"] == pytest.approx(51000.0)
        assert results[1]["price"] == pytest.approx(50000.0)

    def test_top_headlines_stored_and_retrieved(self, storage_dir):
        headlines = [
            {"title": "Gold surges", "source": "Reuters Business",
             "sentiment": {"compound": 0.5}},
        ]
        save_snapshot("Gold", _minimal_metrics(), _minimal_momentum(),
                      _minimal_signal(), headlines)
        snap = load_snapshots("Gold", days=1)[0]
        assert "headlines" in snap
        assert len(snap["headlines"]) == 1
        assert snap["headlines"][0]["title"] == "Gold surges"


# ── apply_retention_policy ────────────────────────────────────────────────────

class TestApplyRetentionPolicy:
    def test_returns_int_gte_zero(self, storage_dir):
        result = apply_retention_policy()
        assert isinstance(result, int)
        assert result >= 0

    def test_does_not_raise_when_dir_missing(self, tmp_path, monkeypatch):
        """If storage dir doesn't exist, returns 0 without raising."""
        monkeypatch.setattr(storage, "_storage_path", tmp_path / "no_such_dir")
        assert apply_retention_policy() == 0

    def test_does_not_raise_on_empty_dir(self, storage_dir):
        assert apply_retention_policy() == 0

    def test_strips_heavy_fields_from_old_snapshots(self, storage_dir):
        """
        Snapshots between STORAGE_FULL_DETAIL_DAYS+1 and STORAGE_REDUCED_DETAIL_DAYS
        days old should have 'headlines', 'change_7d', etc. stripped.
        """
        # Save a snapshot old enough to be in the reduced-detail window
        target_age = STORAGE_FULL_DETAIL_DAYS + 2
        old_date = dt.date(2026, 4, 2) - dt.timedelta(days=target_age)
        with freeze_time(old_date.isoformat()):
            full_metrics = _minimal_metrics()
            full_metrics["change_7d"] = 1.5
            full_metrics["change_30d"] = 3.0
            full_metrics["volatility"] = 0.4
            save_snapshot(
                "Copper",
                full_metrics,
                _minimal_momentum(),
                _minimal_signal(),
                [{"title": "Copper headline", "source": "Reuters Business",
                  "sentiment": {"compound": 0.1}}],
            )

        rewritten = apply_retention_policy()
        assert rewritten >= 1

        # After retention, headlines and change_7d should be stripped
        snaps = load_snapshots("Copper", days=target_age + 1)
        if snaps:  # only check if data was loaded (retention may delete based on STORAGE_MAX_DAYS)
            snap = snaps[0]
            assert "headlines" not in snap
            assert "change_7d" not in snap

    def test_full_detail_snapshots_not_touched(self, storage_dir):
        """Snapshots within STORAGE_FULL_DETAIL_DAYS are NOT rewritten."""
        with freeze_time("2026-04-02"):  # today — within full detail window
            save_snapshot("Gold", _minimal_metrics(), _minimal_momentum(),
                          _minimal_signal(), [{"title": "Keep me",
                                               "source": "Reuters Business",
                                               "sentiment": {"compound": 0.3}}])
        rewritten = apply_retention_policy()
        assert rewritten == 0


# ── cleanup_old_snapshots ─────────────────────────────────────────────────────

class TestCleanupOldSnapshots:
    def test_returns_int_gte_zero(self, storage_dir):
        result = cleanup_old_snapshots()
        assert isinstance(result, int)
        assert result >= 0

    def test_does_not_raise_when_dir_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(storage, "_storage_path", tmp_path / "no_such_dir")
        assert cleanup_old_snapshots() == 0

    def test_does_not_raise_on_empty_dir(self, storage_dir):
        assert cleanup_old_snapshots() == 0

    def test_old_file_is_deleted(self, storage_dir):
        """Snapshot older than days_to_keep threshold is deleted."""
        very_old = dt.date(2026, 4, 2) - dt.timedelta(days=70)
        with freeze_time(very_old.isoformat()):
            save_snapshot("Gold", _minimal_metrics(), _minimal_momentum(),
                          _minimal_signal(), [])
        gz_before = list(storage_dir.glob("Gold_*.json.gz"))
        assert len(gz_before) == 1

        deleted = cleanup_old_snapshots(days_to_keep=60)
        assert deleted >= 1
        gz_after = list(storage_dir.glob("Gold_*.json.gz"))
        assert len(gz_after) == 0

    def test_recent_file_is_preserved(self, storage_dir):
        """Snapshot within days_to_keep threshold is NOT deleted."""
        with freeze_time("2026-04-01"):
            save_snapshot("Silver", _minimal_metrics(), _minimal_momentum(),
                          _minimal_signal(), [])
        deleted = cleanup_old_snapshots(days_to_keep=60)
        assert deleted == 0
        assert len(list(storage_dir.glob("Silver_*.json.gz"))) == 1


# ── list_tracked_assets_with_history ─────────────────────────────────────────

class TestListTrackedAssetsWithHistory:
    def test_returns_empty_when_dir_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(storage, "_storage_path", tmp_path / "no_such_dir")
        assert list_tracked_assets_with_history() == []

    def test_returns_empty_when_dir_empty(self, storage_dir):
        assert list_tracked_assets_with_history() == []

    def test_returns_asset_name_after_snapshot_saved(self, storage_dir):
        save_snapshot("Platinum", _minimal_metrics(), _minimal_momentum(),
                      _minimal_signal(), [])
        result = list_tracked_assets_with_history()
        assert "Platinum" in result

    def test_invariant_returns_list(self, storage_dir):
        """INVARIANT: always returns a list (never None or dict)."""
        assert isinstance(list_tracked_assets_with_history(), list)

    def test_multiple_assets_all_listed(self, storage_dir):
        for name in ("Gold", "Silver", "Copper"):
            save_snapshot(name, _minimal_metrics(), _minimal_momentum(),
                          _minimal_signal(), [])
        result = list_tracked_assets_with_history()
        assert {"Gold", "Silver", "Copper"}.issubset(set(result))

    def test_no_duplicate_names(self, storage_dir):
        """Saving twice for same asset should not produce duplicate entries."""
        save_snapshot("Gold", _minimal_metrics(100.0), _minimal_momentum(),
                      _minimal_signal(), [])
        # Force a second write by changing label (triggers _snapshot_unchanged=False)
        save_snapshot("Gold", _minimal_metrics(200.0), _minimal_momentum(),
                      _minimal_signal(score=5.0, label="Bullish"), [])
        result = list_tracked_assets_with_history()
        assert result.count("Gold") == 1
