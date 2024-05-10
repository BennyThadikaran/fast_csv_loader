# csv_loader.py
The `csv_loader` function efficiently loads a partial portion of a large CSV file containing time-series data into a pandas DataFrame. 

I needed to load data from the end of the file.

The function allows:

- Loading the last N lines from the end of the file.
- Loading the last N lines from a specific date.

It has options to handle 24/7 markets such as Crypto and accounts for public holidays and weekends.

While I tested OHLC data, it can be any time-series data as long as datetime is the first column.

## Performance
Loading a portion of a large file is significantly faster than loading the entire file in memory. Files used in the test were not particularly large. You may need to tweak some parameters for your use case.

It is slower for smaller files or if you're loading nearly the entire portion of the file.

![Execution time](https://res.cloudinary.com/doyu4uovr/image/upload/s--PEPCHkQy--/v1710187024/csv_loader/csv_loader_perf_z15mly.png)

## Basic Algorithm

Here is the broad algorithm without getting too detailed. The function is well documented and commented on for understanding.

Assume you wish to load 160 lines from the end of the file. Dates can be any format passed to pandas.to_datetime.

1. Read the first line to get the column header.
2. Seek to the end of the file.
3. Read the last N bytes (Chunk) of the file.
4. On the first chunk, parse the last date and use it to calculate the start date (Last date - 160 days). 
5. On every chunk,
    - parse the first available date and check if we're past the start date.
    - Store the chunks in a list
6. Once we're past the start date, 
    - Combine the column header and final chunk, append it to the list
    - Reverse the list and join the list into a string.
7. Load it into a Pandas DataFrame and return the slice of data required.

At the minimum, the CSV file must contain a Date and another column with newline chars at the end to correctly parse and load.

```
Date,Price\n
2023-12-01,200\n
```

```python
def csv_loader(
    file_path: Path,
    period=160,
    end_date: Optional[datetime] = None,
    is_24_7=False,
    chunk_size=1024 * 6,
) -> pd.DataFrame
```

Parameters:

- `file_path (Path)`: The path to the CSV file to be loaded.
- `period (int)`: Number of lines/candles to return. The default is 160.
- `end_date (Optional[datetime])`: Load N lines up to this date.
    - If None, will load the last N lines
    - If the date provided, load the last N lines till this date
- `is_24_7 (bool)`: Indicates whether the data represents a 24/7 market. If False, weekends (Sat/Sun) are not included.
- `chunk_size (int)`: The size of data chunks loaded into memory. The default is 6144 bytes (6 KB).
        
I chose a 6Kb chunk size based on testing with my specific requirements.

`csv_loader.py` is the main file containing the function.

`run.py` measures the execution time of csv_loader vs. loading the entire file in Pandas DataFrame.

## Unit Test

`test_csv_loader.py` is the unit test file. I have tested with both intraday and daily OHLC data.

To run the test:

```bash
py -m unittest discover src/
```

You are free to use and improve the function as you see fit for your requirements.
