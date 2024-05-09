# csv_loader.py
This is a demo function to demonstrate, loading a partial portion of a large CSV file into a pandas DataFrame.

The csv_loader function is specifically written for loading timeseries data. 
Specifically i needed to load the last `N` lines of a file. 

## Performance
Larger files are significantly faster to load as compared to loading the entire file in memory. Test files are not particulary large, you may need to tweak the default settings for your needs.

![Execution time](https://res.cloudinary.com/doyu4uovr/image/upload/s--PEPCHkQy--/v1710187024/csv_loader/csv_loader_perf_z15mly.png)

## Basic Algorithm

Here is the broad algorithm without getting too detailed. The function is well documented and commented for understanding.

Assume you wish to load 160 lines from the end of the file. Dates are assumed to be in ISO-format.

1. Read the first line to get the column header.
2. Seek to the end of the file.
3. Read the last N bytes (Chunk) of the file from the end.
4. On the first chunk, parse the last date in the chunk, and use it to calculate the starting date (Last date - 160 days)
5. On every chunk,
    - parse the first available date and check if we're past the starting date.
    - Store the chunks into a list
6. Once we're past the starting date, 
    - Combine the column header and final chunk, append it to the list
    - Reverse the list and join the list into a string.
7. Load it into a Pandas DataFrame and return the exact slice of data required.

The function allows:

    - Loading the last N lines from the end of file
    - Loading the last N lines from a specific date.

At the minimum, the CSV file is expected to contain a Date column with newline chars at the end to correctly parse and load.

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
- `period (int)`: Number of klines/candles to return. Default is 160.
- `end_date (Optional[datetime])`: end date until which data should be loaded.
    - If None, will load the last N `periods`.
    - If date is provided, will load the last N `periods` upto `end_date`
- `is_24_7 (bool)`: Indicates whether the data represents a 24/7 market. If False, weekends (Sat/Sun) is not counted in periods.
- `chunk_size (int)`: The size of data chunks to be loaded into memory at once, in bytes. Default is 6144 bytes (6 KB).
        
I chose 6Kb chunk size based on testing with my specific requirements.

`csv_loader.py` is the main file containing the function.

`run.py` measures the execution time of csv_loader vs loading the entire file in Pandas DataFrame and returning a slice of the data.

## Unit Test

`test_csv_loader.py` is the unittest file. I have tested with both intraday and daily data

To run the test:

```bash
py -m unittest discover src/
```

You are free to use and improve the function as you see fit for your requirements.
