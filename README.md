# csv_loader.py
The `csv_loader` function efficiently loads a partial portion of a large CSV file containing time-series data into a pandas DataFrame. 

The function allows:

- Loading the last N lines from the end of the file.
- Loading the last N lines from a specific date.

It can load any type of time-series (both timezone aware and Naive) and daily or intraday data.

## Update `csv_loader_v2` - 17th May 2024

`csv_loader_v2` is the latest update and recommended to use. 

- It is faster than the previous version and more robust. See [performance below](#performance).
- If a file is less than 19kb or less than chunk size it is fully loaded into memory and returned. This is faster for smaller files.
- Algorithm has been simplified to run faster.
- Unit tests has been rewritten to cover a wide variety of scenarios.

`csv_loader_v1` is the original version and works well for daily data, but had issues loading intraday data due to its underlying algorithm. 

There will be no further development or bugfix on `csv_loader_v1`. I have left it here for comparison and will eventually be removed.


## Performance
Loading a portion of a large file is significantly faster than loading the entire file in memory. Files used in the test were not particularly large. You may need to tweak the chunk_size parameter for your use case.

It is slower for smaller files or if you're loading nearly the entire portion of the file.

### csv_loader_v2 vs csv_loader_v1 vs pandas.read_csv

![Execution time - Last 160 lines](https://res.cloudinary.com/doyu4uovr/image/upload/s--LVsbrjb0--/f_auto/v1715940195/csv_loader/csv_loader_perf_16may2024_sgbwj2.png)

![Execution time - Last 160 lines upto 1st Jan 2023](https://res.cloudinary.com/doyu4uovr/image/upload/s--rzG7kb1P--/f_auto/v1715940195/csv_loader/csv_loader_perf_dt_16may2024_n1cnqy.png)

## Basic Algorithm - csv_loader_v2

Here is the broad algorithm without getting too detailed. The function is well documented and commented on for understanding.

Assume you wish to load 160 lines from the end of the file. Dates can be any format passed to pandas.to_datetime.

1. Read the first line to get the column header.
2. Seek to the end of the file.
3. Read the last N bytes (Chunk) of the file.
4. On the first chunk, get a count of line breaks (`\n`) in the chunk to estimate lines per chunk. 
5. On every chunk,
    - Update the number of lines read by adding the lines per chunk.
    - Store the chunks in a list
6. Once we have the desired number of lines, 
    - Combine the column header and final chunk, append it to the list
    - Reverse the list and join the list into a string.
7. Load it into a Pandas DataFrame and return the slice of data required.

If end_date argument is specified, we parse the first date string in the chunk and check if we're past the end_date. If yes, we continue from Step 5, until desired number of lines have been loaded.

At the minimum, the CSV file must contain a Date and another column with newline chars at the end to correctly parse and load.

```
Date,Price\n
2023-12-01,200\n
```

```python
def csv_loader_v2(
    file_path: Path,
    period: int = 160,
    end_date: Optional[datetime] = None,
    date_column_name: str = "Date",
    chunk_size: int = 1024 * 6,
) -> pd.DataFrame
```

Parameters:

- file_path (Path): The path to the CSV file to be loaded.
- period (int): Number of lines/candles to return. The default is 160.
- end_date (Optional[datetime]): Load N lines up to this date.
    - If None, will load the last N lines from file
    - If the date is provided, load the last N lines from this date
- date_column_name (str): Name of the date column. Defaults to `Date`
- chunk_size (int): The size of data chunks loaded into memory.
    The default is 6144 bytes (6 KB).
        
I chose a 6Kb chunk size based on testing with my specific requirements.

`csv_loader_v2.py` is the main file containing the function.

`run.py` measures the execution time of csv_loader_v2 vs. loading the entire file in Pandas DataFrame.

## Unit Test

`test_csv_loader.py` is the unit test file.

To run the test:

```bash
py -m unittest discover src/
```

You are free to use and improve the function as you see fit for your requirements.
