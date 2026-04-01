# Variable and Constant Reference

[![Source: config.py](https://img.shields.io/badge/Source-config.py-64748b?style=flat-square)]()
[![Source: app.py](https://img.shields.io/badge/Source-app.py-3776AB?style=flat-square)]()
[![Source: dashboard.py](https://img.shields.io/badge/Source-dashboard.py-FF4B4B?style=flat-square)]()
[![Source: storage.py](https://img.shields.io/badge/Source-storage.py-f59e0b?style=flat-square)]()
[![Source: scan.py](https://img.shields.io/badge/Source-scan.py-22c55e?style=flat-square)]()
[![Source: backtest.py](https://img.shields.io/badge/Source-backtest.py-7c3aed?style=flat-square)]()

This document lists every significant constant, module-level variable, function parameter, and return structure across the codebase. Types follow Python annotation conventions.

---

## config.py — All Constants

### 1. Asset Configuration

| Name | Type | Value / Shape | Description |
|---|---|---|---|
| `TRACKED_ASSETS` | `dict[str, dict[str, str]]` | 4 categories, 24 assets | Top-level map from category name to `{asset_name: yahoo_ticker}`. The only place tickers are defined. |
| `SECTOR_PEERS` | `dict[str, list[str]]` | 22 keys | Maps each asset name to a list of peer asset names used for sector correlation in `analyse_market_context`. |
| `MARKET_BENCHMARK` | `dict[str, str]` | 4 keys | Maps each category to a benchmark ticker (e.g. Commodities -> `^GSPC`). |

### 2. News Feeds

| Name | Type | Value | Description |
|---|---|---|---|
| `NEWS_FEEDS` | `list[tuple[str, str]]` | 12 entries | List of `(feed_name, url)` tuples. Feed name is used as the key in `SOURCE_WEIGHTS`. |

### 3. Keyword and Event Configuration

| Name | Type | Shape | Description |
|---|---|---|---|
| `ASSET_KEYWORDS` | `dict[str, list[tuple[str, int]]]` | 24 assets | Maps each asset name to a list of `(keyword, weight)` tuples. Weight is 1, 2, or 3. Used in `correlate_news`. |
| `EVENT_TRIGGERS` | `dict[str, dict]` | 8 event types | Maps event category ID to a dict with `keywords: list[str]`, `label: str`, and `icon: str`. Used in `detect_events`. |

### 4. Data Settings

| Name | Type | Default | Description |
|---|---|---|---|
| `LOOKBACK_DAYS` | `int` | 30 | Number of calendar days of price history to fetch from Yahoo Finance. |
| `PRICE_CHANGE_THRESHOLD` | `float` | 2.0 | Percent change above which the dashboard displays a significant move alert. |
| `NEWS_MAX_AGE_HOURS` | `int` | 96 | Articles older than this are discarded during ingestion. |
| `NEWS_MAX_ARTICLES` | `int` | 300 | Maximum number of articles retained in the pool after deduplication. |
| `RELEVANCE_HIGH` | `int` | 6 | Minimum relevance score for a news article to be considered high-relevance. |
| `RELEVANCE_MEDIUM` | `int` | 3 | Minimum relevance score for medium-relevance articles included in correlation. |
| `DEDUP_SIMILARITY_THRESHOLD` | `float` | 0.65 | Jaccard similarity threshold above which two articles are considered duplicates. |

### 5. Dashboard Settings

| Name | Type | Default | Description |
|---|---|---|---|
| `DASHBOARD_TITLE` | `str` | `"Market Intelligence Platform"` | Browser tab title and sidebar header. |
| `DASHBOARD_ICON` | `str` | `"📊"` | Favicon icon for the Streamlit page. |
| `DASHBOARD_LAYOUT` | `str` | `"wide"` | Streamlit page layout. |
| `AUTO_REFRESH_SECONDS` | `int` | 90 | Page auto-refresh interval. Defined in config but controlled by `st.rerun` trigger. |
| `CHART_HEIGHT` | `int` | 420 | Height in pixels for Plotly price charts. |
| `DEFAULT_CATEGORY` | `str` | `"Commodities"` | Category selected on first load. |

### 6. Cache and Performance

| Name | Type | Default | Description |
|---|---|---|---|
| `PRICE_CACHE_TTL` | `int` | 90 | TTL in seconds for `@st.cache_data` on price history and metrics functions. |
| `NEWS_CACHE_TTL` | `int` | 300 | TTL in seconds for `@st.cache_data` on news fetching. |
| `REQUEST_TIMEOUT` | `int` | 20 | HTTP timeout in seconds applied to all RSS feed fetch requests. |
| `MAX_RETRIES` | `int` | 2 | Number of retry attempts for failed Yahoo Finance requests. |
| `MAX_WORKERS` | `int` | 8 | Thread pool size for parallel data fetching (news feeds, peer prices). |

### 7. Source Credibility Weights

| Name | Type | Shape | Description |
|---|---|---|---|
| `SOURCE_WEIGHTS` | `dict[str, float]` | 12 entries | Maps feed name to a credibility multiplier applied during news correlation. Range: 0.90 – 1.35. |

### 8. Momentum Settings

| Name | Type | Default | Description |
|---|---|---|---|
| `RSI_PERIOD` | `int` | 14 | Lookback window for the Relative Strength Index calculation. |
| `MOMENTUM_PERIOD` | `int` | 10 | Number of days for the rate-of-change (ROC) calculation. |

### 9. Signal Thresholds

| Name | Type | Shape | Description |
|---|---|---|---|
| `SIGNAL_THRESHOLDS` | `dict[str, float]` | 6 keys | Maps signal label identifiers to the minimum score for that label. Labels below the `bearish` threshold are classified as `strong_bearish`. |

### 10. Asset Class Weights

| Name | Type | Shape | Description |
|---|---|---|---|
| `ASSET_CLASS_WEIGHTS` | `dict[str, dict[str, float]]` | 4 classes, 6 components each | Per-class multipliers for trend, momentum, rsi, sentiment, trend_strength, and context components of the signal score. |

### 11. Storage Retention

| Name | Type | Default | Description |
|---|---|---|---|
| `STORAGE_DIR` | `str` | `"market_data"` | Relative path to the snapshot storage directory. |
| `STORAGE_FULL_DETAIL_DAYS` | `int` | 7 | Snapshots younger than this retain all fields including headlines. |
| `STORAGE_REDUCED_DETAIL_DAYS` | `int` | 30 | Snapshots between this and `STORAGE_FULL_DETAIL_DAYS` retain reduced fields. |
| `STORAGE_MAX_DAYS` | `int` | 60 | Snapshots older than this are deleted by `cleanup_old_snapshots`. |
| `SNAPSHOT_LOAD_LIMIT` | `int` | 20 | Default maximum number of snapshots loaded by `load_recent_snapshots`. |
| `BACKTEST_WINDOW` | `int` | 20 | Maximum number of historical signals evaluated in one backtest run. |
| `SCAN_INTERVAL_MINUTES` | `int` | 30 | Minimum minutes between automatic background scans. |

---

## app.py — Module-Level Variables and Function Signatures

### Module-Level

| Name | Type | Description |
|---|---|---|
| `VADER_AVAILABLE` | `bool` | Set to `True` if `vaderSentiment` imported successfully, `False` if fallback keyword scoring is used. |
| `STORAGE_AVAILABLE` | `bool` | Set to `True` if `storage.save_snapshot` imported successfully. |
| `_save_snapshot` | `Callable` | Alias for `storage.save_snapshot`, or a no-op lambda if storage is unavailable. |
| `log` | `logging.Logger` | Module-level logger named after `__name__`. |

### Function Signatures and Return Structures

#### `fetch_price_history(ticker, days)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ticker` | `str` | — | Yahoo Finance ticker symbol |
| `days` | `int` | `LOOKBACK_DAYS` | Number of calendar days to fetch |

Returns `pd.DataFrame` with columns `Open High Low Close Volume Adj Close` indexed by date, or `None` on failure.

---

#### `compute_price_metrics(df)`

| Parameter | Type | Description |
|---|---|---|
| `df` | `Optional[pd.DataFrame]` | OHLCV DataFrame from `fetch_price_history` |

Returns `dict`:

| Key | Type | Description |
|---|---|---|
| `latest_price` | `float` | Most recent Close value |
| `change_1d` | `Optional[float]` | Percentage change over 1 trading day |
| `change_7d` | `Optional[float]` | Percentage change over 7 trading days |
| `change_30d` | `Optional[float]` | Percentage change over 30 trading days |
| `high_30d` | `float` | 30-day rolling high |
| `low_30d` | `float` | 30-day rolling low |
| `volatility` | `float` | Standard deviation of daily returns (pct_change fill_method=None) multiplied by 100 |
| `trend` | `str` | `"uptrend"`, `"downtrend"`, or `"sideways"` |

---

#### `compute_momentum_metrics(df)`

Returns `dict`:

| Key | Type | Description |
|---|---|---|
| `rsi` | `Optional[float]` | 14-period RSI. None if insufficient history |
| `roc_10d` | `Optional[float]` | 10-day rate of change as percentage |
| `trend_strength` | `Optional[float]` | Divergence of 7-day MA from 30-day MA as percentage |
| `momentum_accel` | `Optional[float]` | Recent 5-day ROC minus prior 5-day ROC |

---

#### `fetch_news_articles()`

Takes no parameters. Returns `list[dict]` where each dict contains:

| Key | Type | Description |
|---|---|---|
| `title` | `str` | Article headline, HTML stripped |
| `summary` | `str` | Article body excerpt, HTML stripped, max 600 chars |
| `source` | `str` | Feed name matching a key in `SOURCE_WEIGHTS` |
| `pub_date` | `Optional[datetime]` | Publication datetime (UTC) |
| `sentiment` | `dict` | Output of `score_sentiment` |
| `url` | `str` | Article link |

---

#### `score_sentiment(text)`

Returns `dict`:

| Key | Type | Description |
|---|---|---|
| `compound` | `float` | Composite score -1.0 to +1.0 |
| `pos` | `float` | Positive component 0.0 to 1.0 |
| `neg` | `float` | Negative component 0.0 to 1.0 |
| `neu` | `float` | Neutral component 0.0 to 1.0 |

---

#### `correlate_news(asset_name, articles)`

Returns `list[dict]` — same structure as `fetch_news_articles` output, filtered and extended with:

| Key | Type | Description |
|---|---|---|
| `relevance_score` | `float` | Weighted keyword match score, boosted by recency and source credibility |
| `events_detected` | `list[str]` | Event category labels from `detect_events` |

Sorted descending by `relevance_score`.

---

#### `compute_signal_score(metrics, momentum, news, market_ctx, category)`

Returns `dict`:

| Key | Type | Description |
|---|---|---|
| `score` | `float` | Composite score clamped to -10.0 to +10.0 |
| `label` | `str` | Human-readable label from `SIGNAL_THRESHOLDS` |
| `components` | `dict[str, float]` | Per-component contributions before clamping |

---

#### `analyse_market_context(asset_name, category, asset_change)`

Returns `dict`:

| Key | Type | Description |
|---|---|---|
| `peer_moves` | `dict[str, Optional[float]]` | 1-day percentage change for each sector peer |
| `benchmark_change` | `Optional[float]` | 1-day percentage change of the category benchmark |
| `is_sector_wide` | `bool` | True if >= 60% of peers moved in the same direction |
| `is_market_wide` | `bool` | True if benchmark moved > 0.5% in the same direction |
| `is_asset_specific` | `bool` | True if neither sector-wide nor market-wide |

---

#### `build_explanation(asset_name, metrics, news, market_ctx, momentum, signal)`

Returns `dict`:

| Key | Type | Description |
|---|---|---|
| `verdict` | `str` | One-line summary sentence |
| `why_it_matters` | `str` | Contextual significance paragraph |
| `detail` | `str` | Full markdown narrative with all contributing factors |
| `confidence` | `str` | `"high"`, `"medium"`, or `"low"` |
| `factors` | `list[dict]` | List of factor dicts each with `type`, `label`, `detail` keys |
| `contradictions` | `list[str]` | Human-readable list of detected signal conflicts |

---

#### `analyse_asset(asset_name, ticker, category, articles, with_market_ctx)`

Returns `dict`:

| Key | Type | Description |
|---|---|---|
| `ticker` | `str` | Yahoo Finance ticker |
| `history` | `pd.DataFrame` | Raw OHLCV DataFrame |
| `metrics` | `dict` | Output of `compute_price_metrics` |
| `momentum` | `dict` | Output of `compute_momentum_metrics` |
| `news` | `list[dict]` | Output of `correlate_news` |
| `clusters` | `dict` | Output of `cluster_articles` |
| `market_ctx` | `Optional[dict]` | Output of `analyse_market_context` or None |
| `signal` | `dict` | Output of `compute_signal_score` |
| `explanation` | `dict` | Output of `build_explanation` |
| `historical_features` | `dict` | Output of `storage.get_historical_features` |

---

## dashboard.py — Session State, Singleton State, and UI Variables

### Singleton Scan State (via `@st.cache_resource`)

| Key in `_get_scan_state()` | Type | Description |
|---|---|---|
| `lock` | `threading.Lock` | Prevents concurrent scan threads. Acquired before starting, released in `finally` block. |
| `running` | `bool` | True while a scan thread is active. |
| `last_started` | `float` | `time.time()` value when the most recent scan was initiated. |
| `last_finished` | `float` | `time.time()` value when the most recent scan completed. |
| `error` | `str` | Error message string if the last scan raised an exception, empty string otherwise. |
| `assets_done` | `int` | Number of assets successfully processed in the last scan. |

### `st.session_state` Keys

| Key | Type | Description |
|---|---|---|
| `_scan_check_ts` | `float` | `time.time()` of the last call that passed the 60-second rate-limit guard in `_maybe_trigger_scan`. |

### Cached Data Functions

| Function | TTL | Returns |
|---|---|---|
| `cached_news()` | `NEWS_CACHE_TTL` (300 s) | Deduplicated article list from all 12 feeds |
| `cached_history(symbol)` | `PRICE_CACHE_TTL` (90 s) | OHLCV DataFrame for the given ticker |
| `cached_all_metrics()` | `PRICE_CACHE_TTL` (90 s) | Nested dict `{category: {asset_name: {metrics: ..., momentum: ...}}}` |

### Per-Rerun Variables (main panel)

| Variable | Type | Description |
|---|---|---|
| `selected_category` | `str` | Category chosen in sidebar selectbox |
| `selected_asset` | `str` | Asset chosen in sidebar selectbox |
| `ticker` | `str` | Yahoo Finance ticker for `selected_asset` |
| `history` | `pd.DataFrame` | Price history for `selected_asset` |
| `articles` | `list[dict]` | Full deduplicated news pool |
| `metrics` | `dict` | Price metrics for `selected_asset` |
| `momentum` | `dict` | Momentum metrics for `selected_asset` |
| `news` | `list[dict]` | News correlated with `selected_asset` |
| `clusters` | `dict` | Clustered news output |
| `disp_clust` | `dict` | Top 2 display clusters for UI rendering |
| `market_ctx` | `Optional[dict]` | Market context (only when sidebar checkbox enabled) |
| `signal` | `dict` | Signal score and label |
| `explanation` | `dict` | Full explanation with factors and confidence |
| `sig_score` | `float` | `signal["score"]` extracted for rendering |
| `sig_label` | `str` | `signal["label"]` extracted for rendering |
| `conf` | `str` | `explanation["confidence"]` extracted for rendering |
| `factors` | `list[dict]` | `explanation["factors"]` extracted for rendering |
| `primary_driver` | `Optional[dict]` | First factor from event or context factors list |

---

## storage.py — Internal Variables and Return Structures

### Module-Level

| Name | Type | Description |
|---|---|---|
| `_storage_path` | `pathlib.Path` | Resolved path to `STORAGE_DIR`. |
| `_REDUCED_FIELDS` | `set[str]` | Set of field names retained in reduced-detail snapshots. |
| `log` | `logging.Logger` | Module logger. |

### Snapshot Dict Structure (full detail)

| Key | Type | Description |
|---|---|---|
| `asset` | `str` | Asset name |
| `date` | `str` | ISO date string `YYYY-MM-DD` |
| `price` | `Optional[float]` | Latest close price |
| `change_1d` | `Optional[float]` | 1-day percentage change |
| `change_7d` | `Optional[float]` | 7-day percentage change |
| `change_30d` | `Optional[float]` | 30-day percentage change |
| `volatility` | `Optional[float]` | Daily return std deviation * 100 |
| `trend` | `Optional[str]` | Trend classification string |
| `rsi` | `Optional[float]` | 14-period RSI |
| `roc_10d` | `Optional[float]` | 10-day rate of change |
| `trend_strength` | `Optional[float]` | MA divergence percentage |
| `momentum_accel` | `Optional[float]` | ROC acceleration |
| `signal_score` | `Optional[float]` | Composite signal score |
| `signal_label` | `Optional[str]` | Signal label string |
| `headlines` | `list[dict]` | Top 5 headlines each with `title`, `source`, `sentiment` (float) |

### Reduced-Detail Fields (`_REDUCED_FIELDS`)

`asset`, `date`, `price`, `change_1d`, `signal_score`, `signal_label`, `trend`, `rsi`, `roc_10d`, `trend_strength`

### `get_historical_features(asset_name)` Return Structure

| Key | Type | Description |
|---|---|---|
| `available` | `int` | Number of snapshots found |
| `signal_consistency` | `Optional[float]` | Fraction of historical signals in same direction as latest |
| `trend_persistence` | `int` | Consecutive days the current trend has held |
| `today_vs_yesterday` | `dict` | Field-level comparison of latest vs previous snapshot |

---

## scan.py — Return Structures

### `run_scan()` Return Structure

| Key | Type | Description |
|---|---|---|
| `scan_date` | `str` | ISO date string of scan execution |
| `scan_time` | `str` | ISO datetime string of scan start |
| `total` | `int` | Total number of assets processed |
| `succeeded` | `int` | Number of assets that completed without error |
| `errors` | `list[dict]` | List of error dicts each with `asset`, `category`, `error` keys |
| `results` | `dict[str, dict[str, dict]]` | Nested `{category: {asset_name: entry_dict}}` |

### Entry Dict Within `results`

| Key | Type | Description |
|---|---|---|
| `ticker` | `str` | Yahoo Finance ticker |
| `signal_score` | `Optional[float]` | Composite score |
| `signal_label` | `Optional[str]` | Label string |
| `price` | `Optional[float]` | Latest close price |
| `change_1d` | `Optional[float]` | 1-day percentage change |
| `change_7d` | `Optional[float]` | 7-day percentage change |
| `trend` | `Optional[str]` | Trend classification |
| `rsi` | `Optional[float]` | 14-period RSI |
| `roc_10d` | `Optional[float]` | 10-day ROC |
| `confidence` | `Optional[str]` | Explanation confidence level |
| `verdict` | `str` | One-line summary string |

---

## backtest.py — Return Structures

### `evaluate_signal_accuracy(asset_name, lookback)` Return Structure

| Key | Type | Description |
|---|---|---|
| `hit_rate` | `Optional[float]` | Fraction of correct directional predictions. None if fewer than 2 pairs available |
| `num_evaluated` | `int` | Number of signal-outcome pairs evaluated |
| `details` | `list[dict]` | Per-pair records sorted newest-first |
| `avg_signal_score` | `Optional[float]` | Mean absolute signal score across evaluated pairs |
| `by_signal_strength` | `dict` | Hit rate and count broken down by `strong`, `moderate`, `weak` |
| `by_label` | `dict` | Hit rate and count per signal label |
| `label_summaries` | `list[str]` | Human-readable text summaries per label |

### `get_signal_streak(details)` Return Structure

| Key | Type | Description |
|---|---|---|
| `type` | `str` | `"win"`, `"loss"`, or `"none"` |
| `length` | `int` | Number of consecutive matching outcomes |
