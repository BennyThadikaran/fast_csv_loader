Usage
=====

Example
-------

.. code-block:: python

  from datetime import datetime
  from pathlib import Path

  import pandas as pd

  from csv_loader import csv_loader

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

API
---

.. autofunction:: csv_loader.csv_loader
