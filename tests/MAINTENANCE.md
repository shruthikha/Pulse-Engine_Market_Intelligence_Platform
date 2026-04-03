# Test Suite Maintenance Guide

THIS TEST FOLDER IS AI GENERATED AND A PLACEHOLDER. IT WILL BE IMPROVED AND IMPLEMENTED AS IT GOES ON MANUALLY.
This table tells future contributors exactly which tests are structural
(safe under churn) and which are fragile (require care on specific changes).

| Test file | Breaks if… | Safe when… |
|---|---|---|
| `test_price_metrics.py` | `compute_price_metrics()` return key names change, or `_classify_trend()` label strings are renamed | new keys added to result dict; float weights/thresholds change |
| `test_momentum.py` | `_compute_rsi` / `_compute_roc` / `compute_momentum_metrics()` return key names change | new keys added; RSI period default changes (see test_hyper.py for pin test) |
| `test_dedup_and_clustering.py` | `_jaccard()` or `deduplicate_articles()` internal logic changes structurally; article dict key `"title"` is renamed | `DEDUP_SIMILARITY_THRESHOLD` changes (only test_hyper.py breaks); new articles added to feeds |
| `test_sentiment.py` | `score_sentiment()` or `_fallback_sentiment()` key names change (`compound`, `pos`, `neg`, `neu`) | VADER installed / uninstalled; new sentiment words added to lexicon |
| `test_signal_score.py` | `compute_signal_score()` key names change; `SIGNAL_THRESHOLDS` range boundaries change; `_detect_contradictions()` condition operators change (< vs <=) | new components added to signal; `ASSET_CLASS_WEIGHTS` values tuned (only test_hyper.py breaks) |
| `test_storage.py` | `save_snapshot()` / `load_snapshots()` key names change; `_REDUCED_FIELDS` set changes (only test_hyper.py for exactness) | new snapshot fields added; retention day counts change |
| `test_integration.py` | `analyse_asset()` or `run_full_scan()` top-level return key names change; `APP_MODULE` constant in conftest.py is stale after issue #4 | new keys added to result; new assets added to TRACKED_ASSETS; market context logic changes |
| `test_backtest.py` | `evaluate_signal_accuracy()` return key names change; snapshot date-parsing logic in storage changes | new fields added to result; BACKTEST_WINDOW changes |
| `test_hyper.py` | **intentionally fragile** — each test pins a specific value | only runs when `HYPER_TESTS=1`; never runs in CI |

---

## When to update each file

### After issue #4 (app.py split)
1. Open `conftest.py`
2. Fill in the post-refactor imports in the `except ImportError` block
3. Remove the `raise` at the end of that block
4. Update `APP_MODULE = "app"` to the new module name that *calls* `fetch_price_history`
5. Run `pytest` — if all tests pass, the refactor is clean

### After issue #6 (error handling in fetch pipeline)
1. Find `test_integration.py::TestAnalyseAssetDegradedPath::test_handles_none_price_history`
2. The comment in that test explains the two possible outcomes
3. Update assertion to match whichever contract issue #6 establishes

### After issue #8 (new params on analyse_asset / run_scan)
1. All integration tests call `analyse_asset` with explicit keyword arguments
2. New parameters default to their old behavior → tests continue to pass
3. Only update tests if you want to exercise the new parameter explicitly

### When ASSET_CLASS_WEIGHTS are tuned
- Normal tests (`test_signal_score.py`) will still pass (they assert range, not exact value)
- Activate `test_hyper.py::test_signal_weight_single_component` with `HYPER_TESTS=1` to pin new values

### When DEDUP_SIMILARITY_THRESHOLD changes
- Normal tests will still pass (they test behavior above/below threshold, not the exact value)
- Activate `test_hyper.py::test_jaccard_boundary_value` to pin the new boundary behavior

---

## Running the test suite

```bash
# Normal run (excludes hyper tests)
pytest

# Run a specific file
pytest tests/test_signal_score.py -v

# Run hyper tests (active debugging only)
HYPER_TESTS=1 pytest tests/test_hyper.py -v

# CI-equivalent run (clean environment, no network)
pytest --tb=short -m "not hyper"
```
