# csv_loader.py

The `csv_loader` function efficiently loads a partial portion of a large CSV file containing time-series data into a pandas DataFrame.

The function allows:

- Loading the last N lines from the end of the file.
- Loading the last N lines from a specific date.

It can load any type of time-series (both timezone aware and Naive) and daily or intraday data.

It is useful for loading large datasets that may not fit entirely into memory.
It also improves program execution time, when iterating or loading a large number of CSV files.

**Supports Python >= 3.8**

## Install

`pip install csv_loader`

## Documentation

[https://bennythadikaran.github.io/csv_loader/](https://bennythadikaran.github.io/csv_loader/)

## Performance

Loading a portion of a large file is significantly faster than loading the entire file in memory.
Files used in the test were not particularly large. You may need to tweak the chunk_size parameter for your use case.

It is slower for smaller files or if you're loading nearly the entire portion of the file.

I chose a 6Kb chunk size based on testing with my specific requirements. Your requirements may differ.

### csv_loader vs pandas.read_csv

![Execution time - Last 160 lines](https://res.cloudinary.com/doyu4uovr/image/upload/s--oBlTOOhq--/f_auto/v1728895388/csv_loader/csv_loader_perf_14oct2024_bkjrgt.png)

![Execution time - Last 160 lines upto 1st Jan 2023](https://res.cloudinary.com/doyu4uovr/image/upload/s--H3sgcCoR--/f_auto/v1728895389/csv_loader/csv_loader_perf_dt_14oct2024_vojj0j.png)

To run this performance test.

```bash
py tests/run.py
```

At the minimum, the CSV file must contain a Date and another column with newline chars at the end to correctly parse and load.

```
Date,Price\n
2023-12-01,200\n
```

`run.py` measures the execution time of csv_loader vs. loading the entire file in Pandas DataFrame.

## Unit Test

`test_csv_loader.py` is the unit test file.

To run the test:

```bash
py src/tests/test_csv_loader.py
```
