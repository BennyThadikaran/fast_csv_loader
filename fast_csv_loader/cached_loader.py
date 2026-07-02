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
from typing import Optional
from collections.abc import Sequence

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
    use_columns: Optional[Sequence[str]] = None,
    chunk_size: int = 1024 * 6,
) -> pd.DataFrame:
    """
    .. versionadded:: 2.2.0

    Mtime-aware cached wrapper around ``csv_loader``.

    Provides a drop-in replacement for ``csv_loader`` for cases where the
    same CSV file may be read multiple times within the same process. Results
    are cached based on file path, modification time, and selected query
    parameters.

    The cache key is composed of (file_path, end_date, date_format,
    use_columns). The ``period`` parameter is NOT part of the cache key and
    is applied after cache retrieval, meaning different ``period`` values
    reuse the same cached DataFrame and only affect the returned slice.

    If the underlying file has changed (based on mtime), the cache entry is
    invalidated and the file is reloaded.

    :param file_path: The path to the CSV file to be loaded.
    :type file_path: pathlib.Path

    :param period: Number of rows/candles to return from the end of the
        dataset. Default is 160.
    :type period: int

    :param end_date: Load data up to this timestamp. If None, the most
        recent data is used. If provided, loading is anchored to this date.
    :type end_date: Optional[datetime]

    :param date_format: Custom datetime format string used for parsing the
        CSV date column if automatic parsing fails.
    :type date_format: Optional[str]

    :param use_columns: Default None. A sequence (e.g., list or tuple) of column names to load
        from the CSV file. If None, all columns are loaded.
    :type use_columns: Optional[Sequence[str]]

    :param chunk_size: Size of chunks (in bytes) used when reading the CSV
        file. Default is 6144 bytes (6 KB).
    :type chunk_size: int

    :return: A DataFrame containing the requested slice of timeseries data.
    :rtype: pd.DataFrame

    :raise FileNotFoundError: If ``file_path`` does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"No such file or directory: '{file_path}'")

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
            return (
                df.iloc[-period:].copy() if period and len(df) > period else df.copy()
            )

    # Cache miss — load with enough history that later calls with larger
    # `period` values can still be served from cache. We load a generous
    # buffer by passing period * 4 (min 1000) to the underlying loader.
    load_period = max(period * 4, 1000) if period else 10_000
    with _cache_lock:
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

    return df.iloc[-period:].copy() if period and len(df) > period else df.copy()


def invalidate(file_path) -> int:
    """
    .. versionadded:: 2.2.0

    Drop all cache entries for a given file (any ``end_date`` / columns combination).

    Useful after writing new data to disk when you want to ensure subsequent
    reads do not return stale cached results. Otherwise, cache entries are
    invalidated automatically based on file modification time.

    :param file_path: Path of the file whose cache entries should be removed.
    :type file_path: pathlib.Path | str

    :return: Number of cache entries removed for the given file.
    :rtype: int
    """
    target = str(Path(file_path).resolve())
    with _cache_lock:
        keys = [k for k in _cache if k[0] == target]
        for k in keys:
            _cache.pop(k, None)
        return len(keys)


def invalidate_all() -> int:
    """
    .. versionadded:: 2.2.0

    Drop all entries from the cache.

    Useful for resetting cache state entirely, for example during testing or
    after bulk data updates.

    :return: Number of cache entries removed.
    :rtype: int
    """
    with _cache_lock:
        n = len(_cache)
        _cache.clear()
        return n


def cache_stats() -> dict:
    """
    .. versionadded:: 2.2.0

    Return cache observability metrics including hit/miss counts, current
    cache size, and hit rate.

    :return: Dictionary containing cache statistics:

        - ``hits``: Number of cache hits
        - ``misses``: Number of cache misses
        - ``evictions``: Number of evicted entries
        - ``size``: Current number of cached entries
        - ``hit_rate``: Cache hit rate as a percentage (rounded to 1 decimal)
        - ``max_size``: Maximum allowed cache size

    :rtype: dict
    """
    with _cache_lock:
        total = _stats["hits"] + _stats["misses"]
        hit_rate = (_stats["hits"] / total * 100) if total else 0.0
        return {
            "hits": _stats["hits"],
            "misses": _stats["misses"],
            "evictions": _stats["evictions"],
            "size": len(_cache),
            "hit_rate": round(hit_rate, 1),
            "max_size": _MAX_CACHE_ENTRIES,
        }


def set_max_cache_size(n: int) -> None:
    """
    .. versionadded:: 2.2.0

    Set the maximum number of cached entries allowed.

    If the cache exceeds this size, older entries will be evicted
    automatically.

    :param n: New maximum cache size. Must be greater than 0.
    :type n: int

    :raise ValueError: If ``n`` is less than or equal to 0.
    """
    global _MAX_CACHE_ENTRIES
    if n <= 0:
        raise ValueError("max cache size must be > 0")
    _MAX_CACHE_ENTRIES = int(n)
    with _cache_lock:
        _evict_if_full()
