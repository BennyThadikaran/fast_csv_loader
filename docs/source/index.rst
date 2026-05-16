.. csv_loader documentation master file, created by
   sphinx-quickstart on Mon Oct 14 10:54:56 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

fast_csv_loader
===============

**fast_csv_loader** is a fast and memory efficient way to load large CSV files (Timeseries data) into Pandas Dataframes. 

Python version: >= 3.8

GitHub Source: `BennyThadikaran/fast_csv_loader <https://github.com/BennyThadikaran/fast_csv_loader>`_

The ``csv_loader`` function efficiently loads a partial portion of a large CSV file containing time-series data into a pandas DataFrame.

The function allows:

- Loading the last N lines of the file.
- Loading the last N lines from a specific date.

It can load any type of time-series (both timezone aware and Naive). It handles both daily or intraday data.

**It is useful for loading large datasets that may not fit entirely into memory.**

**It also improves program execution time, when iterating or loading a large number of CSV files.**

cached_csv_loader (Added in v2.2.0)
-----------------------------------

`cached_csv_loader` is a performance optimization wrapper around `csv_loader` designed for workloads that repeatedly read the same CSV files.

Instead of re-reading and re-parsing a file from disk every time, it keeps an in-memory cache of recently loaded DataFrames. On subsequent calls with the same file and parameters, it returns the cached result instantly. The cache automatically invalidates when the underlying file changes (based on modification time), so it stays correct even if data is updated on disk.

This is useful in scenarios like trading scanners, dashboards, or backtests where the same set of CSV files is accessed repeatedly in loops or periodic refresh cycles. In those cases, disk I/O and CSV parsing become unnecessary overhead after the first load.

Thanks to `@sai2311-eng <https://github.com/sai2311-eng>`_ for his contribution.

============
Installation
============

To use ``fast_csv_loader``, first install it using pip:

.. code:: console

   pip install fast-csv-loader


.. toctree::

   Usage
   Algorithm

