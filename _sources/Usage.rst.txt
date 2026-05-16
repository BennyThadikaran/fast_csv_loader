Usage
=====

Example using csv_loader
------------------------

.. code-block:: python

  from datetime import datetime
  from pathlib import Path

  import pandas as pd

  from fast_csv_loader import csv_loader

  file = Path("path/to/your/timeseries_data.csv")

  # Load 160 lines of data from end of file
  df = csv_loader(file_path=file)

  print(df)

.. code-block:: python

  # Load last 500 lines of data upto 10th May 2024
  df = csv_loader(
      file_path=file,
      period=500,
      end_date=datetime(2024, 5, 10),
  )

  # If `Date` is not default datetime column, specify it using `date_column`
  df = csv_loader(file_path=file, date_column="time")

  # If pandas is unable to parse the date column, specify the format using `date_format`
  df = csv_loader(file_path=file, date_format="%d/%m/%Y")

  # Increase the `chunk_size` to optimize performance based of your specific needs.
  df = csv_loader(file_path=file, chunk_size=1024 * 10)

Example using cached_csv_loader
-------------------------------

.. note::
   `cached_csv_loader` was introduced in version 2.2.0

.. code-block:: python

  from fast_csv_loader import (
      cached_csv_loader,
      invalidate, invalidate_all,
      cache_stats, set_max_cache_size,
  )

  df = cached_csv_loader(Path("AAPL.csv"), period=200)   # disk read
  df = cached_csv_loader(Path("AAPL.csv"), period=200)   # cache hit

  # Auto-invalidates when file mtime changes (e.g. after EOD sync overwrites)
  # For explicit invalidation:
  invalidate("AAPL.csv")
  invalidate_all()

  # Observability:
  cache_stats()
  # {'hits': 49, 'misses': 1, 'evictions': 0, 'size': 1, 'hit_rate': 98.0, 'max_size': 500}


API
---

.. autofunction:: fast_csv_loader.csv_loader

.. autofunction:: fast_csv_loader.cached_csv_loader

.. autofunction:: fast_csv_loader.invalidate

.. autofunction:: fast_csv_loader.invalidate_all

.. autofunction:: fast_csv_loader.cache_stats

.. autofunction:: fast_csv_loader.set_max_cache_size

