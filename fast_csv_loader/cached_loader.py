"""
cached_loader — mtime-aware in-memory caching wrapper around csv_loader.

When the same CSV file is read repeatedly (e.g. in a scanner loop, a
rolling backtest, or a dashboard re-render), re-parsing from disk every
time is wasteful. This module caches the parsed DataFrame and invalidates
it automatically when the file's modification time changes.

Typical use case: a trading scanner loops 50–200 stock CSVs every
few minutes, the files only change once a day after EOD sync. Without
caching, every loop re-parses every file.

Benchmark on 133 small daily CSVs (~12 KB each), 5 repeat passes:
    csv_loader (no cache):         ~555 ms
    cached_csv_loader (warm):       ~13 ms    (~43x faster)

Usage:
    from fast_csv_loader import cached_csv_loader

    df = cached_csv_loader(Path("AAPL.csv"), period=200)   # first call: disk
    df = cached_csv_loader(Path("AAPL.csv"), period=200)   # second call: cached

    # After writing new data to the file, cache auto-invalidates on next read
    # because the file mtime changed. For explicit invalidation:
    from fast_csv_loader import invalidate, invalidate_all, cache_stats
    invalidate("AAPL.csv")
    invalidate_all()
    stats = cache_stats()
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

from fast_csv_loader.csv_loader import csv_loader

# Internal cache: absolute_path_str -> (mtime, dataframe)
_cache: dict = {}
_cache_lock = threading.Lock()
_stats = {"hits": 0, "misses": 0, "evictions": 0}

# Cap cache size to avoid unbounded memory growth in long-running processes.
# Entries evicted in insertion order (rough LRU — cheaper than a true LRU).
_MAX_CACHE_ENTRIES = 500


def _evict_if_full() -> None:
    if len(_cache) > _MAX_CACHE_ENTRIES:
        drop_count = max(1, _MAX_CACHE_ENTRIES // 5)
        for k in list(_cache.keys())[:drop_count]:
            _cache.pop(k, None)
            _stats["evictions"] += 1


def cached_csv_loader(
    file_path: Path,
    period: int = 160,
    end_date: Optional[datetime] = None,
    date_format: Optional[str] = None,
    use_columns: Optional[List[str]] = None,
    chunk_size: int = 1024 * 6,
) -> pd.DataFrame:
    """
    Mtime-aware cached wrapper around csv_loader.

    Signature is identical to csv_loader — drop-in replacement wherever
    the same file may be read multiple times in the same process.

    Cache keys include (file_path, end_date, use_columns) so different
    argument shapes are stored separately. The period is applied AFTER
    the cache lookup (different ``period`` values share the same cached
    frame and just take a different tail slice).

    Returns an empty DataFrame if the file cannot be loaded.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return pd.DataFrame()

    try:
        mtime = file_path.stat().st_mtime
    except OSError:
        return pd.DataFrame()

    use_columns_key = tuple(use_columns) if use_columns else None
    cache_key = (str(file_path.resolve()), end_date, date_format, use_columns_key)

    with _cache_lock:
        entry = _cache.get(cache_key)
        if entry and entry[0] == mtime:
            _stats["hits"] += 1
            df = entry[1]
            return df.iloc[-period:] if period and len(df) > period else df.copy()

    # Cache miss — load with enough history that later calls with larger
    # `period` values can still be served from cache. We load a generous
    # buffer by passing period * 4 (min 1000) to the underlying loader.
    load_period = max(period * 4, 1000) if period else 10_000
    _stats["misses"] += 1
    df = csv_loader(
        file_path,
        period=load_period,
        end_date=end_date,
        date_format=date_format,
        use_columns=use_columns,
        chunk_size=chunk_size,
    )

    with _cache_lock:
        _cache[cache_key] = (mtime, df)
        _evict_if_full()

    return df.iloc[-period:] if period and len(df) > period else df.copy()


def invalidate(file_path) -> int:
    """
    Drop all cache entries for a given file (any end_date/columns combo).
    Returns the number of entries removed.

    Useful to call after writing new data to a file if you don't want to
    wait for the automatic mtime-based invalidation on the next read.
    """
    target = str(Path(file_path).resolve())
    with _cache_lock:
        keys = [k for k in _cache if k[0] == target]
        for k in keys:
            _cache.pop(k, None)
        return len(keys)


def invalidate_all() -> int:
    """Drop every entry in the cache. Returns the number of entries removed."""
    with _cache_lock:
        n = len(_cache)
        _cache.clear()
        return n


def cache_stats() -> dict:
    """Observability — return hit/miss counters, size, and hit rate."""
    with _cache_lock:
        total = _stats["hits"] + _stats["misses"]
        hit_rate = (_stats["hits"] / total * 100) if total else 0.0
        return {
            "hits":       _stats["hits"],
            "misses":     _stats["misses"],
            "evictions":  _stats["evictions"],
            "size":       len(_cache),
            "hit_rate":   round(hit_rate, 1),
            "max_size":   _MAX_CACHE_ENTRIES,
        }


def set_max_cache_size(n: int) -> None:
    """Adjust the max number of cached entries. Must be > 0."""
    global _MAX_CACHE_ENTRIES
    if n <= 0:
        raise ValueError("max cache size must be > 0")
    _MAX_CACHE_ENTRIES = int(n)
    with _cache_lock:
        _evict_if_full()
