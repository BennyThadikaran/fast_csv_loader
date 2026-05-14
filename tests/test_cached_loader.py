import os
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from context import csv_loader  # noqa: F401  (makes package importable)
from fast_csv_loader import (
    cache_stats,
    cached_csv_loader,
    invalidate,
    invalidate_all,
    set_max_cache_size,
)


def _make_csv(path: Path, rows: int = 300) -> None:
    dates = pd.date_range("2020-01-01", periods=rows, freq="D")
    df = pd.DataFrame(
        {
            "Date": dates,
            "Open":  np.random.uniform(100, 200, rows),
            "High":  np.random.uniform(100, 200, rows),
            "Low":   np.random.uniform(100, 200, rows),
            "Close": np.random.uniform(100, 200, rows),
        }
    )
    df.to_csv(path, index=False)


class TestCachedLoader(unittest.TestCase):
    def setUp(self):
        invalidate_all()
        self._baseline = cache_stats()
        self.tmpdir = Path(tempfile.mkdtemp(prefix="fcl_test_"))
        self.csv_a = self.tmpdir / "A.csv"
        self.csv_b = self.tmpdir / "B.csv"
        _make_csv(self.csv_a)
        _make_csv(self.csv_b)

    def _delta(self, key: str) -> int:
        return cache_stats()[key] - self._baseline[key]

    def tearDown(self):
        invalidate_all()
        for p in self.tmpdir.iterdir():
            p.unlink()
        self.tmpdir.rmdir()

    def test_returns_same_data_as_csv_loader(self):
        direct = csv_loader(self.csv_a, period=50)
        cached = cached_csv_loader(self.csv_a, period=50)
        pd.testing.assert_frame_equal(direct, cached)

    def test_cache_hit_on_repeat_read(self):
        cached_csv_loader(self.csv_a, period=50)
        cached_csv_loader(self.csv_a, period=50)
        cached_csv_loader(self.csv_a, period=50)
        self.assertGreaterEqual(self._delta("hits"), 2)
        self.assertEqual(self._delta("misses"), 1)

    def test_cache_miss_on_different_file(self):
        cached_csv_loader(self.csv_a, period=50)
        cached_csv_loader(self.csv_b, period=50)
        self.assertEqual(self._delta("misses"), 2)

    def test_mtime_invalidation(self):
        cached_csv_loader(self.csv_a, period=50)
        self.assertEqual(self._delta("misses"), 1)

        # Rewrite the file with new data — mtime should change
        time.sleep(1.1)  # ensure mtime tick on all filesystems
        _make_csv(self.csv_a, rows=400)

        cached_csv_loader(self.csv_a, period=50)
        # New file → new miss (mtime changed)
        self.assertEqual(self._delta("misses"), 2)

    def test_manual_invalidate(self):
        cached_csv_loader(self.csv_a, period=50)
        removed = invalidate(self.csv_a)
        self.assertEqual(removed, 1)
        cached_csv_loader(self.csv_a, period=50)
        self.assertEqual(self._delta("misses"), 2)

    def test_invalidate_all(self):
        cached_csv_loader(self.csv_a, period=50)
        cached_csv_loader(self.csv_b, period=50)
        removed = invalidate_all()
        self.assertEqual(removed, 2)
        self.assertEqual(cache_stats()["size"], 0)

    def test_different_period_shares_cache(self):
        """Two calls with different `period` should hit the same cache entry."""
        cached_csv_loader(self.csv_a, period=50)
        cached_csv_loader(self.csv_a, period=100)
        # Same file, same other args → 1 miss, 1 hit
        self.assertEqual(self._delta("misses"), 1)
        self.assertEqual(self._delta("hits"), 1)

    def test_different_period_returns_correct_size(self):
        df50  = cached_csv_loader(self.csv_a, period=50)
        df100 = cached_csv_loader(self.csv_a, period=100)
        self.assertEqual(len(df50), 50)
        self.assertEqual(len(df100), 100)

    def test_missing_file_raises_filenotfounderror(self):
        with self.assertRaises(FileNotFoundError):
            cached_csv_loader(self.tmpdir / "does_not_exist.csv")

    def test_eviction(self):
        """With a max of 2, the 3rd distinct file should evict older entries."""
        set_max_cache_size(2)
        try:
            c1 = self.tmpdir / "c1.csv"
            c2 = self.tmpdir / "c2.csv"
            c3 = self.tmpdir / "c3.csv"
            for p in (c1, c2, c3):
                _make_csv(p)
            cached_csv_loader(c1, period=50)
            cached_csv_loader(c2, period=50)
            cached_csv_loader(c3, period=50)
            self.assertLessEqual(cache_stats()["size"], 2)
            self.assertGreaterEqual(self._delta("evictions"), 1)
        finally:
            set_max_cache_size(500)


if __name__ == "__main__":
    unittest.main()
