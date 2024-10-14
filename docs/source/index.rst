.. csv_loader documentation master file, created by
   sphinx-quickstart on Mon Oct 14 10:54:56 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

fast_csv_loader
===============

**fast_csv_loader** is a fast and memory efficient way to load large CSV files (Timeseries data) into Pandas Dataframes. 

Python version: >= 3.8

GitHub Source: `BennyThadikaran/csv_loader <https://github.com/BennyThadikaran/csv_loader>`_

The ``csv_loader`` function efficiently loads a partial portion of a large CSV file containing time-series data into a pandas DataFrame.

The function allows:

- Loading the last N lines of the file.
- Loading the last N lines from a specific date.

It can load any type of time-series (both timezone aware and Naive). It handles both daily or intraday data.

**It is useful for loading large datasets that may not fit entirely into memory.**

**It also improves program execution time, when iterating or loading a large number of CSV files.**

============
Installation
============

To use ``fast_csv_loader``, first install it using pip:

.. code:: console

   pip install fast_csv_loader


.. toctree::

   Usage
   Algorithm

